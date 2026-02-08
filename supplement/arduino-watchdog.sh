#!/bin/bash
# Arduino Mega + Node-RED Watchdog v3
#
# Checks every 60s:
#   1. /dev/ttyACM0 exists (USB device present)
#   2. Node-RED process is running
#   3. Node-RED has the serial port open
#   4. Firmata is genuinely connected (last log line is "Connected", not timeout)
#
# ioplugin log sequence:
#   "Available Firmata"  -> board detected on serial
#   "Connected Firmata"  -> connection established (~5s later)
#   "timeout occurred"   -> 20s later: if this is the LAST line, connection FAILED
#                           (GPIO nodes stuck with yellow "waiting" status)
#   If "Connected Firmata" is the last line -> genuinely healthy
#
# Recovery escalation:
#   Level 1: Restart Node-RED (twice)
#   Level 2: USB reset + restart Node-RED (twice more)
#   Level 3: Full system reboot
#
# Restart tracking is time-based: if too many restarts in a window, escalate.

DEVICE="/dev/ttyACM0"
LOGFILE="/var/log/arduino-watchdog.log"
CHECK_INTERVAL=60
USB_DEVICE_PATH="/sys/bus/usb/devices/1-1.1"

# After NR starts, wait this long for "Connected Firmata" before declaring failure
FIRMATA_CONNECT_GRACE=120

# Escalation thresholds (restarts within RESTART_WINDOW seconds)
RESTART_WINDOW=1800  # 30 minutes
NR_RESTART_THRESHOLD=2   # after 2 NR restarts, try USB reset
USB_RESTART_THRESHOLD=4  # after 2 more (4 total), reboot

# File to track restart timestamps (survives watchdog restarts, not reboots)
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

# Get how many seconds NR has been running
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

# Check if Firmata genuinely connected and stayed connected.
# Looks at the LAST firmata-related log line in this NR session:
#   "Connected Firmata"       -> healthy (no timeout followed)
#   "timeout" or "Error"      -> failed (GPIO nodes dead/waiting)
#   "Available Firmata" only  -> still connecting (grace period)
#   nothing                   -> no firmata activity (grace period or stuck)
check_firmata_healthy() {
    local nr_pid
    nr_pid=$(systemctl show nodered -p MainPID --value 2>/dev/null)
    if [ -z "$nr_pid" ] || [ "$nr_pid" = "0" ]; then
        return 1
    fi

    local nr_start
    nr_start=$(systemctl show nodered -p ActiveEnterTimestamp --value 2>/dev/null)
    if [ -z "$nr_start" ]; then
        return 0  # can't determine, assume OK
    fi

    # Convert NR start timestamp to ISO format for journalctl --since
    local nr_start_iso
    nr_start_iso=$(date -d "$nr_start" '+%Y-%m-%d %H:%M:%S' 2>/dev/null)
    if [ -z "$nr_start_iso" ]; then
        return 0  # can't parse timestamp, assume OK
    fi

    # Get the LAST firmata-related log line from this NR session
    local last_firmata_line
    last_firmata_line=$(journalctl -u nodered --no-pager --since "$nr_start_iso" 2>/dev/null \
        | grep -E "Connected Firmata|Available Firmata|timeout.*Board|Device or Firmware Error" \
        | tail -1)

    if [ -z "$last_firmata_line" ]; then
        # No firmata log lines yet
        local uptime
        uptime=$(get_nr_uptime)
        if [ "$uptime" -lt "$FIRMATA_CONNECT_GRACE" ]; then
            return 0  # Still booting
        fi
        return 1  # Running too long with no firmata activity
    fi

    # Last line is "Connected Firmata" -> genuinely healthy
    if echo "$last_firmata_line" | grep -q "Connected Firmata"; then
        return 0
    fi

    # Last line is timeout/error -> connection failed, GPIO nodes dead
    if echo "$last_firmata_line" | grep -qE "timeout|Error"; then
        return 1
    fi

    # Only "Available Firmata" (detected but not yet connected)
    local uptime
    uptime=$(get_nr_uptime)
    if [ "$uptime" -lt "$FIRMATA_CONNECT_GRACE" ]; then
        return 0  # Still connecting
    fi
    return 1  # Stuck in "Available" too long
}

# Count how many restarts happened within RESTART_WINDOW
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
    # Prune entries older than window
    if [ -f "$RESTART_TIMESTAMPS" ]; then
        local cutoff tmpfile
        cutoff=$(( $(date +%s) - RESTART_WINDOW ))
        tmpfile="${RESTART_TIMESTAMPS}.tmp"
        awk -v c="$cutoff" '$1 >= c' "$RESTART_TIMESTAMPS" > "$tmpfile" 2>/dev/null
        mv "$tmpfile" "$RESTART_TIMESTAMPS" 2>/dev/null
    fi
}

reset_usb() {
    log "ACTION" "Resetting USB for Arduino at $USB_DEVICE_PATH"
    if [ -f "$USB_DEVICE_PATH/authorized" ]; then
        echo 0 > "$USB_DEVICE_PATH/authorized" 2>/dev/null
        sleep 3
        echo 1 > "$USB_DEVICE_PATH/authorized" 2>/dev/null
        sleep 8  # wait for USB re-enumeration and ttyACM0 to reappear
    else
        log "WARN" "USB sysfs path not found, trying usbreset"
        usbreset "2341:0042" 2>/dev/null
        sleep 5
    fi
}

restart_nodered() {
    log "ACTION" "Restarting Node-RED service"
    systemctl restart nodered
    record_restart
    sleep 45  # wait for NR to fully start and Firmata to connect
}

reboot_system() {
    log "ACTION" "All recovery failed. Rebooting system."
    sync
    reboot
}

# Decide recovery action based on recent restart count
recover() {
    local reason="$1"
    local recent
    recent=$(count_recent_restarts)

    if [ "$recent" -lt "$NR_RESTART_THRESHOLD" ]; then
        # Level 1: restart NR
        log "WARN" "$reason — restarting Node-RED (restarts in last 30m: $recent)"
        restart_nodered
    elif [ "$recent" -lt "$USB_RESTART_THRESHOLD" ]; then
        # Level 2: USB reset + restart NR
        log "WARN" "$reason — escalating to USB reset + NR restart (restarts in last 30m: $recent)"
        systemctl stop nodered
        sleep 5
        reset_usb
        sleep 3
        systemctl start nodered
        record_restart
        sleep 45
    else
        # Level 3: reboot
        log "ERROR" "$reason — $recent restarts in last 30m exhausted, rebooting"
        reboot_system
    fi
}

# --- Main loop ---

log "INFO" "Watchdog v3 started (device=$DEVICE, interval=${CHECK_INTERVAL}s, connect_grace=${FIRMATA_CONNECT_GRACE}s)"

# Wait for Node-RED to finish starting on boot
sleep 45

while true; do
    rotate_log

    # Step 1: Check USB device exists
    if ! check_device; then
        now=$(date +%s)
        if [ "$device_missing_since" -eq 0 ]; then
            device_missing_since=$now
            log "WARN" "Device $DEVICE missing — waiting for USB re-enumeration"
        fi
        elapsed=$(( now - device_missing_since ))

        if [ "$elapsed" -gt 120 ]; then
            recover "Device missing for ${elapsed}s"
        fi
        sleep "$CHECK_INTERVAL"
        continue
    fi

    # Device present — reset missing timer
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
            recover "Node-RED failed to start"
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
            recover "Node-RED running ${uptime}s but serial not connected"
        fi
        sleep "$CHECK_INTERVAL"
        continue
    fi

    # Step 4: Check Firmata genuinely connected (not timed out or stuck)
    if ! check_firmata_healthy; then
        # Log the last firmata line for debugging
        nr_start_dbg=$(systemctl show nodered -p ActiveEnterTimestamp --value 2>/dev/null)
        last_line_dbg=$(journalctl -u nodered --no-pager --since "$nr_start_dbg" 2>/dev/null \
            | grep -E "Connected Firmata|Available Firmata|timeout.*Board|Device or Firmware Error" \
            | tail -1)
        log "DEBUG" "Last firmata log: $last_line_dbg"
        recover "Firmata unhealthy after $(get_nr_uptime)s (GPIO nodes likely dead)"
        sleep "$CHECK_INTERVAL"
        continue
    fi

    sleep "$CHECK_INTERVAL"
done
