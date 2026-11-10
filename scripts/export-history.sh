#!/usr/bin/env bash
# Export the terrarium's InfluxDB history for offline analysis
# (analysis/timeseries/run_analysis.R --export <dir>).
#
# Run on the Pi as user pi:
#
#   curl -fsSL https://raw.githubusercontent.com/GabrieleZoppoli/terrarium-control-system/claude/raspberry-pi-terrarium-debug-zsiv9y/scripts/export-history.sh | bash
#
# What it does:
#   1. Reads InfluxDB (read-only), month by month so the Pi is never asked for
#      one huge result: 5-minute means of the core channels, raw points for
#      events and change-only channels, hourly means of everything else.
#   2. Adds a few non-secret diagnostics: disk usage, the SD-backup log tail,
#      the health ledger if present.
#   3. Publishes the result:
#        --to github (default)  one commit on branch `data-export` of
#                               GabrieleZoppoli/terrarium-analysis, using the
#                               Pi's existing git login. That repository is
#                               PUBLIC (it already holds sensor CSVs).
#        --to drive             private: rclone copy to gdrive:terrarium-exports/
#        --to file              keep the archive on the Pi only
#      A copy always stays in ~/terrarium-exports/.
#
# Options:  --days N   how far back to go (default 400 = everything kept)
set -euo pipefail

DB="${DB:-highland}"
INFLUX_URL="${INFLUX_URL:-http://localhost:8086}"
DAYS=400; TO=github
while [ $# -gt 0 ]; do
  case "$1" in
    --days) DAYS="$2"; shift 2 ;;
    --to)   TO="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

say() { printf '\n\033[1m▶ %s\033[0m\n' "$*"; }
ok()  { printf '  ✓ %s\n' "$*"; }

STAMP=$(date +%Y%m%d-%H%M)
KEEP_DIR="$HOME/terrarium-exports"; mkdir -p "$KEEP_DIR"
WORK=$(mktemp -d); OUT="$WORK/export"; mkdir -p "$OUT"
trap 'rm -rf "$WORK"' EXIT

CORE="local_temperature local_humidity vpd target_temperature_computed target_humidity_computed
difference_humidity fan_speed freezer_status mister_status light_status power_consumption
room_temperature room_humidity wbt_shutdown_active pid_control_mode night_test_mode"
RAW="mist_event fan_pwm_outlet fan_pwm_impeller fan_pwm_freezer fan_pwm_circulation"

# One query → CSV rows "name,time(ns),value" on stdout (no header).
q() {
  if command -v influx >/dev/null 2>&1; then
    influx -database "$DB" -format csv -precision ns -execute "$1" 2>/dev/null | tail -n +2
  else
    curl -sS -G "$INFLUX_URL/query" -H 'Accept: application/csv' \
      --data-urlencode "db=$DB" --data-urlencode "epoch=ns" --data-urlencode "q=$1" \
      | tail -n +2 | cut -d, -f1,3-          # drop the empty "tags" column
  fi
}

say "Checking InfluxDB"
curl -fsS -m 5 "$INFLUX_URL/ping" >/dev/null || { echo "  ✗ InfluxDB not answering at $INFLUX_URL" >&2; exit 1; }
ALL=$(q "SHOW MEASUREMENTS" | cut -d, -f2 | tr -d '\r' | grep -E '^[A-Za-z0-9_]+$' || true)
[ -n "$ALL" ] || { echo "  ✗ no measurements found in database $DB" >&2; exit 1; }
ok "$(echo "$ALL" | wc -l) measurements in $DB"

# Month-sized windows from DAYS ago to now.
START=$(date -u -d "$DAYS days ago" +%Y-%m-01)
windows() {
  local a="$START" b
  while [ "$(date -u -d "$a" +%s)" -lt "$(date -u +%s)" ]; do
    b=$(date -u -d "$a +1 month" +%Y-%m-%d); echo "$a $b"; a="$b"
  done
}
export_one() {   # export_one <measurement> <select-expr> <group-by or "">
  local m="$1" sel="$2" grp="$3" f="$OUT/$1.csv" a b
  echo "name,time,value" > "$f"
  while read -r a b; do
    q "SELECT $sel FROM \"$m\" WHERE time >= '${a}T00:00:00Z' AND time < '${b}T00:00:00Z' $grp" >> "$f" || true
  done < <(windows)
  local n=$(( $(wc -l < "$f") - 1 ))
  if [ "$n" -le 0 ]; then rm -f "$f"; else printf '%-34s %8d rows\n' "$m" "$n" >> "$OUT/MANIFEST.txt"; fi
}

say "Exporting (5-minute means, back to $START)"
echo "terrarium export $STAMP, database $DB, from $START" > "$OUT/MANIFEST.txt"
for m in $CORE; do
  echo "$ALL" | grep -qx "$m" || continue
  export_one "$m" "mean(value)" "GROUP BY time(5m) fill(none)"; printf '.'
done
for m in $RAW; do
  echo "$ALL" | grep -qx "$m" || continue
  export_one "$m" "value" ""; printf '.'
done
for m in $ALL; do
  echo "$CORE $RAW" | tr ' \n' '\n\n' | grep -qx "$m" && continue
  export_one "$m" "mean(value)" "GROUP BY time(1h) fill(none)"       # numeric channels
  [ -f "$OUT/$m.csv" ] || export_one "$m" "last(value)" "GROUP BY time(30m) fill(none)"   # text channels
  printf '.'
done
echo
ok "$(ls "$OUT"/*.csv | wc -l) files, $(du -sh "$OUT" | cut -f1) before compression"

say "Diagnostics (no passwords)"
{
  echo "== date"; date -Is
  echo "== uptime"; uptime
  echo "== df"; df -h / /boot 2>/dev/null
  echo "== biggest folders"
  for d in /var/lib/influxdb /var/log /home/pi /home/pi/snapshots /home/pi/.node-red /var/cache /tmp; do
    [ -e "$d" ] && timeout 60 du -sh "$d" 2>/dev/null
  done
  echo "== largest items under /home/pi"; timeout 90 du -xh --max-depth=2 /home/pi 2>/dev/null | sort -h | tail -15
  echo "== sd-backup log (tail)"; tail -n 60 /var/log/sd-backup.log 2>/dev/null | grep -E "start|OK|FAIL|pruned|elapsed" || echo "(not readable)"
  echo "== services"
  for s in nodered influxdb grafana-server meross-daemon conditions-server arduino-watchdog; do
    printf '%s=%s\n' "$s" "$(systemctl is-active "$s" 2>/dev/null)"
  done
  echo "== tailscale funnel"; timeout 10 tailscale funnel status 2>&1 | head -8 || true
  echo "== installed report scripts"; ls -la /usr/local/bin/terrarium-*.py 2>/dev/null
} > "$OUT/diagnostics.txt" 2>&1 || true
[ -f "$HOME/.terrarium-health-ledger.jsonl" ] && cp "$HOME/.terrarium-health-ledger.jsonl" "$OUT/health-ledger.jsonl"
ok "diagnostics.txt written"

gzip -9 "$OUT"/*.csv
TARBALL="$KEEP_DIR/terrarium-export-$STAMP.tar.gz"
tar -C "$WORK" -czf "$TARBALL" export
ok "archive: $TARBALL ($(du -h "$TARBALL" | cut -f1))"

publish_github() {
  local url=""
  for d in "$HOME"/terrarium-analysis "$HOME"/terrarium-control-system "$HOME"/*/; do
    url=$(git -C "$d" remote get-url origin 2>/dev/null | grep -i "GabrieleZoppoli/terrarium-" || true)
    [ -n "$url" ] && break
  done
  [ -n "$url" ] || { echo "  ! no terrarium git clone found on this Pi"; return 1; }
  url=$(echo "$url" | sed -E 's#terrarium-(control-system|analysis)(\.git)?$#terrarium-analysis.git#')
  ( cd "$OUT" && git init -q && git checkout -q -b data-export && git add -A &&
    git -c user.name="terrarium-pi" -c user.email="pi@terrarium.local" commit -qm "data export $STAMP" &&
    git push -q -f "$url" data-export ) || return 1
  ok "pushed to branch data-export of terrarium-analysis (public repository)"
}
publish_drive() {
  command -v rclone >/dev/null 2>&1 || { echo "  ! rclone not installed"; return 1; }
  rclone copy "$TARBALL" gdrive:terrarium-exports/ || return 1
  ok "uploaded to Google Drive: terrarium-exports/$(basename "$TARBALL")"
}

say "Publishing ($TO)"
case "$TO" in
  github) publish_github || { echo "  ! GitHub push failed, trying Google Drive"; publish_drive || echo "  ! not published; the archive is at $TARBALL"; } ;;
  drive)  publish_drive || echo "  ! not published; the archive is at $TARBALL" ;;
  file)   ok "kept on the Pi only" ;;
  *) echo "unknown --to $TO" >&2; exit 2 ;;
esac
say "Done"
