# Highland Cloud Forest — 24/7 YouTube live broadcast

**Date:** 2026-06-09
**Status:** approved design (brainstorming complete)
**Host:** controller `rei1` (192.168.1.168, Raspberry Pi 4B 8 GB, Debian 12)

## Goal

A continuous YouTube live stream of the terrarium cabinet, composited with the
live Node-RED dashboard, with automatic and manually-triggered event captions
and a calm soundscape — running on the control Pi **without ever endangering
the climate-control loop** (the Pi keeps 75 living plants alive; plants > pixels).

## Hardware / inputs (verified during install)

- **Camera:** HQCAM UVC USB camera `2ce3:c670` on `/dev/video0`. MJPG up to
  **1920×1080@30** (also 1280×720/1024, etc.). Wide-angle, IR night-vision
  (hardware photoresistor-triggered, no SW control), fixed lens (~2 m factory
  focus, hand-twist for closer). **Has a built-in mic** (enumerates as USB Audio,
  `arecord` card 3).
- **Live camera feed:** `ustreamer` 4.9 installed as systemd service
  `terrarium-cam`, MJPEG passthrough (HW), bound `0.0.0.0:8080`, `--slowdown`
  when idle. Endpoints `/stream`, `/snapshot`, `/state`.
- **Dashboard:** Node-RED UI at `http://localhost:1880/ui` (chosen over Grafana —
  live websocket gauges read better than static snapshots).
- **Encoders available:** `h264_v4l2m2m` (HW), `h264_omx`. HW JPEG decode for
  the camera. `ffmpeg` present.

## Decisions

| Item | Decision |
|---|---|
| Encoder host | Controller `.168`, CPU-capped (NOT offloaded to 2nd Pi) |
| Overclock | **No** by default; revisit only if P1 measurements force it, and only with confirmed active cooling |
| Layout | Split: camera ~65 % left + Node-RED `/ui` panel ~35 % right |
| Resolution | **1080p** (framerate tuned in P1 for thermal safety) |
| Audio | Live camera mic (high-pass + soft limiter) mixed with a generative relaxing **highland-cloud-forest ambient bed** — water drops, mist, soft wind. **No gongs, no birds.** All CC0/self-generated → no Content-ID risk |
| Output | HW `h264_v4l2m2m` + AAC → `rtmp://a.rtmp.youtube.com/live2/<KEY>` |

## Pipeline — ffmpeg-native composite (chosen)

A single `ffmpeg` process is the spine. *(Alternative rejected: full headless-browser
OBS-style scene — continuous 30 fps Chromium is too heavy for the life-support box.)*

Layers:
1. **Camera** — ffmpeg consumes ustreamer MJPEG (HW JPEG decode). Left ~65 %.
   To minimise scaling cost, ustreamer outputs at/near the panel target size.
2. **Dashboard panel** — a lightweight grabber screenshots `/ui` every ~2 s →
   `dashboard.png`; ffmpeg overlays it (right ~35 %). Inherits Node-RED styling;
   gauges current within ~2 s.
3. **Event banner** — Node-RED writes a styled `banner.png` on events; ffmpeg
   overlays it (designed look, not plain text). Cleared when the event ends.
4. **Chrome** — title + running clock + "Day N of continuous operation."
5. **Audio** — camera mic (ALSA hw:3) high-passed + soft-limited, mixed (`amix`)
   with the generative ambient bed.

## Events (Node-RED already owns these states)

- **Auto:** misting on/off 💧, photoperiod sunrise/sundown ☀/🌙, door-open 🚪.
- **Manual suspense:** a button/field on the Node-RED `/ui` (reachable from the
  user's phone on the LAN, where he is when opening the cabinet) — "maintenance
  in N min" → on-screen countdown to pre-announce the door-opening drama.

## Safety / isolation (non-negotiable)

- systemd `terrarium-stream`: `CPUQuota` (~150 % of 400 %), `Nice=10`,
  `IOSchedulingClass=idle`, `MemoryMax`. Node-RED / InfluxDB always preempt it.
- Temp guard: if SoC > ~75 °C, the stream throttles/pauses. Plants > pixels.
- `Restart=always` + ffmpeg `-reconnect` for RTMP drops; boot-persistent.

## Phased build (each independently verifiable)

- **P1 — Prove the pipe:** camera-only → local preview (HLS/file), 1080p,
  HW-encoded, CPU-capped, thermal guard, boot service. Measure CPU/temp/throttle
  over hours. *(This also settles the overclock question empirically.)*
- **P2 — Composite:** add dashboard panel + title/clock chrome.
- **P3 — Audio:** camera mic + generative ambient bed.
- **P4 — Events:** Node-RED auto-captions + phone-triggered suspense banner.
- **P5 — Polish + go live:** styling, "Day N", swap output to YouTube stream key
  once the channel's 24 h activation completes, optional YouTube embed on
  highlandcloudforest.com.

## User-provided

- YouTube channel: live streaming **activated 2026-06-09**, ~24 h until first
  live allowed. Stream key to be dropped into a secret file on the Pi (never in
  chat), like the SSH password flow.

## Open items

- Pi cooling type (bare / heatsink / active fan) — gates whether OC is ever viable.
- Final framerate (target 1080p; P1 decides 20–30 fps).
- Audio ambient bed sourcing (CC0 samples vs. self-generated drone + drop one-shots).
