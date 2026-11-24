# Flowering Time-lapse (Part B1: capture, archive, vision check) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Archive lossless, privacy-cropped terrarium photos every 10 minutes while the lights are on, and run a daily Claude vision check that keeps a registry of Heliamphora flowers/buds up to date, with the owner confirming doubtful calls through the 07:00 report email.

**Architecture:** A cron job (`timelapse.capture`) asks camgate's new loopback-only gate endpoint whether the doors have been closed long enough, grabs the camera's own JPEG from ustreamer, and crops and rotates it **losslessly** with `jpegtran`, using the CROP from `/etc/surveil/surveil.conf` snapped inward to the JPEG block grid. A daily job (`timelapse.vision`) picks the sharpest plateau photo and compares close-up crops of today against yesterday for each item in an owner-seeded registry. It calls `claude -p` and updates `registry.json`. The 07:00 report shows the flower status and attaches a numbered-dot image when something needs the owner.

**Tech Stack:** Python 3 stdlib + Pillow + numpy (both installed), `jpegtran` (apt `libjpeg-turbo-progs`), Claude Code CLI `~/.local/bin/claude`, cron (user `pi`), unittest.

**Spec:** `docs/superpowers/specs/2026-11-24-live-camera-and-flowering-timelapse-design.md` §7 (Part B), as amended by owner decisions on 2026-11-24 (listed below). Part B2 (films, website gallery, live overlay dots) is a separate later plan.

**Amendments to the spec (owner, 2026-11-24 conversation — these win over the spec text):**
- Capture every **10 min while the lights are on** (not only the plateau), so leaf/pitcher growth is archived too. The 60 % plateau frames are flagged, and films use them by default to avoid flicker. During the plateau each capture is a **burst of 3** frames, kept for multi-frame work on the owner's GPU workstation.
- Archive = the camera's own JPEG, **losslessly** cropped and rotated (no re-encode). Plain dated folders with a per-day JSON sidecar, easy to `rsync` to the workstation.
- Detection is **not** "no human involvement": the owner's corrections showed single-frame judging is unreliable (pink LEDs make colour useless for age, and stalk joints look like buds). So the registry is **seeded and corrected by the owner**, vision **tracks changes** day to day by **shape, not colour**, low-confidence calls become "?" items shown to the owner in the report, and nothing doubtful is ever public.
- Website overlay (B2) must be **simple**: small dots, labels on hover/tap, hide button, only confirmed/confident items.

**My calls (owner can override):** flowers only for now. The registry has a `kind` field, so `pitcher` can be added later without code changes. Archive cap 40 GB / free-space floor 15 GB, and on hitting either, capture **stops**: nothing is ever deleted automatically. Vision runs daily at 16:30. Corrections are made by telling Pi-Claude, who runs the registry CLI. No email-reply parsing.

## Global Constraints

- Privacy first: an archived frame must never contain pixels outside the CROP region. The lossless crop is the CROP snapped **inward** to the MCU grid; any mismatch → discard the frame.
- Never archive a frame unless camgate's decision reason is exactly `"ok"` (doors closed, fresh signals, valid crop) **and** the last non-ok moment was ≥ `AFTER_PRIVATE_S = 600` s ago. `showme` does **not** count as ok.
- Never archive during misting: skip if `mister` is true or a `mist_event` happened in the last `MIST_QUIET_S = 300` s.
- `/etc/surveil/surveil.conf` CROP is the single source of truth (currently `CROP=1180:1080:164:0`, owner: permanent until they say otherwise). Missing/invalid → no capture. `CROP=none` → no capture either (archive never stores full frames).
- Camera frames and registry data never go into any git repo. Tests use synthetic Pillow-generated JPEGs only.
- Archive root `/var/lib/terrarium-timelapse/` (owner `pi`), not served by any web server, not under the DVR store.
- Vision runs `claude -p` with `ANTHROPIC_API_KEY` **removed from the environment**, at most once per day (plus manual re-runs), timeout 900 s. Failure leaves the registry untouched and is reported.
- The control system comes first: cron jobs run under `nice -n 10` with `flock -n`, and capture takes < 5 s CPU.
- No new network listeners, Funnel routes, or public paths. camgate's new endpoint is **not** under `/cam/`, so the conditions-server proxy (which forwards only `/cam/*`) never exposes it.
- Code style: match `scripts/camgate/` (stdlib, small modules, docstrings, unittest under `<pkg>/tests`, run as `cd scripts && python3 -m unittest discover -s timelapse/tests`).

## Review Focus

1. **CROP changes (camera re-aimed) mid-archive** → each frame's sidecar records the geometry. The vision job compares geometry with the registry and, if it differs, marks every item `needs_owner` instead of guessing positions. Test in Task 7.
2. **Node-RED globals file missing, half-written or stale** (NR down) → capture skips with reason `light_schedule_unknown`, and never crashes. Test in Task 3.
3. **Claude CLI fails** (logged out, usage limit, timeout, prose instead of JSON, JSON with unknown ids) → the registry is unchanged, the status file says `vision_failed: <why>`, and the report shows it. Test in Task 7.
4. **Disk pressure** → over the cap or under the floor, capture stops with `archive_full` and never deletes anything. Test in Task 4.
5. **camgate down or the gate endpoint unreachable** → no capture (`gate_unreachable`). The gate is re-checked **after** the snapshot, and the frame is discarded if the state changed in between. Test in Task 4.

---

### Task 1: camgate archive-gate endpoint (loopback-only)

**Files:**
- Create: `scripts/camgate/archive_gate.py`
- Modify: `scripts/camgate/__main__.py` (tick loop feeds the tracker), `scripts/camgate/server.py` (route)
- Test: `scripts/camgate/tests/test_archive_gate.py`, extend `scripts/camgate/tests/test_server.py`

**Interfaces:**
- Produces: `class ArchiveGate: __init__(self, clock=time.time)`, `observe(self, now: float, decision: Decision) -> None`, `state(self, now: float) -> dict` returning `{"ok": bool, "reason": str, "last_not_ok_at": float, "now": float}`. Route `GET /internal/archive-gate.json` returns `state()`.
- `ok` is True only if the latest observed `decision.reason == "ok"` and the observation is ≤ 3 s old. `last_not_ok_at` starts at construction time (the state before start is unknown).

- [ ] **Step 1: Write failing tests**

```python
def test_starts_not_ok_and_last_not_ok_is_start(self):
    g = ArchiveGate(clock=lambda: 100.0)
    s = g.state(100.0)
    self.assertFalse(s["ok"]); self.assertEqual(s["last_not_ok_at"], 100.0)

def test_ok_after_ok_observation_keeps_last_not_ok(self):
    g = ArchiveGate(clock=lambda: 100.0)
    g.observe(105.0, Decision(True, "ok"))
    s = g.state(105.5)
    self.assertTrue(s["ok"]); self.assertEqual(s["last_not_ok_at"], 100.0)

def test_showme_is_not_ok(self):
    g = ArchiveGate(clock=lambda: 0.0)
    g.observe(10.0, Decision(True, "showme"))
    s = g.state(10.0)
    self.assertFalse(s["ok"]); self.assertEqual(s["last_not_ok_at"], 10.0)

def test_stale_observation_is_not_ok(self):
    g = ArchiveGate(clock=lambda: 0.0)
    g.observe(10.0, Decision(True, "ok"))
    self.assertFalse(g.state(13.5)["ok"])
```

Server test: `GET /internal/archive-gate.json` → 200 JSON with the 4 keys; `GET /cam/internal/archive-gate.json` → 404.

- [ ] **Step 2: Run** `cd scripts && python3 -m unittest camgate.tests.test_archive_gate -v`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement** `ArchiveGate` (lock-protected). In `__main__.tick_loop`, after `keeper.tick()`, call `gate.observe(now, decide_fn(now))`. Pass `gate.state` to `make_server` as `archive_gate_fn` and add the route in `_dispatch`.
- [ ] **Step 4: Run the full camgate suite** `cd scripts && python3 -m unittest discover -s camgate/tests`. Expected: all pass (133 + new).
- [ ] **Step 5: Deploy and verify:** `sudo scripts/camgate/deploy/install.sh`, then `curl -s 127.0.0.1:8788/internal/archive-gate.json` shows `"ok": true` with doors closed, and `curl -s -o /dev/null -w '%{http_code}' https://rei1.tail7cc014.ts.net/internal/archive-gate.json` gives **404**.
- [ ] **Step 6: Commit** `camgate: loopback-only archive gate (doors-closed-long-enough signal for the time-lapse)`.

### Task 2: Lossless crop + rotate (`timelapse.lossless`)

**Files:**
- Create: `scripts/timelapse/__init__.py`, `scripts/timelapse/config.py`, `scripts/timelapse/lossless.py`
- Test: `scripts/timelapse/tests/__init__.py`, `scripts/timelapse/tests/test_lossless.py`

**Interfaces:**
- Consumes: `camgate.config.load_crop(path)` and `Crop(w, h, x, y)` / `NO_CROP` (import from camgate; do not copy).
- Produces: `mcu_size(jpeg: bytes) -> tuple[int, int]` (8×max h-sampling, 8×max v-sampling); `snap_inward(crop: Crop, mcu: tuple[int,int], frame: tuple[int,int]) -> Crop | None` (None if empty or crop is out of frame); `crop_rotate(jpeg: bytes, crop: Crop) -> bytes` (runs `jpegtran -copy none -perfect -crop WxH+X+Y`, then `jpegtran -copy none -perfect -rotate 180`, checks output size == (crop.w, crop.h), raises `LosslessError` otherwise or on non-zero exit). `archive_geometry(crop) -> str` like `"1168x1080+176+0/rot180"`.
- `config.py` holds every constant named in this plan (paths, intervals, thresholds) in one place.

- [ ] **Step 1: Install the tool:** `sudo apt-get install -y libjpeg-turbo-progs` and check that `jpegtran -version` prints libjpeg-turbo.
- [ ] **Step 2: Write failing tests** with a synthetic 1920×1080 JPEG saved by Pillow with `subsampling=1` (4:2:2, like the camera) and a gradient plus marker squares:

```python
def test_mcu_422(self):  self.assertEqual(mcu_size(self.jpeg), (16, 8))
def test_snap_inward_current_crop(self):
    self.assertEqual(snap_inward(Crop(1180,1080,164,0),(16,8),(1920,1080)), Crop(1168,1080,176,0))
def test_snap_never_grows(self):  # every snapped crop lies inside the original
    for c in [Crop(1180,1080,164,0), Crop(1344,1080,0,0), Crop(1001,999,3,5)]:
        s = snap_inward(c,(16,8),(1920,1080))
        self.assertTrue(s.x >= c.x and s.y >= c.y and s.x+s.w <= c.x+c.w and s.y+s.h <= c.y+c.h)
def test_crop_rotate_matches_pillow(self):
    out = crop_rotate(self.jpeg, Crop(1168,1080,176,0))
    ref = Image.open(io.BytesIO(self.jpeg)).crop((176,0,1344,1080)).rotate(180)
    diff = np.abs(np.asarray(Image.open(io.BytesIO(out)), float) - np.asarray(ref, float))
    self.assertEqual(Image.open(io.BytesIO(out)).size, (1168,1080)); self.assertLess(diff.mean(), 1.0)
def test_marker_outside_crop_is_absent(self):  # red square at raw x 100..150 must not survive
def test_misaligned_crop_raises(self):  # crop_rotate(jpeg, Crop(1180,1080,164,0)) raises LosslessError
```

- [ ] **Step 3: Run** `cd scripts && python3 -m unittest timelapse.tests.test_lossless -v`. Expected: FAIL.
- [ ] **Step 4: Implement** using `subprocess.run(..., input=jpeg, capture_output=True, timeout=10)`. Read sampling with `PIL.JpegImagePlugin.get_sampling` and the layers (`im.layer`).
- [ ] **Step 5: Run** the tests. Expected: PASS.
- [ ] **Step 6: Commit** `timelapse: lossless privacy crop + 180° rotate via jpegtran`.

### Task 3: Capture conditions (`timelapse.conditions`)

**Files:**
- Create: `scripts/timelapse/conditions.py`
- Test: `scripts/timelapse/tests/test_conditions.py`

**Interfaces:**
- Produces:
  - `LightWindow(on, off, plateau_start, plateau_end)`, in minutes from local midnight.
  - `light_window(globals_path: str) -> LightWindow | None`, from `payload.photo_light_on`, `payload.photo_light_off`, `payload.photo_midday_up`, `payload.photo_midday_down` in `/home/pi/.node-red/context/global/global.json`. `plateau_start = midday_up + 30`, `plateau_end = midday_down`. Returns None if the file is missing or unparseable, a value is missing or non-numeric, the order is not `on < plateau_start < plateau_end < off`, or the file mtime is > 1 h old.
  - `phase(now_local: datetime, w: LightWindow) -> str` in `{"dark", "lit", "plateau"}`.
  - `gate_check(gate: dict | None, now: float) -> str | None`: None means OK; otherwise a reason (`gate_unreachable`, `gate_<reason>`, `after_private`).
  - `mist_check(conditions: dict | None, last_mist_ts: float | None, now: float) -> str | None`: reasons `conditions_unreachable`, `misting`, `mist_recent`.

- [ ] **Step 1: Write failing tests.**
  - Today's real values give `LightWindow(408, 1182, 737, 883)`.
  - Phases are correct at 06:47 (dark), 06:48 (lit), 12:17 (plateau) and 14:43 (lit).
  - `light_window` returns None for a missing file, garbage, a missing key, a string value, bad ordering, and an mtime older than 2 h. Use `os.utime` for the last one.
  - `gate_check`:
    - `{"ok":True,"last_not_ok_at":0,"now":1000,...}` at now=1000 → None;
    - last_not_ok 500 s ago → `"after_private"`;
    - `ok False reason doors_open` → `"gate_doors_open"`;
    - None → `"gate_unreachable"`.
  - `mist_check`:
    - `{"mister":True}` → `"misting"`;
    - last mist 200 s ago → `"mist_recent"`;
    - 400 s ago → None.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** them as pure functions. The I/O helpers live in `capture.py` (Task 4).
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** `timelapse: light window, gate and misting checks`.

### Task 4: Capture job + storage (`timelapse.capture`, `timelapse.storage`)

**Files:**
- Create: `scripts/timelapse/storage.py`, `scripts/timelapse/capture.py`
- Test: `scripts/timelapse/tests/test_storage.py`, `scripts/timelapse/tests/test_capture.py`

**Interfaces:**
- Consumes: Tasks 2 and 3; `camgate.config.load_crop`.
- Produces:
  - `storage.frame_path(root, ts_local, idx: int | None) -> Path`. Layout: `frames/YYYY/MM/DD/HHMM.jpg`, burst frames `HHMM-0.jpg`… `HHMM-2.jpg`.
  - `storage.write_atomic(path, data)`.
  - `storage.append_sidecar(day_dir, entry: dict)`: `day.json` holds `{"frames":[...]}` and is rewritten atomically.
  - `storage.space_check(root, cap_gb=40, floor_gb=15) -> str | None` (`archive_full` / `disk_low`).
  - `capture.capture_once(now: datetime, deps: Deps) -> dict`. It returns `{"saved":[paths], "skipped": reason|None}`.
    - `Deps` is a NamedTuple of callables: `read_gate`, `read_conditions`, `read_last_mist`, `fetch_snapshot`, `light_window`, `load_crop`, `root`.
    - Order:
      1. space check;
      2. light phase (`dark` → `skipped="dark"`);
      3. crop valid and not NO_CROP;
      4. gate;
      5. mist;
      6. snapshot(s): 3 in plateau, `BURST_GAP_S = 0.3` apart, otherwise 1;
      7. **gate re-check**, where a changed `last_not_ok_at` or not-ok means discard all;
      8. lossless crop each, write, and append the sidecar entry.
    - Sidecar entry: `{"time": ISO local, "files": [...], "phase", "geometry", "sharpness": [float]}`. Sharpness is the variance of a 3×3 Laplacian on a 1/4-scale grayscale, computed with numpy.
  - `capture.main()`: real deps on loopback. Gate `http://127.0.0.1:8788/internal/archive-gate.json`, conditions `http://127.0.0.1:8787/api/conditions.json`, raw snapshot `http://127.0.0.1:8080/snapshot`, last mist = InfluxDB `SELECT last(value) FROM mist_event WHERE time > now() - 10m` on db `highland`. It logs one line per run to `/var/lib/terrarium-timelapse/logs/capture.log` and exits 0.

- [ ] **Step 1: Write failing tests** with fake deps:
  - happy lit path (1 file, sidecar entry, geometry `1168x1080+176+0/rot180`);
  - plateau path (3 files);
  - dark;
  - each gate/mist/crop/space reason;
  - **gate changes between the two checks → nothing written**;
  - `fetch_snapshot` raises → `skipped="camera_error"`, nothing written;
  - `crop_rotate` raises → nothing written;
  - `CROP=none` → `skipped="crop_none"`;
  - a sidecar with 2 runs has 2 entries.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `cd scripts && python3 -m unittest discover -s timelapse/tests`. Expected: PASS.
- [ ] **Step 5: Commit** `timelapse: capture job with privacy gate re-check and lossless archive`.

### Task 5: Registry + owner CLI (`timelapse.registry`)

**Files:**
- Create: `scripts/timelapse/registry.py`, `scripts/timelapse/seed_2026-11-24.json`. The seed holds only coordinates and labels, no pixels.
- Test: `scripts/timelapse/tests/test_registry.py`

**Interfaces:**
- Registry file is `/var/lib/terrarium-timelapse/registry.json`:
  - `{"geometry": str, "items": {id: Item}, "runs": [{"date","status","note"}]}`.
  - Item: `{"id": "f1", "kind": "flower", "label": str, "stalk": str, "state": "bud|opening|open|fading|gone|hidden", "x": int, "y": int, "first_seen": date, "opened_on": date|None, "ended_on": date|None, "confirmed": bool, "needs_owner": bool, "streak": int, "history": [{"date","state","confidence","source"}]}`. `source` is `"vision"` or `"owner"`.
- Produces:
  - `load(path) -> dict` (missing file → empty registry).
  - `save(path, reg)` (atomic).
  - `apply_vision(reg, date: str, result: dict, geometry: str) -> dict`. Rules:
    - geometry differs → set all `needs_owner`, change no states;
    - confidence ≥ `CONFIDENT = 0.8` → update state/position, set `opened_on` on the first `open`, set `ended_on` on `gone`, and `streak += 1`;
    - lower confidence → keep the state, `needs_owner = True`, `streak = 0`;
    - unknown ids → ignored;
    - new candidates → added as `confirmed=False, needs_owner=True` with ids `f<N>`.
  - `is_public(item) -> bool`: `confirmed` or `streak >= 3`, and never when `needs_owner`.
  - CLI `python3 -m timelapse.registry [--path P] list | confirm ID | set ID STATE | move ID X Y | drop ID | add KIND STATE X Y LABEL [--stalk S] | seed FILE`. Owner actions write `source="owner"` and set `confirmed=True, needs_owner=False`.
- Seed (owner-corrected frame of 2026-11-24, archive coordinates, geometry `1168x1080+176+0/rot180`, all `confirmed=true`):
  - f1: closed bud, (740,390), stalk "centre";
  - f2: opening, (695,445), "centre";
  - f3: young flower/bud (state `bud`), (555,405), "centre";
  - f4: open, (985,640), "right";
  - f5: opening, (905,510), "right".
  - Label text "Heliamphora".

- [ ] **Step 1: Write failing tests**, one per rule above, plus:
  - CLI round-trip (`add`, then `set`, then `list` output contains the id and state);
  - `seed` refuses to overwrite a non-empty registry without `--force`.
- [ ] **Step 2: Run.** Expected: FAIL. **Step 3: Implement. Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** `timelapse: flower registry with owner CLI and 2026-11-24 seed`.

### Task 6: Vision inputs + annotation (`timelapse.annotate`, `timelapse.vision` part 1)

**Files:**
- Create: `scripts/timelapse/annotate.py`, `scripts/timelapse/vision.py`
- Test: `scripts/timelapse/tests/test_annotate.py`, `scripts/timelapse/tests/test_vision_inputs.py`

**Interfaces:**
- Produces:
  - `annotate.draw_dots(jpeg: bytes, items: list[dict], show_pending=True) -> bytes`: a small filled circle (radius 9 px, white with a black ring) plus the item number. Pending (`needs_owner`) items get an orange ring and "?". This is the same simple style B2 will use on the website.
  - `vision.pick_best(day_dir) -> Path | None`: plateau frame with max sharpness from `day.json`, else the best lit frame, else None.
  - `vision.build_inputs(today: Path, yesterday: Path | None, reg: dict, workdir: Path) -> list[Path]`. It writes:
    - `overview.jpg`: today at 50 % with numbered dots and a 100 px grid labelled in full-res coordinates;
    - per item, `item-<id>.jpg`: a 400×400 full-res crop centred on the item, today on the left and yesterday on the right, 2× upscaled. Clamp at the edges.
  - `vision.build_prompt(reg, files) -> str`. Fixed text must say:
    - judge state by **shape** (closed and pointed = bud; tepals separating = opening; spread = open; limp or shrivelled = fading; absent = gone; covered = hidden);
    - **colour is unreliable under the pink LEDs**, and pink does not mean old;
    - bends and joints on a stalk are not buds;
    - report confidence 0–1;
    - list new flower candidates only if clearly a Heliamphora flower or bud;
    - answer **only** with JSON `{"items":[{"id","state","confidence","x","y"}],"new":[{"state","confidence","x","y","note"}]}`.
- [ ] **Step 1: Write failing tests:**
  - `draw_dots` output has the same size, and the pixel at a dot centre is white;
  - `pick_best` prefers plateau and handles an empty day;
  - `build_inputs` creates `overview.jpg` + one crop per non-gone item, and an edge item (x=5) does not raise;
  - `build_prompt` contains each id and the word "shape".
- [ ] **Step 2: Run.** Expected: FAIL. **Step 3: Implement. Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** `timelapse: vision inputs (overview + per-item today/yesterday crops) and dot annotation`.

### Task 7: Daily vision run (`timelapse.vision` part 2)

**Files:**
- Modify: `scripts/timelapse/vision.py`
- Test: `scripts/timelapse/tests/test_vision_run.py`

**Interfaces:**
- Produces:
  - `run_claude(prompt: str, workdir: Path, timeout=900) -> str`. It runs `[CLAUDE_BIN, "-p", prompt, "--output-format", "json", "--allowedTools", "Read"]` with `cwd=workdir` and an env copy with `ANTHROPIC_API_KEY` **deleted**, where `CLAUDE_BIN = /home/pi/.local/bin/claude`. It returns the `result` field and raises `VisionError` on a non-zero exit, a timeout, or a missing field.
  - `parse_result(text: str, known_ids: set) -> dict`: extracts the first JSON object (the text may be wrapped in ``` fences), validates types and states, clamps confidence to 0..1, and raises `VisionError` on anything invalid.
  - `daily(date, root, runner=run_claude) -> dict`:
    1. `pick_best` for today, plus yesterday's best;
    2. inputs;
    3. prompt;
    4. runner;
    5. parse;
    6. `apply_vision`;
    7. save the registry;
    8. write `status/vision-YYYY-MM-DD.json` `{"status":"ok"|"vision_failed"|"no_frame", "why", "summary": [lines], "pending": [ids]}`;
    9. if any pending, write `status/checkin-YYYY-MM-DD.jpg` via `draw_dots` on today's best frame.
    
    On any failure the registry file is byte-identical to before.
  - `main()`: `daily(today)`, logging to `logs/vision.log`.
- [ ] **Step 1: Write failing tests** with a fake runner:
  - valid JSON → registry updated and status ok;
  - prose → `vision_failed`, registry bytes unchanged;
  - an unknown id is ignored;
  - runner raises a timeout → `vision_failed`;
  - geometry mismatch → all `needs_owner` and a check-in image written;
  - no frames today → `no_frame`;
  - the env passed to the subprocess lacks `ANTHROPIC_API_KEY` (patch `subprocess.run` and inspect `env`).
- [ ] **Step 2: Run.** Expected: FAIL. **Step 3: Implement. Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** `timelapse: daily Claude vision check updating the registry`.

### Task 8: Install, cron, seed, and the report section

**Files:**
- Create:
  - `scripts/timelapse/deploy/install.sh`. It:
    - checks for `jpegtran`;
    - copies the package to `/opt/terrarium-timelapse/timelapse` plus `camgate/config.py` dependencies. Simplest: also copy `camgate` into `/opt/terrarium-timelapse/` the same way camgate's own installer does;
    - creates `/var/lib/terrarium-timelapse/{frames,status,logs}` owned by `pi`, mode 750;
    - adds the cron lines idempotently, backing up the crontab first.
  - `scripts/timelapse/deploy/terrarium-report-timelapse.patch` (diff against the live `/usr/local/bin/terrarium-report.py`; back it up as `.bak_<ts>` before patching).
- Cron (user `pi`):
  - `*/10 * * * * flock -n /tmp/tl-capture.lock nice -n 10 /usr/bin/python3 -m timelapse.capture` with `cd /opt/terrarium-timelapse`;
  - `30 16 * * * flock -n /tmp/tl-vision.lock nice -n 10 /usr/bin/python3 -m timelapse.vision` with `cd /opt/terrarium-timelapse`.
- Report patch:
  - Add a "Flowers" section to the text and HTML output from the latest `status/vision-*.json` (≤ 36 h old), plus "archive: N frames yesterday, X GB total, skipped: {reason: count}" from yesterday's `day.json` and `capture.log`.
  - If a `checkin-*.jpg` for the latest run exists, switch the message to `multipart/mixed` (alternative part + image attachment) and add the line "Some flowers need you: reply in chat with corrections".
  - With no time-lapse data the report is unchanged. Wrap all time-lapse code in try/except so the report never fails because of it.

- [ ] **Step 1:** Run `install.sh`. Then `python3 -m timelapse.registry seed timelapse/seed_2026-11-24.json`, and `list` shows f1–f5.
- [ ] **Step 2:** Run the capture once by hand while the lights are on and the doors are closed. A frame appears and the sidecar has the geometry. Open the frame yourself (Read tool): the right edge must stop at the white cabinet frame, exactly like the public still. **Never commit or send it anywhere.**
- [ ] **Step 3:** Run the report's dry-run/print mode (check `main()` for the flag; if there is none, call `render_text(make_report(...))` from a Python one-liner). The Flowers section shows "no vision run yet", and nothing else changes.
- [ ] **Step 4:** Next day after 16:30, check that `status/vision-<date>.json` exists with `status: ok`. A manual run is allowed once: `python3 -m timelapse.vision`.
- [ ] **Step 5: Commit** `timelapse: installer, cron and report section`. Update memory `camgate-live-camera-2026-11-24.md` (Part B1 live, paths, CLI), and note in `website/HANDOFF.md` that B2 (gallery + dots) is coming.

## Out of scope (Part B2, separate plan after a few weeks of data)

Film rendering with arrow/counters/inset, the Flowerings gallery JSON served through camgate, the simple dot overlay on the live page and still, exposure locking (the white flower clips; the UVC controls may be fake, as the zoom is), and pitcher tracking.
