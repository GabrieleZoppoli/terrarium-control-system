# Live terrarium camera + automatic flowering time-lapse — design

Date: 2026-11-24 · Status: final draft, awaiting owner approval · Owner: Gabriele (the terrarium owner)

Two connected features built on the existing terrarium webcam:

- **A. Live camera page** on the public website (highlandcloudforest.com).
- **B. Automatic flowering time-lapse**: Heliamphora flowerings are found, tracked and turned into short films with no human involvement.

Both share one camera, one privacy gatekeeper and one overlay style.

---

## 1. Intent and why

The terrarium is a long-running scientific and personal project (highland cloud-forest plants, ~120 species, running since 2022) with a public website and papers. Visitors currently see numbers and dashboard images. The owner wants them to *see the plants alive*: a real live view with the live readings on top, and, over months, films of Heliamphora flower stalks rising and opening.

The camera sits in the owner's living room. **Privacy is the overriding concern**: the owner must never appear on the public site unless they choose to, and the living room must never be visible.

## 2. Goals

- A visitor opening the camera page sees **live, high-resolution video** of the terrarium immediately, with an **overlay of live readings** (temperature, humidity, lights on/off) and a "LIVE" badge with a countdown.
- After **30 seconds** live, the page switches to a **sharp still photo refreshed every few minutes**, with a "Watch live again" button (another 30 s, rate-limited). Purpose of the cap: protect the Pi's CPU and the home upload bandwidth from visitors who leave tabs open.
- **Night** (lights off): the same flow, using the camera's live infrared (black and white).
- **Doors open → camera private** immediately (blurred last frame plus a "Gardener at work" card) until the doors close, **unless** the owner has switched **"show me"** on.
- **Flowering time-lapse, fully automatic**: a vision model spots new Heliamphora flower stalks, an overlay arrow plus "day N since the stalk appeared / day N of flowering" counters follow each one, and when the flower fades a short film is rendered and published.

## 3. Non-goals

- No continuous public recording or archive of the live view. The existing private 24 h DVR stays as it is and is not exposed.
- No camera motion or optical zoom. The camera's UVC zoom, pan and focus controls are **fake** (verified 2026-11-23: fixed 3.6 mm lens, no effect), and the camera is never physically moved by this system.
- No audio anywhere. The microphone is disabled in the DVR (`AUDIO=off`, 2026-11-23) and must stay off.
- No human confirmation step for detections: the owner explicitly chose fully automatic and accepts occasional wrong arrows.
- Time-lapse covers Heliamphora flowering only, for now.

## 4. Anti-goals (failure even if it "works")

1. **The owner appears on the public site without having switched "show me" on.** This includes a few seconds of lag after a door opens, a stale door signal, or a cached frame served after the doors open.
2. **The living room is visible on the public site.** That means any frame not cropped to the agreed region, including the still photo, the films, social previews and error paths.
3. **The raw camera stream (full frame) becomes reachable from outside the Pi.**
4. **The terrarium's control system gets slower or less reliable.** Node-RED, InfluxDB, the serial link to the Arduino and the health checks take priority over viewers. The Pi is already loaded (load average ~3.4 of 4 cores, swap full, DVR encoding ~44% of a core).
5. Films that flicker or jump in brightness, which makes the growth unreadable.

## 5. Hard constraints and existing system

- **Hardware:** Raspberry Pi 4 (8 GB), hostname `rei1`. USB UVC camera (Alcorlink 2ce3:c670) with IR night illumination, max 1920×1080 at 30 fps, MJPEG.
- **Camera service:** `terrarium-cam.service` runs ustreamer v4.9 at 1920×1080, 8 fps, bound to **127.0.0.1:8080 only**. Endpoints `/stream` (MJPEG) and `/snapshot` (JPEG). It must stay loopback-only.
- **Privacy crop:** the right part of the frame shows the living room through the glass. The agreed public region is **x 0–1344, y 0–1080** (`CROP=1344:1080:0:0` in `/etc/surveil/surveil.conf`). This must be the single source of truth for the crop. If the camera is later re-aimed, every public output must follow the new value automatically. **Fail closed on the crop too (my call):** a missing, empty or unparseable `CROP` means *private*, not full frame; publishing the uncropped frame requires an explicit `CROP=none`.
- **Private DVR:** `surveil-recorder.service` (ffmpeg → encrypted HLS, 24 h retention, tailnet-only web UI on :8090/:8443) reads ustreamer's `/stream`. It must keep working unchanged.
- **Public exposure path:** the only public entry point is **Tailscale Funnel** → `127.0.0.1:8787` (`/home/pi/snap-renderer/conditions-server.py`, a threaded `http.server`, systemd `conditions-server.service` with `ProtectSystem=strict`/`ProtectHome=read-only`). It already serves `/api/conditions.json` (live readings, CORS `*`) and whitelisted `/highland/*.png` images. Anything public must go through this path; do not open new Funnel routes or ports.
- **Doors:** the Arduino reports door contacts (`D22` left, `D24` right) over serial to Node-RED, which sets globals `doors_open` / `doors_status` **instantly**. They are **not** in InfluxDB or MQTT today, and the on-disk global context flushes only every ~30 s, which is **too slow for privacy**.
- **Lights:** Node-RED globals give today's schedule in minutes from midnight. The light curve holds a **60% plateau from `midday_up`+30 to `midday_down`** (today ≈12:17–14:43, centred on ~13:15). This is the only fixed-brightness window of the day.
- **Website:** Hugo at `terrarium-paper/website`, deployed by GitHub Actions to GitHub Pages (highlandcloudforest.com). A placeholder webcam section exists (`content/highland/webcam/_index.md` + `_index.it.md`, marker `<!-- WEBCAM_EMBED_HERE -->`), bilingual EN/IT. Live data is fetched client-side from `https://rei1.tail7cc014.ts.net/...` (see `layouts/partials/highland-live.html`). Website changes are normally coordinated with the Mac-side Claude via `website/HANDOFF.md` and git.
- **Secrets / Claude access:** vision runs through the **Claude Code CLI already installed on the Pi** (`~/.local/bin/claude`, headless `claude -p` with an image), on the owner's existing Claude plan, **not** a separately billed API key. Note: `ANTHROPIC_API_KEY` is exported in the owner's `~/.bashrc`; the detection job must run with that variable **unset**, otherwise the CLI bills the API instead of using the plan. Any other secrets go in `/etc/terrarium/secrets.env` (mode 600), never in code or the repo.
- **Disk:** about 68 GB free on the SD card. The repo must never contain camera frames or films.
- **Repo hygiene:** the weekly flows sync pushes from this repo; `.superpowers/` is gitignored.

## 6. Part A: live camera page

### 6.1 What the visitor sees (agreed with the owner via mockups)

| State | When | Shows |
|---|---|---|
| Live | first 30 s after the page opens, or after "Watch live again" | cropped live video, high resolution, "● LIVE · 0:18 left" badge + progress bar, readings strip (°C, % RH, lights on/off) |
| Still | after 30 s | latest cropped high-res photo, "updated N min ago" badge, readings strip, "▶ Watch live again" button |
| Private | any door open (and "show me" off), or door state unknown | blurred last *pre-opening* frame + card "🌿 Gardener at work: the camera is paused while the terrarium is being tended. Back in a moment." |
| Night | lights off | same as Live/Still, using the infrared picture, readings strip adds "🌙 night, lights off" |
| Busy | live viewer cap reached | still photo + note that live is busy, with automatic retry |

The overlay style is the one in the mockup: semi-transparent dark chips on the picture, rounded frame, red live dot. Readings come from the existing `/api/conditions.json`. The page is bilingual (EN/IT) like the rest of the site. **Social preview / thumbnail (my call):** a fixed, non-camera image already used by the site, never a live or recent camera frame (crawlers cache previews indefinitely).

### 6.2 Privacy gatekeeper (the core of Part A)

A single component on the Pi sits between ustreamer and the public. Nothing else serves camera pixels publicly. Its rules:

1. **Every public pixel is cropped** to the region from `surveil.conf` before leaving the Pi, for live frames, stills, previews and films alike.
2. **Fail closed:** the camera is public only when the gatekeeper has a **fresh positive "doors closed" signal**. If the door signal is missing, stale (older than a few seconds) or ambiguous, or Node-RED is down, it shows **Private**.
3. **Instant cut:** when a door opens, live streams stop sending new frames immediately (within about a second), and the still endpoint keeps serving the last frame captured **before** the opening.
4. **"Show me"** overrides the door rule only while it's on. It **switches itself off automatically** after a timeout (owner's existing rule: every manual override must auto-revert). Default 30 min, my call.
5. **Live session limits:** 30 s per session, a per-visitor cooldown on "Watch live again", and a global cap on simultaneous live viewers. When the cap is reached, new visitors get Still + "busy". Exact numbers are for the builder, sized so live viewing can't starve the control system (anti-goal 4).
6. **One camera read for all viewers:** the gatekeeper reads ustreamer once and fans frames out, so it does not open a stream per visitor. When nobody is watching live, it does no live work.

### 6.3 Door signal and "show me" switch

- Node-RED publishes door state the moment it changes (from the same handler that sets `doors_open`), plus a periodic heartbeat so the gatekeeper can tell "closed" from "silent". The transport is the builder's choice. MQTT on localhost:1883 (already running) with a retained topic is the natural fit.
- "Show me" is a switch on the existing Node-RED dashboard. Its state and expiry are published the same way. The dashboard shows the remaining time.
- Node-RED changes must not alter any existing control behaviour (door-safety light/freezer logic stays untouched). They are additive publish nodes only.

### 6.4 Resolution and bandwidth

The owner asked for **high resolution live**. The full cropped frame (1344×1080) at a low frame rate (around 2–4 fps; builder to tune) is the default. Expect about 0.3–1 MB/s per live viewer, so the viewer cap mostly protects home upload bandwidth. The owner prefers capped viewers with full quality over more viewers with lower quality (my call, played back and not objected to). Cropping without re-encoding (lossless JPEG crop on MCU boundaries, since 1344 is a multiple of 16) is a suggested way to keep the CPU cost low; the method is the builder's choice.

### 6.5 Website side

- Fill the existing `highland/webcam` section (EN + IT) using the placeholder marker, styled to match the mockup.
- The page fetches stills, live and status from the gatekeeper's public routes on `rei1.tail7cc014.ts.net` and readings from `/api/conditions.json`.
- **Who does the website work:** see open question in §9.

## 7. Part B: automatic flowering time-lapse

### 7.1 Capture

- Frames are taken **only during the daily 60% light plateau** (`midday_up`+30 → `midday_down`, read from Node-RED each day) so brightness is constant and films don't flicker. Default: one frame every **5 minutes** (about 25–30 frames/day), my call.
- Frames with the **doors open** are discarded, as are frames within a short margin after the doors close (owner's hands, disturbed plants, misting splashes). Frames taken during a misting burst are discarded too.
- Frames are stored **cropped**, full resolution, as JPEG, outside the repo and outside the 24 h DVR store, e.g. `/var/lib/terrarium-timelapse/frames/YYYY/MM/DD/HHMM.jpg`. They are kept indefinitely, about 2–3 GB/year, as raw material.
- Camera exposure may drift (auto exposure). Light brightness normalisation across frames at render time is allowed.

### 7.2 Detection (fully automatic, owner's choice)

- Once a day, after the plateau, the best plateau frame is given to **Claude via the headless Claude Code CLI on the Pi** with today's frame plus a few recent days for comparison. It asks: are there Heliamphora flower stalks? Where are they (approximate point or box)? Which are new since yesterday? Has any tracked flower opened or faded?
- The model's answers drive a small **flowering registry** (one record per stalk: position, first-seen date, flowering-start date, end date, status). No human confirmation.
- **Back-dating:** when a new stalk is found, earlier frames may be checked to set "day 1" to when it first became visible.
- The position may drift slightly day to day, so the arrow follows the latest detected position, smoothed.
- Only this daily frame (plus the few comparison frames) leaves the Pi. They're cropped terrarium images, sent to Claude. The owner was told this and accepted fully automatic operation.
- **Usage guard:** no money ceiling is needed (owner's plan, owner's decision). Instead, at most one detection run per day (plus back-dating runs when a new stalk is found), so it never eats noticeably into the owner's own Claude usage. If a run fails (usage limit, CLI logged out), detection skips that day and says so in the daily report.

### 7.3 The film

- When a tracked flowering ends (flower faded), a film is rendered automatically from the plateau frames between "stalk appeared" and "flowering ended". Default length **20–30 s**, my call. Frame rate and interpolation are the builder's choice.
- The film shows the **whole (cropped) terrarium** with:
  - an **arrow** pointing at the stalk,
  - counters **"day N since the stalk appeared"** and, once open, **"day N of flowering"**,
  - a **small zoomed inset** in a corner showing the stalk area (softer than the main picture, which is accepted).
- The same overlay (arrow + counters) also appears on the **live page and the still photo** while a flowering is in progress.
- **Publication:** each finished film is added to a **"Flowerings" gallery** on the website (EN/IT) and announced in the 07:00 report email (`terrarium-report.py`). Films **and the gallery index** are served from the Pi through the gatekeeper (a JSON list of films with dates, plant position and durations). The website renders the gallery in the browser from that JSON, so **the Pi never commits to the website repo** and new films appear with nobody involved (my call).
- **Camera re-aim / crop change:** the registry records the crop geometry with each stalk. A flowering whose frames span a geometry change is **split at the change** into separate films (my call).

## 8. Decisions

**The owner decided:**
- Live first 30 s, then periodic still photos; high-resolution live with the readings overlay.
- Doors open → private (blurred), unless "show me" is on.
- Night → live infrared.
- Time-lapse subject: Heliamphora flowering. The camera stays where it is, the whole view is kept, and an arrow plus day counters mark the stalk.
- Detection: **fully automatic** vision, accepting occasional mistakes.

**My calls (the owner can override):**
- "Show me" timeout 30 min, on the Node-RED dashboard.
- Live capped by a viewer limit rather than lower quality.
- Gatekeeper fails closed on any doubt about door state.
- Capture every 5 min during the 60% plateau only; discard door-open, after-door and misting frames.
- Film 20–30 s with a zoomed inset; published to a website gallery plus the report email; served from the Pi.
- Frames kept indefinitely on the Pi (~2–3 GB/year).
- Vision: one run/day via the Pi's Claude Code CLI, with `ANTHROPIC_API_KEY` unset.
- Missing/invalid `CROP` → private; full frame only with explicit `CROP=none`.
- Gallery rendered in the browser from a JSON index served by the Pi; the Pi never pushes to the website repo.
- A flowering spanning a camera re-aim is split into separate films.
- Social preview is a fixed non-camera image.

## 9. Open questions for the owner

Answered 2026-11-24:
1. **Website page:** built by Pi-Claude on a separate branch; the owner approves before it goes live. Note it in `website/HANDOFF.md` so the Mac-side Claude doesn't collide.
2. **Vision cost:** "it's Claude", meaning run through the Pi's Claude Code CLI on the owner's plan, no API billing (see §5, §7.2).

**Consent gate:** on 2026-11-23 the owner instructed that the camera must never be made public or added to the website without explicit consent. Owner approval of this document is that consent for exactly what it describes; nothing camera-related is deployed publicly before it.

## 10. Left to the builder

- Implementation language and process layout of the gatekeeper (extend `conditions-server.py` vs a separate service behind it), streaming format (MJPEG vs other), crop technique, frame rates, viewer cap, cooldown and staleness thresholds (all within §6.2's rules).
- Door/"show me" transport details (MQTT topics, heartbeat interval).
- Exact capture scheduler, storage layout, vision prompt and schema, registry format, film encoding and overlay rendering.
- Tests: at minimum, automated tests of the privacy rules (door open → no new frames; stale signal → private; crop applied on every route) and a manual end-to-end check with the doors actually opened.
