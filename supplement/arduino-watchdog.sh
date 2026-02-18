#!/bin/bash
# Arduino Mega + Node-RED Watchdog v7
#
# v7: Reboot-first for heartbeat failure.
#   - NR restarts don't fix serial stall — proven by repeated failures
#   - Heartbeat dead → reboot directly (skip futile NR restarts)
#   - NR restart still used for NR-down or serial-not-connected cases
#   - Diagnostic snapshot logged before reboot for root-cause analysis
#
# v6: Replaced Firmata with custom serial protocol.
# v5: Combined Firmata log + GPIO heartbeat (deploy-tolerant)
# v4.1: Added GPIO liveness via InfluxDB
# v4: Removed USB reset, faster escalation, reboot cooldown

DEVICE="/dev/ttyACM0"
LOGFILE="/var/log/arduino-watchdog.log"
CHECK_INTERVAL=60
USB_DEVICE_PATH="/sys/bus/usb/devices/1-1.1"

# Grace period before checking GPIO liveness (NR needs time to connect serial + receive heartbeats)
GPIO_LIVENESS_GRACE=300  # 5 minutes after NR start

# NR restart threshold — only used for non-heartbeat issues (NR down, serial not connected)
RESTART_WINDOW=1800
NR_RESTART_THRESHOLD=2

REBOOT_COOLDOWN=600

RESTART_TIMESTAMPS="/tmp/arduino-watchdog-restarts"

device_missing_since=0

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$1] $2" | tee -a "$LOGFILE"
}

rotate_log() {
    local size
    size=$(stat -c%s "$LOGFILE" 2>/dev/null || echo 0)
    if [ "$size" -gt 1048576 ]; then
        mv "$LOGFILE" "${LOGFILE}.old"
        log "INFO" "Log rotated"
    fi
}

check_device() {
    [ -e "$DEVICE" ]
}

check_nodered_running() {
    systemctl is-active --quiet nodered
}

check_nodered_has_serial() {
    lsof "$DEVICE" 2>/dev/null | grep -q node-red
}

get_nr_uptime() {
    local nr_start_ts now_ts nr_start_epoch
    nr_start_ts=$(systemctl show nodered -p ActiveEnterTimestamp --value 2>/dev/null)
    if [ -z "$nr_start_ts" ]; then
        echo 0
        return
    fi
    now_ts=$(date +%s)
    nr_start_epoch=$(date -d "$nr_start_ts" +%s 2>/dev/null || echo "$now_ts")
    echo $(( now_ts - nr_start_epoch ))
}

get_system_uptime() {
    awk '{print int($1)}' /proc/uptime
}

# Check GPIO liveness via InfluxDB arduino_status (heartbeat from serial parser)
# Returns 0 (healthy) if last arduino_status value is 1 within last 3 minutes
# Returns 1 (unhealthy) if last value is 0 or missing
check_gpio_alive() {
    local uptime
    uptime=$(get_nr_uptime)
    if [ "$uptime" -lt "$GPIO_LIVENESS_GRACE" ]; then
        return 0  # Too soon after start, give it time
    fi

    local result
    result=$(influx -database highland -execute \
        "SELECT last(value) FROM arduino_status WHERE time > now() - 3m" \
        2>/dev/null | tail -1)

    if [ -z "$result" ]; then
        log "WARN" "Could not query arduino_status from InfluxDB"
        return 0  # Can't determine, assume OK
    fi

    # Parse the last value (format: "timestamp   value")
    local status_val
    status_val=$(echo "$result" | awk '{print $NF}')

    if [ "$status_val" = "0" ]; then
        return 1  # GPIO dead
    fi

    return 0
}

count_recent_restarts() {
    local cutoff count
    cutoff=$(( $(date +%s) - RESTART_WINDOW ))
    count=0
    if [ -f "$RESTART_TIMESTAMPS" ]; then
        while IFS= read -r ts; do
            if [ "$ts" -ge "$cutoff" ] 2>/dev/null; then
                count=$((count + 1))
            fi
        done < "$RESTART_TIMESTAMPS"
    fi
    echo "$count"
}

record_restart() {
    echo "$(date +%s)" >> "$RESTART_TIMESTAMPS"
    if [ -f "$RESTART_TIMESTAMPS" ]; then
        local cutoff tmpfile
        cutoff=$(( $(date +%s) - RESTART_WINDOW ))
        tmpfile="${RESTART_TIMESTAMPS}.tmp"
        awk -v c="$cutoff" '$1 >= c' "$RESTART_TIMESTAMPS" > "$tmpfile" 2>/dev/null
        mv "$tmpfile" "$RESTART_TIMESTAMPS" 2>/dev/null
    fi
}

restart_nodered() {
    log "ACTION" "Restarting Node-RED service"
    systemctl restart nodered
    record_restart
    sleep 45
}

reboot_system() {
    local sys_uptime
    sys_uptime=$(get_system_uptime)
    if [ "$sys_uptime" -lt "$REBOOT_COOLDOWN" ]; then
        log "WARN" "System only up ${sys_uptime}s — skipping reboot (cooldown ${REBOOT_COOLDOWN}s). Will retry next cycle."
        return 1
    fi
    log "ACTION" "Rebooting system (uptime was ${sys_uptime}s)"
    sync
    reboot
}

# Log diagnostic snapshot before rebooting — helps find root cause
log_diagnostics() {
    log "DIAG" "--- Diagnostic snapshot before reboot ---"
    log "DIAG" "NR uptime: $(get_nr_uptime)s, System uptime: $(get_system_uptime)s"
    log "DIAG" "NR PID: $(pgrep -f 'node-red' | head -1)"
    log "DIAG" "Serial FDs: $(lsof $DEVICE 2>/dev/null | tail -n +2)"
    log "DIAG" "NR memory: $(ps -p $(pgrep -f 'node-red' | head -1) -o rss= 2>/dev/null) KB"
    log "DIAG" "Free memory: $(awk '/MemAvailable/{print $2}' /proc/meminfo) KB"
    log "DIAG" "Last 3 NR serial lines: $(journalctl -u nodered --no-pager -n 50 2>/dev/null | grep -i serial | tail -3)"
    log "DIAG" "Last dmesg USB: $(dmesg | grep -i 'ttyACM\|usb.*1-1.1\|cdc_acm' | tail -3)"
    log "DIAG" "--- End diagnostic snapshot ---"
}

# Recover from non-heartbeat issues (NR down, serial not connected)
# These CAN be fixed by NR restart, so use escalation
recover_nr() {
    local reason="$1"
    local recent
    recent=$(count_recent_restarts)

    if [ "$recent" -lt "$NR_RESTART_THRESHOLD" ]; then
        log "WARN" "$reason — restarting Node-RED (restarts in last 30m: $recent)"
        restart_nodered
    else
        log "ERROR" "$reason — $recent NR restarts failed, rebooting"
        log_diagnostics
        reboot_system
    fi
}

# Recover from heartbeat failure — reboot directly
# NR restarts don't fix serial stall, skip straight to reboot
recover_heartbeat() {
    local reason="$1"
    log "ERROR" "$reason — serial stall detected, rebooting directly"
    log_diagnostics
    reboot_system
}

# --- Main loop ---

log "INFO" "Watchdog v7 started (device=$DEVICE, interval=${CHECK_INTERVAL}s, gpio_grace=${GPIO_LIVENESS_GRACE}s)"

sleep 45

while true; do
    rotate_log

    # Step 1: Check USB device exists
    if ! check_device; then
        now=$(date +%s)
        if [ "$device_missing_since" -eq 0 ]; then
            device_missing_since=$now
            log "WARN" "Device $DEVICE missing — waiting for re-enumeration"
        fi
        elapsed=$(( now - device_missing_since ))

        if [ "$elapsed" -gt 120 ]; then
            log "ERROR" "Device missing for ${elapsed}s — rebooting (USB stack likely broken)"
            reboot_system
        fi
        sleep "$CHECK_INTERVAL"
        continue
    fi

    if [ "$device_missing_since" -ne 0 ]; then
        log "INFO" "Device $DEVICE reappeared"
        device_missing_since=0
    fi

    # Step 2: Check Node-RED is running
    if ! check_nodered_running; then
        log "WARN" "Node-RED is not running — starting it"
        systemctl start nodered
        record_restart
        sleep 45
        if ! check_nodered_running; then
            recover_nr "Node-RED failed to start"
        else
            log "INFO" "Node-RED started successfully"
        fi
        sleep "$CHECK_INTERVAL"
        continue
    fi

    # Step 3: Check Node-RED has the serial port open
    if ! check_nodered_has_serial; then
        uptime=$(get_nr_uptime)
        if [ "$uptime" -gt 60 ]; then
            recover_nr "Node-RED running ${uptime}s but serial not connected"
        fi
        sleep "$CHECK_INTERVAL"
        continue
    fi

    # Step 4: Check GPIO heartbeat — reboot directly if dead
    if ! check_gpio_alive; then
        log "ERROR" "GPIO heartbeat dead — Arduino serial stall (NR up $(get_nr_uptime)s)"
        recover_heartbeat "GPIO heartbeat dead after $(get_nr_uptime)s"
        sleep "$CHECK_INTERVAL"
        continue
    fi

    sleep "$CHECK_INTERVAL"
done
