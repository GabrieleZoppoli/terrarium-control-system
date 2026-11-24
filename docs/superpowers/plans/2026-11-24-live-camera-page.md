# Live Camera Page (Part A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put the terrarium camera on highlandcloudforest.com as a 30-second live view, then still photos, with a privacy gatekeeper that goes private the moment a door opens or anything is uncertain.

**Architecture:** A new Python service, `camgate` (127.0.0.1:8788), is the only thing that serves camera pixels publicly. It reads ustreamer on loopback, crops every frame using the `CROP` from `/etc/surveil/surveil.conf`, and decides public or private from MQTT door and "show me" signals published by Node-RED straight from the raw serial door events. The existing public server (`conditions-server.py`, behind Tailscale Funnel) forwards `/cam/*` to camgate. The website gets a bilingual webcam page built on a branch.

**Tech Stack:** Python 3.11 stdlib (`http.server`, `threading`, `unittest`), Pillow 9.4 (installed), paho-mqtt 2.1 (installed), Mosquitto on localhost:1883 (running), Node-RED 3.1.3 (Admin API on :1880, no admin auth), Hugo 0.157 extended (installed).

**Spec:** `docs/superpowers/specs/2026-11-24-live-camera-and-flowering-timelapse-design.md` (approved 2026-11-24). Part B (time-lapse) gets its own plan after this one ships.

## Global Constraints

- Public pixels: **every** image/stream byte leaving camgate is cropped with the `CROP` value from `/etc/surveil/surveil.conf` (currently `1344:1080:0:0`). Missing, empty or unparseable `CROP` means **private**; only an explicit `CROP=none` allows the full frame.
- Fail closed: public only with a fresh positive "doors closed" signal. Any doubt (no message yet, stale, serial link stale, MQTT disconnected) means private.
- Door cut: within about 1 s of a door opening, no new live frames are sent and the still is the last frame captured **before** the opening (blurred while private).
- "Show me": overrides the door rule only while on; auto-off after **30 min** (`1800 s`), enforced by Node-RED **and** camgate (expiry timestamp).
- Live: session **30 s**; global live viewer cap; per-visitor cooldown; a single ustreamer read fanned out to all viewers; no live work when nobody watches.
- Still photo refresh: every few minutes (`180 s`).
- No audio, ever. The raw ustreamer stream (`127.0.0.1:8080`) stays loopback-only. No new Funnel routes or ports.
- Node-RED changes are **additive only**: new nodes and new wires; existing nodes' code and existing wires are untouched.
- Never commit camera frames to git. The website work happens on branch `feature/webcam-page`; the owner approves before merge.
- Tests use stdlib `unittest` (pytest is not installed): `cd scripts && python3 -m unittest discover -s camgate/tests -v`.

## Review Focus

1. **Door opens while someone is watching live.** Expect the stream to end within ~1 s with no frame captured after the opening sent. Pinned in Task 5 (`test_stream_stops_when_private`) and Task 6 (`test_live_stream_ends_on_door_open`).
2. **camgate starts while the doors are open, or before any MQTT message arrives.** Expect private. Pinned in Task 2 (`test_no_signal_yet_is_private`) and Task 6 (`test_startup_without_signals_serves_placeholder`).
3. **Camera unplugged or ustreamer down** (the camera re-enumerated on 2026-11-23). Expect the still route to keep serving the last good image or the placeholder, live to return 503, and nothing to hang. Pinned in Task 4 (`test_source_failure_keeps_last_still`) and Task 5 (`test_source_failure_ends_sessions`).
4. **A tab left open, or a script hammering "watch live".** Expect cooldown 429s and a viewer cap, so threads and bandwidth can't be exhausted. Pinned in Task 5 (`test_cooldown_blocks_immediate_restart`, `test_cap_rejects_extra_viewer`).
5. **A stale "show me"** (Node-RED restarted with a retained `on`, or `until` in the past). Expect it to be treated as off. Pinned in Task 2 (`test_expired_showme_is_ignored`).

---

## File Structure

```
scripts/camgate/                    # new package (repo: terrarium-paper)
  __init__.py
  __main__.py                       # entry: wires everything, starts server
  config.py                         # constants + load_crop()
  frames.py                         # crop_jpeg, blur_jpeg, placeholder_jpeg, iter_mjpeg_frames
  policy.py                         # DoorSignal, ShowMe, Decision, decide()
  signals.py                        # SignalStore + MQTT payload parsing + paho bridge
  camera.py                         # SnapshotSource, StreamSource, StillKeeper
  live.py                           # LiveHub (fan-out, cap, cooldown, sessions)
  server.py                         # HTTP routes on 127.0.0.1:8788
  tests/test_*.py                   # one file per module above
scripts/camgate/deploy/
  terrarium-camgate.service         # systemd unit
  install.sh                        # copies package to /opt/terrarium-camgate, installs unit
/home/pi/snap-renderer/conditions-server.py   # modify: /cam/* reverse proxy (not in git, back up first)
Node-RED (tab 0ff01249801c9e0e)     # add: Camera Door Publisher, 1 s tick, Show-me switch + timer, 2 mqtt out
website/layouts/shortcodes/webcam.html        # new
website/i18n/en.yaml, it.yaml                 # add webcam strings
website/content/highland/webcam/_index.md, _index.it.md   # replace placeholder
website/HANDOFF.md                            # note: Pi-Claude owns the webcam page
```

**MQTT contract (Task 3 consumes; Task 8 produces), both retained, QoS 1:**
- `terrarium/camera/doors` → `{"open": bool|null, "left": 0|1|null, "right": 0|1|null, "serial_age_s": number, "ts": epoch_s}`. `null` means unknown.
- `terrarium/camera/showme` → `{"on": bool, "until": epoch_s|null, "ts": epoch_s}`

**Public HTTP contract (camgate; Task 6 produces, Task 9 consumes), all with `Access-Control-Allow-Origin: *`:**
- `GET /cam/status.json` → `{"public": bool, "reason": str, "showme": bool, "live_slots_free": int, "still_taken_at": iso8601|null}`, `Cache-Control: no-store`
- `GET /cam/still.jpg` → cropped JPEG (blurred if private; placeholder if none), `Cache-Control: no-store`
- `GET /cam/live.mjpg` → `multipart/x-mixed-replace; boundary=frame`, ≤ 30 s; `403` private, `429` busy/cooldown (JSON body `{"error":"busy"|"cooldown","retry_after_s":int}`), `503` camera unavailable

---

### Task 1: Crop config and frame operations

**Files:**
- Create: `scripts/camgate/__init__.py`, `scripts/camgate/config.py`, `scripts/camgate/frames.py`
- Test: `scripts/camgate/tests/__init__.py`, `scripts/camgate/tests/test_config.py`, `scripts/camgate/tests/test_frames.py`

**Interfaces:**
- Produces: `Crop = NamedTuple(w:int, h:int, x:int, y:int)`; `NO_CROP` sentinel; `load_crop(path:str) -> Crop | NO_CROP | None` (None = invalid/missing → private). Constants in `config.py`: `PORT=8788`, `SURVEIL_CONF="/etc/surveil/surveil.conf"`, `USTREAMER_SNAPSHOT="http://127.0.0.1:8080/snapshot"`, `USTREAMER_STREAM="http://127.0.0.1:8080/stream"`, `MQTT_HOST="localhost"`, `MQTT_PORT=1883`, `TOPIC_DOORS="terrarium/camera/doors"`, `TOPIC_SHOWME="terrarium/camera/showme"`, `DOOR_STALE_S=3.0`, `SERIAL_STALE_S=90.0`, `SHOWME_MAX_S=1800`, `LIVE_SESSION_S=30`, `LIVE_FPS=3`, `LIVE_MAX_VIEWERS=3`, `LIVE_COOLDOWN_S=60`, `STILL_REFRESH_S=180`, `JPEG_QUALITY=85`, `BLUR_RADIUS=24`.
- Produces: `crop_jpeg(jpeg:bytes, crop) -> bytes`, `blur_jpeg(jpeg:bytes) -> bytes`, `placeholder_jpeg(w:int=1344, h:int=1080) -> bytes`, `iter_mjpeg_frames(stream: BinaryIO) -> Iterator[bytes]`.

- [ ] **Step 1: Write failing tests**

```python
# test_config.py — write the conf to a tempfile per case
def test_valid_crop(self):      self.assertEqual(load_crop(conf("CROP=1344:1080:0:0")), Crop(1344,1080,0,0))
def test_missing_crop_is_none(self):  self.assertIsNone(load_crop(conf("AUDIO=off")))
def test_garbage_crop_is_none(self):  self.assertIsNone(load_crop(conf("CROP=13x4:abc")))
def test_empty_crop_is_none(self):    self.assertIsNone(load_crop(conf("CROP=")))
def test_explicit_none(self):         self.assertIs(load_crop(conf("CROP=none")), NO_CROP)
def test_unreadable_file_is_none(self): self.assertIsNone(load_crop("/nonexistent/surveil.conf"))
def test_commented_crop_ignored(self):  self.assertIsNone(load_crop(conf("# CROP=1344:1080:0:0")))

# test_frames.py — build a 1920x1080 JPEG with Pillow whose right 576 px are pure red
def test_crop_dimensions_and_removes_right_side(self):
    out = Image.open(io.BytesIO(crop_jpeg(make_frame(), Crop(1344,1080,0,0))))
    self.assertEqual(out.size, (1344,1080)); self.assertLess(out.getpixel((1340,540))[0], 100)  # no red left
def test_no_crop_keeps_full_frame(self): self.assertEqual(Image.open(io.BytesIO(crop_jpeg(make_frame(), NO_CROP))).size, (1920,1080))
def test_crop_none_raises(self): self.assertRaises(ValueError, crop_jpeg, make_frame(), None)
def test_blur_keeps_size(self): ...size equal, and pixel variance much lower than input
def test_placeholder_is_jpeg(self): self.assertEqual(Image.open(io.BytesIO(placeholder_jpeg())).size, (1344,1080))
def test_iter_mjpeg_frames_splits_parts(self):
    # canned ustreamer-style body: b"--boundarydonotcross\r\nContent-Type: image/jpeg\r\nContent-Length: N\r\n\r\n<jpeg>\r\n" x3
    self.assertEqual(list(iter_mjpeg_frames(io.BytesIO(body))), [j1, j2, j3])
def test_iter_mjpeg_frames_stops_on_truncated_part(self): ...truncated last part is not yielded
```

- [ ] **Step 2: Run and confirm failures.** `cd scripts && python3 -m unittest discover -s camgate/tests -v`. Expected: ImportError / FAIL.
- [ ] **Step 3: Implement `config.py` and `frames.py`.** `load_crop` parses `KEY=VALUE` lines, ignoring comments; any exception → `None`. `crop_jpeg` uses Pillow `Image.crop((x,y,x+w,y+h))` + `save(format="JPEG", quality=JPEG_QUALITY)`, and raises `ValueError` for `None` (callers must never get pixels without a valid crop decision). `iter_mjpeg_frames` reads part headers and uses `Content-Length` (ustreamer sends it).
- [ ] **Step 4: Run tests.** Expected: all PASS.
- [ ] **Step 5: Commit.** `git add scripts/camgate && git commit -m "camgate: crop config and frame ops"`

### Task 2: Privacy policy

**Files:**
- Create: `scripts/camgate/policy.py`
- Test: `scripts/camgate/tests/test_policy.py`

**Interfaces:**
- Consumes: constants from `config.py`.
- Produces: `DoorSignal(open: bool|None, serial_age_s: float, ts: float)`, `ShowMe(on: bool, until: float|None)`, `Decision(public: bool, reason: str)`, `decide(now: float, doors: DoorSignal|None, showme: ShowMe|None, crop) -> Decision`. Reasons, exactly: `"ok"`, `"showme"`, `"doors_open"`, `"door_state_unknown"`, `"door_signal_stale"`, `"serial_stale"`, `"crop_invalid"`. Precedence: `crop_invalid` first (even "show me" can't publish an uncropped frame); then show-me if active (`on` and `until > now` and `until - now <= SHOWME_MAX_S`); then door checks in the order missing/unknown → stale (`now - ts > DOOR_STALE_S`) → serial stale (`serial_age_s > SERIAL_STALE_S`) → open.

- [ ] **Step 1: Write failing tests** (all with `now=1000.0`, valid crop unless stated):

```python
test_closed_fresh_is_public:        decide(1000, DoorSignal(False, 5, 999.5), None, CROP) == Decision(True, "ok")
test_open_is_private:               reason "doors_open"
test_no_signal_yet_is_private:      decide(1000, None, None, CROP) == Decision(False, "door_state_unknown")
test_unknown_door_is_private:       DoorSignal(None, 5, 999.5) -> "door_state_unknown"
test_stale_signal_is_private:       DoorSignal(False, 5, 996.9) -> "door_signal_stale"
test_serial_stale_is_private:       DoorSignal(False, 91, 999.5) -> "serial_stale"
test_showme_overrides_open_door:    DoorSignal(True,5,999.5), ShowMe(True, 1600) -> Decision(True, "showme")
test_showme_overrides_stale_signal: None doors, ShowMe(True,1600) -> Decision(True,"showme")
test_expired_showme_is_ignored:     ShowMe(True, 999) with open door -> "doors_open"
test_showme_too_long_is_ignored:    ShowMe(True, 1000+1801) with open door -> "doors_open"
test_invalid_crop_beats_everything: crop=None with ShowMe active -> Decision(False, "crop_invalid")
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement `decide()`** as specified in Interfaces.
- [ ] **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** `camgate: fail-closed privacy policy`.

### Task 3: Signal store and MQTT bridge

**Files:**
- Create: `scripts/camgate/signals.py`
- Test: `scripts/camgate/tests/test_signals.py`

**Interfaces:**
- Consumes: `DoorSignal`, `ShowMe`; MQTT contract above.
- Produces: `parse_doors(payload: bytes) -> DoorSignal|None`, `parse_showme(payload: bytes) -> ShowMe|None` (malformed → `None`); `class SignalStore` with `set_doors(sig|None)`, `set_showme(sm|None)`, `set_connected(bool)`, `snapshot() -> tuple[DoorSignal|None, ShowMe|None]` (thread-safe; returns `(None, None)` for doors while disconnected); `start_mqtt(store: SignalStore) -> paho.mqtt.client.Client` (connects, subscribes to both topics QoS 1, `loop_start()`, sets connected False on disconnect).

- [ ] **Step 1: Write failing tests**

```python
test_parse_doors_closed: parse_doors(b'{"open":false,"left":0,"right":0,"serial_age_s":4,"ts":999.5}') == DoorSignal(False,4,999.5)
test_parse_doors_unknown: parse_doors(b'{"open":null,"left":null,"right":0,"serial_age_s":4,"ts":999.5}').open is None
test_parse_doors_malformed: parse_doors(b'not json') is None; parse_doors(b'{"open":"no"}') is None
test_parse_showme: parse_showme(b'{"on":true,"until":1600,"ts":1000}') == ShowMe(True,1600)
test_store_disconnected_hides_doors: store.set_doors(sig); store.set_connected(False); store.snapshot()[0] is None
test_store_malformed_message_clears_doors: on_message with garbage sets doors None   # fail closed
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement.** paho 2.x: `mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="camgate")`. `on_message` routes by topic; a malformed doors payload sets doors to `None`. `on_disconnect` → `set_connected(False)`; `on_connect` → `set_connected(True)` and re-subscribe.
- [ ] **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** `camgate: MQTT signal store`.

### Task 4: Camera sources and still keeper

**Files:**
- Create: `scripts/camgate/camera.py`
- Test: `scripts/camgate/tests/test_camera.py`

**Interfaces:**
- Consumes: `crop_jpeg`, `blur_jpeg`, `placeholder_jpeg`, `iter_mjpeg_frames`, `load_crop`, `decide`, `SignalStore`.
- Produces: `class SnapshotSource: fetch() -> bytes` (raises `CameraError` on failure; 5 s timeout); `class StreamSource: frames() -> Iterator[bytes]` (opens `USTREAMER_STREAM`, raises `CameraError`); `class StillKeeper(source, decide_fn: Callable[[float], Decision], crop_fn: Callable[[], crop], clock=time.time)` with `tick() -> None` (captures a cropped still when public and `STILL_REFRESH_S` has elapsed) and `current() -> tuple[bytes, float|None]` (cropped still if public; blurred last still if private; placeholder if none; plus the capture time). The policy is re-checked **after** the fetch returns, and the frame is discarded if it's no longer public.

- [ ] **Step 1: Write failing tests** (fake source returning a canned 1920×1080 JPEG; fake clock; `decide_fn` toggled by the test):

```python
test_captures_when_public_and_due:      tick at t=0 then current() size (1344,1080), taken_at == 0
test_no_capture_when_private:           decide private -> tick -> current() is placeholder, taken_at None
test_refresh_interval:                  tick at t=0 and t=100 -> source called once; t=181 -> twice
test_private_serves_blurred_last_still: capture public at t=0, then private -> current() bytes != stored still, size same, taken_at == 0
test_frame_discarded_if_door_opened_during_fetch: decide_fn returns public before fetch, private after -> still not updated
test_source_failure_keeps_last_still:   source raises CameraError after a good capture -> current() still the old still, no exception
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement.** `StillKeeper` holds a lock; the blurred version is computed once per stored still and cached.
- [ ] **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** `camgate: camera sources and still keeper`.

### Task 5: Live hub

**Files:**
- Create: `scripts/camgate/live.py`
- Test: `scripts/camgate/tests/test_live.py`

**Interfaces:**
- Consumes: `StreamSource`-like object (`frames()`), `crop_jpeg`, `crop_fn`, `decide_fn`, constants.
- Produces: `class LiveHub(source, decide_fn, crop_fn, clock=time.time)`:
  - `open_session(visitor: str) -> Session`, raising `Busy(retry_after_s)`, `Cooldown(retry_after_s)` or `Private()`.
  - `Session.frames() -> Iterator[bytes]` yields cropped frames at ≤ `LIVE_FPS`. It ends at `LIVE_SESSION_S`, when the decision turns private (checked per frame, before yielding), or on source failure (raises `CameraError` at the start if no frame arrives within 5 s).
  - `Session.close()`.
  - `slots_free() -> int`.
  - A single background reader thread starts with the first session and stops when the last one closes. Cooldown starts when a visitor's session ends: `LIVE_COOLDOWN_S`, keyed by `visitor`.

- [ ] **Step 1: Write failing tests** (fake source yielding numbered frames forever; fake clock you advance):

```python
test_session_ends_after_30s:          frames stop once clock passes 30 s
test_stream_stops_when_private:       flip decide_fn to private -> the next frames() step ends; no further frame yielded
test_frames_are_cropped:              every yielded frame decodes to (1344,1080)
test_cap_rejects_extra_viewer:        3 sessions open -> 4th raises Busy
test_cooldown_blocks_immediate_restart: same visitor reopens right after close -> Cooldown(retry_after_s≈60)
test_private_rejects_open:            decide private -> open_session raises Private
test_single_reader_for_many_viewers:  3 sessions -> source.frames() called once
test_reader_stops_when_idle:          after all sessions close, reader thread exits (join within 2 s)
test_source_failure_ends_sessions:    source raises CameraError -> frames() ends, slots freed
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement.** The reader keeps only the latest frame (condition variable plus frame sequence number); each session waits for a new sequence number, then crops it. Cropping happens per session at ≤ 3 fps. To keep CPU low, the reader may crop once per new frame and share the result.
- [ ] **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** `camgate: live hub with cap, cooldown, fail-closed sessions`.

### Task 6: HTTP server and entry point

**Files:**
- Create: `scripts/camgate/server.py`, `scripts/camgate/__main__.py`
- Test: `scripts/camgate/tests/test_server.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `make_server(keeper: StillKeeper, hub: LiveHub, status_fn: Callable[[], dict], host="127.0.0.1", port=PORT) -> ThreadingHTTPServer`, with routes exactly as in the Public HTTP contract.
  - Visitor key: first address in `X-Forwarded-For`, else `"anon"`.
  - `HEAD` returns headers only.
  - Unknown paths return 404.
- `__main__.py` builds `SignalStore` plus `start_mqtt`. It defines `decide_fn = lambda now: decide(now, *store.snapshot(), load_crop(SURVEIL_CONF))`, re-reading the conf at most every 10 s so a re-aim needs no restart. The same cached value is passed as `crop_fn` to `StillKeeper` and `LiveHub`. It runs `keeper.tick()` every 5 s in a thread, then serves. Environment overrides (for test instances only): `CAMGATE_SURVEIL_CONF` (default `SURVEIL_CONF`), `CAMGATE_PORT` (default `PORT`), `CAMGATE_MAX_VIEWERS` (default `LIVE_MAX_VIEWERS`).

- [ ] **Step 1: Write failing tests** (in-process server on port 0, fakes from Tasks 4–5, `http.client`):

```python
test_status_json_shape:                       keys exactly {"public","reason","showme","live_slots_free","still_taken_at"}, CORS header present
test_still_is_cropped:                         GET /cam/still.jpg -> 200 image/jpeg, size (1344,1080), Cache-Control no-store
test_startup_without_signals_serves_placeholder: no signals -> still is placeholder, status public False reason "door_state_unknown"
test_live_private_is_403
test_live_busy_is_429_with_retry:              JSON {"error":"busy","retry_after_s":int}
test_live_stream_ends_on_door_open:            open stream, read 1 part, flip private -> stream closes within 1.5 s
test_every_route_is_cropped:                   for /cam/still.jpg and each live part: decoded size == crop size
test_unknown_path_404
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement.** Live response: write `--frame\r\nContent-Type: image/jpeg\r\nContent-Length: N\r\n\r\n<jpeg>\r\n` per frame. A broken pipe closes the session.
- [ ] **Step 4: Run the full suite.** `python3 -m unittest discover -s camgate/tests -v`. Expected: all PASS.
- [ ] **Step 5: Commit** `camgate: HTTP server and entry point`.

### Task 7: Deploy camgate and the /cam proxy

**Files:**
- Create: `scripts/camgate/deploy/terrarium-camgate.service`, `scripts/camgate/deploy/install.sh`
- Modify: `/home/pi/snap-renderer/conditions-server.py` (back up to `conditions-server.py.bak_<stamp>` first; not in git)

**Interfaces:**
- Unit: `User=pi`, `ExecStart=/usr/bin/python3 -m camgate`, `WorkingDirectory=/opt/terrarium-camgate`, `After=mosquitto.service terrarium-cam.service`, `Restart=always`, `RestartSec=3`, `Nice=10`, `NoNewPrivileges=true`, `ProtectSystem=strict`, `ProtectHome=read-only`, `PrivateTmp=true`.
- `install.sh`: copies `scripts/camgate` (no tests) to `/opt/terrarium-camgate/camgate`, installs the unit, `daemon-reload`, `enable --now`. It is idempotent.
- `conditions-server.py`: paths starting with `/cam/` are forwarded to `http://127.0.0.1:8788` with method, path and `X-Forwarded-For` preserved. Status, headers and body are streamed back in chunks, so live MJPEG flows. All existing routes are unchanged.

- [ ] **Step 1: Run `install.sh`; verify.** `systemctl is-active terrarium-camgate` gives `active`; `ss -ltn | grep 8788` shows `127.0.0.1:8788` only.
- [ ] **Step 2: Local checks.** `curl -s 127.0.0.1:8788/cam/status.json` is valid JSON. With no Node-RED publisher yet, expect `"public":false,"reason":"door_state_unknown"`. `curl -s 127.0.0.1:8788/cam/still.jpg | python3 -c "import sys,io;from PIL import Image;print(Image.open(io.BytesIO(sys.stdin.buffer.read())).size)"` gives `(1344, 1080)`.
- [ ] **Step 3: Patch `conditions-server.py`, `sudo systemctl restart conditions-server`.** Verify `/api/conditions.json` still returns 200 (regression), and `curl -s https://rei1.tail7cc014.ts.net/cam/status.json` gives the same JSON as locally.
- [ ] **Step 4: Check Funnel's client IP header.** Temporarily log `X-Forwarded-For` in camgate (journal) for one public request, then confirm it holds a real client address. If it doesn't, the visitor key falls back to `"anon"` (global cooldown). Note the result in the commit message, then remove the debug log.
- [ ] **Step 5: Commit** `camgate: systemd deploy + /cam proxy` (the repo holds a patch copy of the `conditions-server.py` change at `scripts/camgate/deploy/conditions-server-cam-proxy.patch`).

### Task 8: Node-RED door publisher and "show me" switch

**Files:**
- Modify: Node-RED flows (tab `0ff01249801c9e0e`) via the Admin API. Back up first: `cp ~/.node-red/flows.json ~/.node-red/flows_backup_$(date +%Y%m%d-%H%M%S)_before_camgate.json`.

**Interfaces:**
- Produces: the MQTT contract (both topics retained, QoS 1, existing broker config `280303304ebeda9f`).
- New nodes:
  - **"Camera Door Publisher"** (function), with **new wires added from `serial_parser_001` outputs 0, 1 and 2**. Output 0 is the heartbeat `H,…`; outputs 1 and 2 carry `door_left`/`door_right` with payload 0|1 (msg.topic tells which).
    - It keeps `left`, `right` (initially `null`) and `last_serial_ts` in **node context**, persisted, so state survives restarts.
    - It publishes immediately on every door message, and on every tick from a new **1 s inject** wired into the same node (msg.topic `tick`).
    - Payload: `{"open": left===null||right===null ? null : !!(left||right), "left", "right", "serial_age_s": (now - last_serial_ts), "ts": now}`. Times are epoch seconds.
  - **"Camera show-me"** (`ui_switch` in the existing dashboard group used for manual overrides) → function "Show-me timer". Turning on publishes `{"on":true,"until":now+1800,"ts":now}` and arms a 1800 s timer. The timer or turning off publishes `{"on":false,"until":null,"ts":now}` and resets the switch. The remaining minutes are shown in a `ui_text` next to the switch.
- Existing nodes' `func` and existing wires are unchanged; only new wires are added from `serial_parser_001` outputs 0–2.

- [ ] **Step 1: Back up flows** (command above). Verify the backup file exists and its size matches.
- [ ] **Step 2: Deploy.** `GET http://127.0.0.1:1880/flows` gives the full config. Append the new nodes, add the three new wire targets to `serial_parser_001.wires[0..2]`, then `POST /flows` with header `Node-RED-Deployment-Type: nodes`. Verify with a diff of before/after JSON: only new node ids, plus appended targets in `serial_parser_001.wires`.
- [ ] **Step 3: Verify the topics.** `mosquitto_sub -h localhost -t 'terrarium/camera/#' -v -C 3` shows a doors message every ~1 s, with `serial_age_s` < 90. `open` is `null` until each door has reported once.
- [ ] **Step 4: Owner step.** Ask the owner to open and close each door once. Expect `open` true then false, `left`/`right` 0|1, and camgate `status.json` turning `public:true` after both doors are closed. Note that this arming step is needed once after deploy.
- [ ] **Step 5: Verify show-me.** Toggle on from the dashboard; status shows `"showme":true`. Toggle off; status is back to door logic.
- [ ] **Step 6: Commit** the exported new nodes as `scripts/camgate/deploy/node-red-camera-nodes.json` (for re-import) with message `node-red: camera door publisher + show-me`.

### Task 9: Website webcam page (branch `feature/webcam-page`)

**Files:**
- Create: `website/layouts/shortcodes/webcam.html` (markup + scoped CSS + JS, following `layouts/shortcodes/highland-live.html`)
- Modify: `website/i18n/en.yaml`, `website/i18n/it.yaml`, `website/content/highland/webcam/_index.md`, `website/content/highland/webcam/_index.it.md`, `website/HANDOFF.md`

**Interfaces:**
- Consumes: the public HTTP contract at `{{ site.Params.liveConditionsURL | replace "/api/conditions.json" "" }}` + `/cam/...`, and `/api/conditions.json` for the readings chips.
- Page behaviour (matches the approved mockup):
  - **On load:** fetch status. If `public`, show `<img src=/cam/live.mjpg>` with a "● LIVE · 0:NN left" badge, a red progress bar and readings chips: °C (1 decimal), % RH (integer), lights on/off, plus "🌙 night, lights off" when `lights` is false.
  - **At 30 s, or when the stream ends:** swap to `/cam/still.jpg?t=<now>`, with an "updated N min ago" badge from `still_taken_at` and a "▶ Watch live again" button. Refresh the still every 180 s.
  - **On 429:** show the still plus a "live is busy" note, with the button disabled for `retry_after_s`.
  - **Private:** show the blurred still plus the card "🌿 Gardener at work: the camera is paused while the terrarium is being tended. Back in a moment." Re-check status every 10 s.
  - Social preview: front-matter `images:` set to an existing site image (not a camera frame).
- i18n keys (EN/IT): `webcamLive`, `webcamLeft`, `webcamUpdatedAgo`, `webcamWatchAgain`, `webcamBusy`, `webcamPrivateTitle`, `webcamPrivateBody`, `webcamNight`, `webcamLightsOn`, `webcamLightsOff`.

- [ ] **Step 1:** `git checkout -b feature/webcam-page`.
- [ ] **Step 2: Write shortcode, i18n strings, content.** Replace the placeholder text and the `<!-- WEBCAM_EMBED_HERE -->` marker with `{{< webcam >}}` plus one intro paragraph per language.
- [ ] **Step 3: Build.** `cd website && hugo --gc --minify -d /tmp/claude-1000/webcam-build`. Expected: exit 0, no template errors, `highland/webcam/index.html` contains the shortcode output.
- [ ] **Step 4: Preview for the owner.** `hugo server --bind 100.75.138.32 --baseURL http://100.75.138.32:1313/` (tailnet-only). Walk through all states: live, then still after 30 s; busy (set `LIVE_MAX_VIEWERS=0` temporarily via env override or a test instance); private (open a door); night.
- [ ] **Step 5: HANDOFF.md.** Add a line saying the webcam section is owned by Pi-Claude on `feature/webcam-page`, so the Mac-side Claude doesn't edit it.
- [ ] **Step 6: Commit on the branch** `website: live webcam page`. **Do not merge or push to `master`**: the owner approves the preview first (deploy happens on push to master).

### Task 10: End-to-end privacy acceptance (with the owner)

**Files:** none (verification only; record results in `docs/superpowers/plans/2026-11-24-live-camera-page.md` under a new "Acceptance" heading)

- [ ] **Step 1: Door cut.** With a public live stream open through `https://rei1.tail7cc014.ts.net/cam/live.mjpg` (on a phone off Wi-Fi), the owner opens a door. Expect the stream to end within ~1 s, and the still to become the blurred pre-opening frame.
- [ ] **Step 2: Stale signal.** `mosquitto_pub -r -t terrarium/camera/doors -m '{"open":false,"left":0,"right":0,"serial_age_s":1,"ts":1}'`, with no publisher tick in between (disable the 1 s inject for 10 s). Expect `reason` to be `door_signal_stale` (re-enable the inject afterwards).
- [ ] **Step 3: Crop guard.** Temporarily set `CROP=bogus` in a **copy** of the conf, pointed to via `CAMGATE_SURVEIL_CONF`, on a test instance on port 8789. Expect `crop_invalid` and no camera pixels served (placeholder only).
- [ ] **Step 4: Load.** Open 4 live viewers. Expect the 4th to get 429. Check the system load: `uptime` 1-min load must not rise by more than ~1.0, and Node-RED `/flows` must stay responsive.
- [ ] **Step 5: Owner approval.** Show the preview; on approval, merge `feature/webcam-page` to `master` and push (GitHub Pages deploys).
