#!/bin/bash
# snapshot-capture.sh — Capture Grafana dashboard screenshots and push to GitHub
# Runs as cron every 6 hours: 0 0,6,12,18 * * * /path/to/snapshot-capture.sh
#
# Prerequisites:
#   - chromium-browser installed
#   - Grafana anonymous access enabled in /etc/grafana/grafana.ini:
#       [auth.anonymous]
#       enabled = true
#       org_role = Viewer
#   - Git repo with SSH key or token configured for push
set -e

REPO_DIR="/home/pi/terrarium-paper"
SNAPSHOT_DIR="$REPO_DIR/website/content/dashboard/snapshots"
GRAFANA_URL="http://localhost:3000"
TIMESTAMP=$(date +%Y-%m-%d_%H%M)
WIDTH=1600
HEIGHT=900

# Dashboards to capture (uid:name pairs)
declare -A DASHBOARDS=(
  ["terrarium-roraima"]="Terrarium Roraima"
  ["system-performance"]="System Performance"
)

# Time ranges: now-24h and now-7d
declare -A RANGES=(
  ["24h"]="now-24h"
  ["7d"]="now-7d"
)

mkdir -p "$SNAPSHOT_DIR"

for uid in "${!DASHBOARDS[@]}"; do
  for label in "${!RANGES[@]}"; do
    from="${RANGES[$label]}"
    outfile="$SNAPSHOT_DIR/${uid}_${label}.png"

    url="${GRAFANA_URL}/d/${uid}?orgId=1&from=${from}&to=now&kiosk=1"

    chromium-browser \
      --headless \
      --no-sandbox \
      --disable-gpu \
      --disable-software-rasterizer \
      --window-size=${WIDTH},${HEIGHT} \
      --screenshot="$outfile" \
      --virtual-time-budget=10000 \
      "$url" 2>/dev/null || {
        echo "WARNING: Failed to capture ${uid} ${label}" >&2
        continue
      }

    echo "Captured: ${uid}_${label}.png"
  done
done

# Update the dashboard page with fresh image references
cat > "$REPO_DIR/website/content/dashboard/_index.md" << 'DASHEOF'
---
title: "Live Dashboard"
description: "Grafana dashboard snapshots updated every 6 hours"
---

Automated snapshots of the terrarium's Grafana dashboards, captured every 6 hours by a cron job on the Raspberry Pi.

## Terrarium Roraima — 24 hours

![Terrarium Roraima 24h](snapshots/terrarium-roraima_24h.png)

## Terrarium Roraima — 7 days

![Terrarium Roraima 7d](snapshots/terrarium-roraima_7d.png)

## System Performance — 24 hours

![System Performance 24h](snapshots/system-performance_24h.png)

## System Performance — 7 days

![System Performance 7d](snapshots/system-performance_7d.png)

---

*Snapshots captured automatically every 6 hours (00:00, 06:00, 12:00, 18:00 CET).*
DASHEOF

# Commit and push if there are changes
cd "$REPO_DIR"
git add website/content/dashboard/
if git diff --cached --quiet; then
  echo "No changes to commit."
else
  git commit -m "dashboard: update snapshots ${TIMESTAMP}"
  git push origin master 2>/dev/null || git push origin main 2>/dev/null || {
    echo "WARNING: Push failed. Snapshots committed locally." >&2
  }
fi

echo "Snapshot capture complete: ${TIMESTAMP}"
