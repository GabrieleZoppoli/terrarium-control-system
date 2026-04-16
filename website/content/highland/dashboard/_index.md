---
title: "Live Dashboard"
description: "Grafana dashboard snapshots updated every 6 hours"
---

Automated snapshots of the terrarium's Grafana dashboards, captured every 6 hours by a cron job on the Raspberry Pi. These show the real-time state of the system including temperature, humidity, fan speeds, and actuator status.

## Current Conditions (24-hour view)

[Snapshots will appear here automatically once the snapshot cron is configured. See `scripts/snapshot-capture.sh`.]

## Weekly Overview (7-day view)

[Snapshots will appear here automatically.]

---

*Snapshots are captured at 00:00, 06:00, 12:00, and 18:00 CET and pushed to this site automatically.*

*For real-time monitoring, the Grafana instance runs locally at `http://192.168.1.X:3000` (LAN only).*
