#!/usr/bin/env bash
# Idempotent installer for camgate (binds 127.0.0.1:8788 only).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$(dirname "$HERE")"                      # scripts/camgate
DEST=/opt/terrarium-camgate
UNIT=terrarium-camgate.service

sudo install -d -m 755 "$DEST/camgate"
if command -v rsync >/dev/null 2>&1; then
  sudo rsync -a --delete --exclude tests/ --exclude deploy/ --exclude __pycache__/ "$SRC/" "$DEST/camgate/"
else
  sudo find "$DEST/camgate" -mindepth 1 -delete
  (cd "$SRC" && tar cf - --exclude=tests --exclude=deploy --exclude=__pycache__ .) | sudo tar xf - -C "$DEST/camgate"
fi
sudo chown -R root:root "$DEST"
sudo install -m 644 "$HERE/$UNIT" "/etc/systemd/system/$UNIT"
sudo systemctl daemon-reload
if systemctl is-active --quiet "$UNIT"; then
  sudo systemctl enable "$UNIT"
  sudo systemctl restart "$UNIT"
else
  sudo systemctl enable --now "$UNIT"
fi
echo "camgate installed: $(systemctl is-active "$UNIT")"
