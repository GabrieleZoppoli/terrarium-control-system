#!/bin/bash
# thermal-guard.sh — pause the broadcast if the SoC gets too hot, resume when it
# cools. The climate controller must never be put at thermal risk by the stream.
# Runs as root (needs systemctl). P1 measured ~58C under load, so this should
# essentially never fire — it's a safety net well below the Pi's ~80C throttle.
set -u
HOT="${HOT:-78}"      # stop streaming at/above this SoC temp (C)
COOL="${COOL:-68}"    # resume once back at/below this
SVC="terrarium-stream.service"
FLAG="/run/hcf-thermal-paused"

while true; do
  t=$(vcgencmd measure_temp 2>/dev/null | grep -oE '[0-9]+' | head -1)
  [ -z "$t" ] && { sleep 20; continue; }
  if [ "$t" -ge "$HOT" ] && systemctl is-active --quiet "$SVC"; then
    logger -t hcf-thermal "SoC ${t}C >= ${HOT}C — pausing broadcast (plants > pixels)"
    systemctl stop "$SVC"
    touch "$FLAG"
  elif [ "$t" -le "$COOL" ] && [ -f "$FLAG" ]; then
    logger -t hcf-thermal "SoC ${t}C <= ${COOL}C — resuming broadcast"
    rm -f "$FLAG"
    systemctl start "$SVC"
  fi
  sleep 20
done
