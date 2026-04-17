---
title: "Live Terrarium"
description: "Near-live view of the highland control UI — a fresh snapshot every 15 minutes"
weight: 5
layout: "live"
snapshotURL:      "https://rei1.tail7cc014.ts.net/highland/ui-latest.png"
liveURL:          "http://rei1.tail7cc014.ts.net:1880/ui/"
snapshotInterval: 60
---

A headless Chromium on the Pi captures the Node-RED control UI every 15 minutes and publishes the PNG over a Tailscale Funnel endpoint. That's what's rendering below — close enough to live for most purposes, without exposing the dashboard itself to the open internet.

If you're on my tailnet, the *interactive* dashboard is one hop away too — the link opens it in Node-RED proper, where you can flip setpoints and scrub graphs. Otherwise the image refreshes on its own.
