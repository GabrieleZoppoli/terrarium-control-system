---
title: "Live Dashboard"
description: "Grafana snapshots of the last 24 h — temperature, humidity, VPD, equipment state"
weight: 6
---

Headless Chromium on the Pi renders the Grafana board to PNG every 15 minutes — one layout optimised for desktop, one for phone — and publishes them over a Tailscale Funnel endpoint. The board itself stays on the tailnet; only these read-only snapshots reach the public internet.

<picture>
  <source media="(max-width: 500px)"
          srcset="https://rei1.tail7cc014.ts.net/highland/grafana-latest-mobile.png">
  <img src="https://rei1.tail7cc014.ts.net/highland/grafana-latest-desktop.png"
       alt="Latest 24-hour Grafana snapshot of the highland terrarium"
       loading="lazy"
       style="width:100%;max-width:1200px;height:auto;border-radius:8px;">
</picture>

<p style="font-size:0.85em;opacity:0.6;margin-top:0.5em;">
Refreshed every 15 min · data for the last 24 h · all times Europe/Rome.
</p>

## What the panels show

- **Hero row** — current temperature, humidity and VPD, each with its own 24-hour sparkline.
- **Target vs actual** — the violet line is the measured value; the amber dashed line is the Colombian-highland setpoint (shifted 15 h to hit Genoese dawn at the tepui equivalent); the green line is the outside room for context.
- **Equipment state** — lights, freezer and mister on/off history as an area chart of the last 24 h.
- **Footer** — latest room temperature, room RH, and system power draw (Meross MSS310).

For the interactive Grafana (tailnet-only) see [rei1.tail7cc014.ts.net:3000](http://rei1.tail7cc014.ts.net:3000).
