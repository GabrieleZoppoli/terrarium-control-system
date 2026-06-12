#!/bin/bash
# Arduino Mega Connection Monitor
# Logs disconnections and optionally restarts Node-RED

DEVICE="/dev/ttyACM0"
LOGFILE="/var/log/arduino-monitor.log"
CHECK_INTERVAL=30

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOGFILE"
}

log "Arduino monitor started"

was_connected=false

while true; do
    if [ -e "$DEVICE" ]; then
        if [ "$was_connected" = false ]; then
            log "Arduino CONNECTED at $DEVICE"
            was_connected=true
        fi
    else
        if [ "$was_connected" = true ]; then
            log "Arduino DISCONNECTED! Device $DEVICE missing"
            # Log dmesg for debugging
            dmesg | tail -10 >> "$LOGFILE"
            was_connected=false
        fi
    fi
    sleep $CHECK_INTERVAL
done
