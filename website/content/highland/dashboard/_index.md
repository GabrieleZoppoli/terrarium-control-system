---
title: "Live Dashboard"
description: "The last 24 h inside the terrarium: temperature, humidity, VPD, power, freezer and mister"
weight: 6
---

A small script on the Pi redraws these charts every minute straight from the sensor database (InfluxDB) and publishes them over a Tailscale Funnel endpoint, one layout for desktop and one for phone. The control system itself stays private; only these read-only images reach the public internet.

<picture>
  <source media="(max-width: 600px)" srcset="https://rei1.tail7cc014.ts.net/highland/dashboard-mobile.png">
  <img src="https://rei1.tail7cc014.ts.net/highland/dashboard-desktop.png" data-refresh="60"
       onerror="this.onerror=null;this.src='https://rei1.tail7cc014.ts.net/highland/grafana-latest-desktop.png'"
       alt="The last 24 hours inside the highland terrarium" loading="eager"
       style="width:100%;max-width:1400px;height:auto;border-radius:8px;">
</picture>
<script>
setInterval(function () {
  if (document.visibilityState !== 'visible') return;
  var pic = document.querySelector('picture img[data-refresh]');
  if (!pic) return;
  var t = '?t=' + Date.now();
  var src = pic.parentNode.querySelector('source');
  if (src) src.srcset = 'https://rei1.tail7cc014.ts.net/highland/dashboard-mobile.png' + t;
  pic.src = 'https://rei1.tail7cc014.ts.net/highland/dashboard-desktop.png' + t;
}, 60000);
</script>

<p style="font-size:0.85em;opacity:0.6;margin-top:0.5em;">
Redrawn every minute · last 24 h · times Europe/Rome · night (lights off) shaded
</p>

## What the charts show

- **Top line**: the room around the cabinet (temperature and RH), the water tank level, and the system's power draw right now.
- **Temperature and humidity**: the coloured line is the cabinet; the dashed line is the Colombian-highland setpoint (shifted 15 h so Genoese dawn matches the tepui's); the grey line is the room, for context. Night is shaded, so the nightly cool-down and humidity rise are easy to see.
- **VPD**: vapour-pressure deficit, how strongly the air pulls water from the leaves. Low is what cloud-forest plants want.
- **Power**: the whole system's draw (Meross MSS310); the night plateau is the compressor.
- **Freezer and mister**: on/off strips on the same timeline.
