#!/usr/bin/env bash
# Idempotent installer for the time-lapse capture/vision package.
# Copies code to /opt/terrarium-timelapse, creates the archive dirs, adds pi's cron lines.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$(dirname "$HERE")"                 # scripts/timelapse
CAMGATE_SRC="$(dirname "$SRC")/camgate"  # scripts/camgate
DEST=/opt/terrarium-timelapse
DATA=/var/lib/terrarium-timelapse
MARK="# terrarium-timelapse"

command -v jpegtran >/dev/null 2>&1 || { echo "jpegtran missing (apt install libjpeg-turbo-progs)" >&2; exit 1; }

copy_pkg() {  # src dest
  sudo install -d -m 755 "$2"
  if command -v rsync >/dev/null 2>&1; then
    sudo rsync -a --delete --exclude tests/ --exclude deploy/ --exclude __pycache__/ "$1/" "$2/"
  else
    sudo find "$2" -mindepth 1 -delete
    (cd "$1" && tar cf - --exclude=tests --exclude=deploy --exclude=__pycache__ .) | sudo tar xf - -C "$2"
  fi
}
copy_pkg "$SRC" "$DEST/timelapse"
copy_pkg "$CAMGATE_SRC" "$DEST/camgate"
sudo chown -R root:root "$DEST"
sudo chmod -R go-w "$DEST"

for d in frames status logs tmp; do sudo install -d -m 750 -o pi -g pi "$DATA/$d"; done
sudo chown pi:pi "$DATA"; sudo chmod 750 "$DATA"

CRON_CAP='*/10 * * * * cd /opt/terrarium-timelapse && flock -n /tmp/tl-capture.lock nice -n 10 /usr/bin/python3 -m timelapse.capture >/dev/null 2>&1'
CRON_VIS='30 16 * * * cd /opt/terrarium-timelapse && flock -n /tmp/tl-vision.lock nice -n 10 /usr/bin/python3 -m timelapse.vision >/dev/null 2>&1'
CUR="$(crontab -l 2>/dev/null || true)"
if printf '%s\n' "$CUR" | grep -qF "$MARK"; then
  echo "cron: already installed"
else
  [ -n "$CUR" ] && printf '%s\n' "$CUR" > "$HOME/crontab.bak_$(date +%Y%m%d-%H%M%S)"
  { printf '%s\n' "$CUR"; echo "$MARK"; echo "$CRON_CAP"; echo "$CRON_VIS"; } | crontab -
  echo "cron: installed"
fi
echo "timelapse installed in $DEST, data in $DATA"
