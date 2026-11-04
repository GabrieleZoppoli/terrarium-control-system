---
title: "Live Terrarium"
description: "Near-live view of the Node-RED control UI: a fresh snapshot every 15 minutes, plus the live-conditions strip on the Highland page."
weight: 5
layout: "live"
snapshotURL:      "https://rei1.tail7cc014.ts.net/highland/ui-latest.png"
liveURL:          "http://rei1.tail7cc014.ts.net:1880/ui/"
snapshotInterval: 60
---

A headless Chromium on the Raspberry Pi captures the Node-RED control UI every 15 minutes and publishes the PNG over a Tailscale Funnel endpoint. That is what renders below: close enough to live for most purposes, without exposing the dashboard itself to the open internet (the UI has buttons that switch Tapo outlets; a picture is the right level of access for anyone who isn't me).

For a faster read of what's actually happening inside the cabinet, see the live conditions strip on the [Highland landing](../): temperature, humidity, VPD and compressor state, polled every few seconds from a read-only JSON endpoint on the Pi.

On my tailnet the *interactive* dashboard is one hop away: the `liveURL` link opens it in Node-RED proper, where setpoints and graphs are editable. Otherwise the image below refreshes on its own.
