#!/bin/bash
# net-watchdog.sh — independent connectivity probe + InfluxDB log + escalating recovery
# Runs every minute via cron (pi user; uses sudo -n NOPASSWD).
#
# Probes (4s timeout each):
#   - DNS: getent hosts api.openweathermap.org
#   - WAN: curl --head --resolve 1.1.1.1 https://1.1.1.1/
#   - LAN: tcp connect 192.168.1.196:80 (Tapo freezer plug)
#
# InfluxDB measurements (db=highland):
#   net_watchdog_ok, net_watchdog_fails, net_watchdog_dns_ok / _wan_ok / _lan_ok
#   net_watchdog_recovery (tag kind=nmcli_reconnect|nm_restart|reboot)
#
# Escalating recovery (each action has its own 30-min cooldown):
#   5  consec DNS fails → sudo nmcli con down/up preconfigured
#   15 consec DNS fails → sudo systemctl restart NetworkManager
#   30 consec DNS fails → write reboot memory + sudo reboot
#                          (capped at 3/day; needs >=10 min uptime)
#
# Tags: net_watchdog_2026_05_14, escalation_v2_2026_05_14

set -u
LANG=C
LC_ALL=C
INFLUX_URL="http://127.0.0.1:8086/write?db=highland&precision=ms"
STATE_FILE="/var/lib/net-watchdog/state"
LOG_FILE="/var/log/net-watchdog.log"
REBOOT_MEMORY="/home/pi/.claude/projects/-home-pi/memory/auto-reboot-log.md"
TIMEOUT=4

NMCLI_THRESHOLD=5
NMRESTART_THRESHOLD=15
REBOOT_THRESHOLD=30
COOLDOWN_SEC=1800
MAX_REBOOTS_PER_DAY=3
MIN_UPTIME_FOR_REBOOT_SEC=600

mkdir -p "$(dirname "$STATE_FILE")" 2>/dev/null || true
touch "$STATE_FILE" "$LOG_FILE" 2>/dev/null || true

probe_dns() { timeout "$TIMEOUT" getent hosts api.openweathermap.org >/dev/null 2>&1; }
probe_wan() { timeout "$TIMEOUT" curl -s --head --resolve 1.1.1.1:443:1.1.1.1 https://1.1.1.1/ -o /dev/null; }
probe_lan() { timeout "$TIMEOUT" bash -c '</dev/tcp/192.168.1.196/80' 2>/dev/null; }

probe_dns; dns_ok=$?; dns_ok=$(( dns_ok == 0 ? 1 : 0 ))
probe_wan; wan_ok=$?; wan_ok=$(( wan_ok == 0 ? 1 : 0 ))
probe_lan; lan_ok=$?; lan_ok=$(( lan_ok == 0 ? 1 : 0 ))

fails=$(( (1 - dns_ok) + (1 - wan_ok) + (1 - lan_ok) ))
ok=$(( fails == 0 ? 1 : 0 ))

ts_ms=$(date +%s%3N)
log_ts=$(date '+%Y-%m-%d %H:%M:%S')
now_sec=$(date +%s)
today_date=$(date '+%Y%m%d')
uptime_sec=$(awk '{print int($1)}' /proc/uptime)

curl -sS --max-time 3 -XPOST "$INFLUX_URL" --data-binary "
net_watchdog_ok value=$ok $ts_ms
net_watchdog_fails value=$fails $ts_ms
net_watchdog_dns_ok value=$dns_ok $ts_ms
net_watchdog_wan_ok value=$wan_ok $ts_ms
net_watchdog_lan_ok value=$lan_ok $ts_ms
" >/dev/null 2>&1

# State file v2: consec_dns_fails:last_nmcli_ts:last_nmrestart_ts:last_reboot_ts:reboots_today:reboot_day
prev=$(cat "$STATE_FILE" 2>/dev/null || echo "0:0:0:0:0:0")
IFS=':' read -r prev_dns_fails last_nmcli_ts last_nmrestart_ts last_reboot_ts reboots_today reboot_day <<<"$prev"
prev_dns_fails=${prev_dns_fails:-0}
last_nmcli_ts=${last_nmcli_ts:-0}
last_nmrestart_ts=${last_nmrestart_ts:-0}
last_reboot_ts=${last_reboot_ts:-0}
reboots_today=${reboots_today:-0}
reboot_day=${reboot_day:-0}

if [ "$today_date" != "$reboot_day" ]; then
    reboots_today=0
    reboot_day="$today_date"
fi

if [ "$dns_ok" -eq 0 ]; then
    new_dns_fails=$(( prev_dns_fails + 1 ))
else
    new_dns_fails=0
fi

do_reboot=0
do_nmrestart=0
do_nmcli=0

if   [ "$new_dns_fails" -ge "$REBOOT_THRESHOLD" ] \
  && [ $(( now_sec - last_reboot_ts )) -gt "$COOLDOWN_SEC" ] \
  && [ "$reboots_today" -lt "$MAX_REBOOTS_PER_DAY" ] \
  && [ "$uptime_sec" -ge "$MIN_UPTIME_FOR_REBOOT_SEC" ]; then
    do_reboot=1
elif [ "$new_dns_fails" -ge "$NMRESTART_THRESHOLD" ] \
  && [ $(( now_sec - last_nmrestart_ts )) -gt "$COOLDOWN_SEC" ]; then
    do_nmrestart=1
elif [ "$new_dns_fails" -ge "$NMCLI_THRESHOLD" ] \
  && [ $(( now_sec - last_nmcli_ts )) -gt "$COOLDOWN_SEC" ]; then
    do_nmcli=1
fi

if [ "$do_nmcli" -eq 1 ]; then
    echo "$log_ts RECOVERY-1 (nmcli): DNS failed $new_dns_fails consecutive checks. nmcli reconnect." >> "$LOG_FILE"
    sudo -n nmcli con down preconfigured >> "$LOG_FILE" 2>&1
    sleep 2
    sudo -n nmcli con up preconfigured >> "$LOG_FILE" 2>&1
    last_nmcli_ts="$now_sec"
    curl -sS --max-time 3 -XPOST "$INFLUX_URL" --data-binary "net_watchdog_recovery,kind=nmcli_reconnect value=1 $ts_ms" >/dev/null 2>&1
fi

if [ "$do_nmrestart" -eq 1 ]; then
    echo "$log_ts RECOVERY-2 (NM restart): DNS failed $new_dns_fails consecutive checks. systemctl restart NetworkManager." >> "$LOG_FILE"
    sudo -n systemctl restart NetworkManager >> "$LOG_FILE" 2>&1
    last_nmrestart_ts="$now_sec"
    curl -sS --max-time 3 -XPOST "$INFLUX_URL" --data-binary "net_watchdog_recovery,kind=nm_restart value=1 $ts_ms" >/dev/null 2>&1
fi

if [ "$do_reboot" -eq 1 ]; then
    reboots_today=$(( reboots_today + 1 ))
    echo "$log_ts RECOVERY-3 (REBOOT): DNS failed $new_dns_fails consecutive checks. sudo reboot. ($reboots_today/$MAX_REBOOTS_PER_DAY today)" >> "$LOG_FILE"
    last_reboot_ts="$now_sec"
    last_nmcli_ts="$now_sec"
    last_nmrestart_ts="$now_sec"

    # Append context to auto-reboot memory log for next Claude session to pick up.
    # File created with leading frontmatter on first write; subsequent runs only append entries.
    # 2026-05-18: ensure the directory exists and log if write fails (was silent).
    mkdir -p "$(dirname "$REBOOT_MEMORY")" 2>/dev/null || true
    if ! touch "$REBOOT_MEMORY" 2>/dev/null; then
        echo "$log_ts REBOOT-MEMORY-WRITE-FAIL: cannot create $REBOOT_MEMORY" >> "$LOG_FILE"
    fi
    if [ ! -s "$REBOOT_MEMORY" ]; then
        cat >> "$REBOOT_MEMORY" <<EOF
---
name: auto-reboot-log
description: "Append-only log of watchdog-triggered Pi reboots. Each entry: timestamp, reason, fails count, today's reboot tally, key state at time of reboot."
metadata:
  type: project
---

# Auto-reboot log (net-watchdog escalation)

Watchdog reboots are escalation step 3, fired after 30 consecutive DNS-fail checks (~30 min) when NetworkManager restart already failed to recover. After reboot the @reboot cron launches \`screen -dmS claude\` running \`claude\` so you can attach via \`screen -r claude\`.

Read this file at session start to know whether the last reboot was watchdog-triggered (vs. user-initiated). Most recent entry is at the bottom.

---

EOF
    fi
    cat >> "$REBOOT_MEMORY" <<EOF
## ${log_ts} CEST — auto-reboot #${reboots_today}/${MAX_REBOOTS_PER_DAY} today
- Trigger: $new_dns_fails consecutive DNS-fail checks (~$new_dns_fails min)
- Probes at last check: dns=$dns_ok wan=$wan_ok lan=$lan_ok
- Last action timestamps before this reboot:
  - nmcli reconnect: $(date -d "@$last_nmcli_ts" '+%Y-%m-%d %H:%M' 2>/dev/null || echo "never")
  - NM restart:      $(date -d "@$last_nmrestart_ts" '+%Y-%m-%d %H:%M' 2>/dev/null || echo "never")
- Uptime before reboot: $((uptime_sec/60)) min
- After reboot: \`screen -r claude\` to attach. If outages persist, MAC rotation already in place (see [network-drops-diagnosis-2026-05-14](network-drops-diagnosis-2026-05-14.md)).

EOF

    # B2 (2026-05-18): write counter as 0 so the post-reboot watchdog starts
    # with a fresh count. Without this, persistent outages re-reboot every ~30 min
    # after cooldown, burning the 3/day cap in ~2 hours.
    echo "0:${last_nmcli_ts}:${last_nmrestart_ts}:${last_reboot_ts}:${reboots_today}:${reboot_day}" > "$STATE_FILE"
    curl -sS --max-time 3 -XPOST "$INFLUX_URL" --data-binary "net_watchdog_recovery,kind=reboot value=1 $ts_ms" >/dev/null 2>&1
    sync
    sudo -n reboot
    exit 0
fi

echo "${new_dns_fails}:${last_nmcli_ts}:${last_nmrestart_ts}:${last_reboot_ts}:${reboots_today}:${reboot_day}" > "$STATE_FILE"

if [ "$fails" -gt 0 ]; then
    echo "$log_ts FAIL: dns=$dns_ok wan=$wan_ok lan=$lan_ok consec_dns_fails=$new_dns_fails" >> "$LOG_FILE"
fi
