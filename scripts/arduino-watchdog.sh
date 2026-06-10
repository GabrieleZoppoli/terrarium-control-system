#!/bin/bash
# Arduino Mega + Node-RED Watchdog v10
#
# v10: Fast serial prod — checks every 15s, USB-resets after 30s stale.
#   - Heartbeat stale > 30s + device present → sysfs USB reset (unbind/rebind driver)
#   - NR serial node auto-reconnects when device reappears (~15s)
#   - No NR restart for serial stalls, ever
#   - Cooldown: max 1 USB reset per 60s
#   - Device missing > 120s → reboot (USB stack broken)
#
# v9: Log-only for heartbeat, USB power-cycle only if device missing
# v7: Reboot-first for heartbeat failure

DEVICE="/dev/arduino"
LOGFILE="/var/log/arduino-watchdog.log"
CHECK_INTERVAL=15
USB_SYSFS_PATH="/sys/bus/usb/devices/1-1.2"

# How long heartbeat can be stale before we prod
HEARTBEAT_STALE_THRESHOLD=30

# Min seconds between USB resets
USB_RESET_COOLDOWN=60

# NR grace after start — don't check heartbeat until NR has had time to connect
NR_GRACE=120

# Device missing timeout — reboot if gone this long
DEVICE_MISSING_TIMEOUT=120

REBOOT_COOLDOWN=600

LAST_USB_RESET=0
LAST_HEARTBEAT_OK=0
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

# Read heartbeat timestamp directly from InfluxDB
# Returns seconds since last alive heartbeat, or 9999 if unknown
# Hardened 2026-05-18:
#   A4: if `influx` CLI binary is missing/broken, return 0 (assume alive) so we
#       do NOT enter an infinite USB-reset loop driven by an infrastructure
#       failure that has nothing to do with the Arduino.
#   B4: 30 s query window (was 5 min) — Arduino heartbeats every 2 s; a 30 s
#       window is populated when alive and empty when not. Removes the
#       "4m59-old `1` reported as alive" failure mode.
get_heartbeat_age() {
    if ! command -v influx >/dev/null 2>&1; then
        log "WARN" "influx CLI missing — assuming Arduino alive (will not USB-reset)"
        echo 0
        return
    fi

    # Hardening 2026-05-19: distinguish "Arduino dead" from "InfluxDB / NR
    # write pipeline broken". Probe InfluxDB itself with a known-fresh
    # non-arduino measurement first. If the probe is empty, InfluxDB is the
    # problem (or NR can't write to it) — we cannot trust the arduino_status
    # staleness signal, so assume alive and refuse to USB-reset. Without this
    # gate, an InfluxDB outage manifests as a USB-reset storm that physically
    # interrupts the fans every ~60 s via the Bug-5-fix-driven pin disconnect
    # at Arduino init. See memory/incident-2026-05-19-fan-cascade.md.
    local probe
    probe=$(influx -database highland -execute \
        "SELECT last(value) FROM local_temperature WHERE time > now() - 5m" \
        2>/dev/null | tail -1)
    if [ -z "$probe" ]; then
        log "WARN" "InfluxDB probe (local_temperature) empty — InfluxDB or NR write pipeline likely broken; assuming Arduino alive (will not USB-reset)"
        echo 0
        return
    fi

    local result status_val
    result=$(influx -database highland -execute \
        "SELECT last(value) FROM arduino_status WHERE time > now() - 5m" \
        2>/dev/null | tail -1)

    if [ -z "$result" ]; then
        echo 60
        return
    fi

    status_val=$(echo "$result" | awk '{print $NF}')

    if [ "$status_val" = "1" ]; then
        echo 0
    else
        echo 60
    fi
}

usb_reset_device() {
    local now
    now=$(date +%s)

    # Cooldown check
    if [ $(( now - LAST_USB_RESET )) -lt "$USB_RESET_COOLDOWN" ]; then
        return 1
    fi

    log "ACTION" "USB reset — toggling $USB_SYSFS_PATH/authorized"
    echo 0 > "$USB_SYSFS_PATH/authorized"
    sleep 1
    echo 1 > "$USB_SYSFS_PATH/authorized"
    LAST_USB_RESET=$(date +%s)

    # Wait for device to reappear
    local waited=0
    while [ ! -e "$DEVICE" ] && [ "$waited" -lt 15 ]; do
        sleep 1
        waited=$((waited + 1))
    done

    if [ -e "$DEVICE" ]; then
        log "INFO" "Device back after ${waited}s — NR will auto-reconnect"
        return 0
    else
        log "ERROR" "Device did NOT reappear after USB reset"
        return 1
    fi
}

reboot_system() {
    local sys_uptime
    sys_uptime=$(awk '{print int($1)}' /proc/uptime)
    if [ "$sys_uptime" -lt "$REBOOT_COOLDOWN" ]; then
        log "WARN" "System only up ${sys_uptime}s — skipping reboot"
        return 1
    fi
    log "ACTION" "Rebooting system"
    sync
    reboot
}

# --- Main loop ---

log "INFO" "Watchdog v10 started (interval=${CHECK_INTERVAL}s, stale_threshold=${HEARTBEAT_STALE_THRESHOLD}s, reset_cooldown=${USB_RESET_COOLDOWN}s)"

# Bootstrap LAST_HEARTBEAT_OK to startup time so the first stale check after
# NR grace can actually act. Without this, a stall already in progress at
# watchdog startup is silently ignored forever (was 8h on 2026-04-07/08).
LAST_HEARTBEAT_OK=$(date +%s)

sleep 30  # Initial grace on startup

while true; do
    rotate_log

    # 1. Device present?
    if [ ! -e "$DEVICE" ]; then
        now=$(date +%s)
        if [ "$device_missing_since" -eq 0 ]; then
            device_missing_since=$now
            log "WARN" "Device $DEVICE missing"
        fi
        elapsed=$(( now - device_missing_since ))

        if [ "$elapsed" -gt "$DEVICE_MISSING_TIMEOUT" ]; then
            log "ERROR" "Device missing for ${elapsed}s — rebooting"
            reboot_system
        fi
        sleep "$CHECK_INTERVAL"
        continue
    fi

    # Device appeared/reappeared
    if [ "$device_missing_since" -ne 0 ]; then
        log "INFO" "Device $DEVICE reappeared"
        device_missing_since=0
    fi

    # 2. NR running?
    if ! systemctl is-active --quiet nodered; then
        log "WARN" "Node-RED not running — starting"
        systemctl start nodered
        sleep 30
        continue
    fi

    # 3. NR grace period
    nr_up=$(get_nr_uptime)
    if [ "$nr_up" -lt "$NR_GRACE" ]; then
        sleep "$CHECK_INTERVAL"
        continue
    fi

    # 4. Check heartbeat — the core logic
    hb_age=$(get_heartbeat_age)

    if [ "$hb_age" -eq 0 ]; then
        # Healthy — reset tracking. (Dead "Heartbeat OK" log-once branch removed
        # 2026-05-18 — LAST_HEARTBEAT_OK is bootstrapped to nonzero at startup,
        # so the -eq 0 check was unreachable.)
        LAST_HEARTBEAT_OK=$(date +%s)
    else
        # Stale heartbeat
        now=$(date +%s)
        stale_duration=$(( now - LAST_HEARTBEAT_OK ))

        # Only act if stale long enough
        if [ "$LAST_HEARTBEAT_OK" -gt 0 ] && [ "$stale_duration" -gt "$HEARTBEAT_STALE_THRESHOLD" ]; then
            log "WARN" "Heartbeat stale for ${stale_duration}s — prodding USB"
            usb_reset_device
            # Give NR time to reconnect after reset
            sleep 20
            continue
        fi
    fi

    sleep "$CHECK_INTERVAL"
done
