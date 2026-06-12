#!/usr/bin/env python3
"""Terrarium automated health check with alerts.

Cron: */5 * * * * /usr/local/bin/terrarium-health.py

Sends alerts via Gmail (primary) and/or CallMeBot WhatsApp (if unbanned):
- Every 6 hours: green status report
- Immediately: on any yellow/red alert (30min cooldown per unique alert)
"""

import asyncio, hashlib, json, os, re, smtplib, subprocess, sys, time
import urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText

# ── Config ──────────────────────────────────────────────────────────────
GMAIL_ADDRESS  = "REDACTED — Gmail sender address"
GMAIL_APP_PASS = "REDACTED — set Gmail app password before deployment"
GMAIL_TO       = "REDACTED — Gmail recipient address"

PHONE = "REDACTED — E.164 phone for WhatsApp alerts"
CALLMEBOT_KEY = "REDACTED — get from callmebot.com"           # Set to "" to disable WhatsApp

STATE_FILE = "/home/pi/.terrarium-health-state.json"
GREEN_INTERVAL = 6 * 3600   # 6 hours
ALERT_COOLDOWN = 1800       # 30 min same alert
POWER_FIX_COOLDOWN = 900    # 15 min between relay auto-fix attempts

# STUCK RELAY false-positive prevention (added 2026-05-11 after two false-positive
# AUTO-FIX events on 2026-05-10 evening + 2026-05-11 morning). Root cause: Tapo
# state poll and Meross power poll are not synchronous, so a single sample
# during a freezer cmd transition or a 1-sample Meross spike could trigger a
# bogus STUCK RELAY and AUTO-FIX cycle on an already-off plug.
STUCK_HYSTERESIS_SAMPLES = 3    # require 3 consecutive cycles (~15 min) of excess >70W before STUCK RED
STUCK_TRANSITION_WINDOW = 120   # seconds after a freezer cmd state change during which STUCK check is suppressed

TAPO_EMAIL = "REDACTED — Tapo account email"
TAPO_PASS  = "REDACTED — Tapo account password"
INFLUX_URL = "http://localhost:8086/query?db=highland"

PLUGS = {"freezer": "192.168.1.196", "lights": "192.168.1.55", "mister": "192.168.1.199"}
CEST = timezone(timedelta(hours=2))

# ── Helpers ─────────────────────────────────────────────────────────────

def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", -1
    except Exception:
        return "", -1


def get_light_slider():
    """Read the lights dimmer slider (0-100) from Node-RED global context.
    Returns None if unavailable. Used by the power cross-check to estimate
    expected lights draw."""
    try:
        with urllib.request.urlopen(
            "http://localhost:1880/context/global/payload.current_dimmer_slider",
            timeout=2) as r:
            js = json.load(r)
        v = js.get("msg") if isinstance(js, dict) else None
        if v is None or v == "(undefined)":
            return None
        return float(v)
    except Exception:
        return None


def influx_query(q):
    url = INFLUX_URL + "&q=" + urllib.parse.quote(q)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def freezer_changed_recently(window_s):
    """Return True if freezer_status had different values within the last `window_s` seconds.

    Used to suppress the STUCK RELAY check during the transition window after a
    freezer ON/OFF command, when Tapo state poll and Meross power can be out of sync
    by 30-90 s (compressor spin-down + meter averaging + Tapo cache).
    """
    res = influx_query(f"SELECT min(value), max(value) FROM freezer_status WHERE time > now() - {window_s}s")
    try:
        vals = res["results"][0]["series"][0]["values"][0]
        # vals = [time, min, max]; transition = min != max
        return vals[1] is not None and vals[2] is not None and vals[1] != vals[2]
    except (KeyError, IndexError, TypeError):
        return False


def ping_device(ip):
    out, _ = run(f"ping -c1 -W2 {ip}")
    m = re.search(r"time=([\d.]+)", out)
    return float(m.group(1)) if m else None


def parse_influx_ts(ts_str):
    """Parse InfluxDB ISO timestamp to epoch seconds."""
    ts_str = ts_str.rstrip("Z")
    if "." in ts_str:
        ts_str = ts_str[:26]  # trim nanoseconds
    return datetime.fromisoformat(ts_str + "+00:00").timestamp()


# ── Data collection ─────────────────────────────────────────────────────

async def get_tapo_states():
    from tapo import ApiClient
    client = ApiClient(TAPO_EMAIL, TAPO_PASS)
    results = {}
    for name, ip in PLUGS.items():
        try:
            dev = await client.p100(ip)
            info = await dev.get_device_info()
            results[name] = {"on": info.device_on, "on_time": getattr(info, "on_time", 0)}
        except Exception as e:
            results[name] = {"on": None, "error": str(e)[:60]}
    return results


def get_sensors():
    # Continuous channels (5-min window — staleness flagged on these).
    # fan_speed (the humidity-PID global) is intentionally NOT queried: it goes
    # stale at night when the lights-off/freezer-latched gate forces outlet+
    # impeller to 0 but the PID's last-computed value stays cached. Per-pin
    # fan_pwm_* is the truth — fetched separately below with RBE handling.
    q = ("SELECT last(value) FROM local_temperature, local_humidity, "
         "target_temperature_computed, target_humidity_computed, "
         "freezer_status, light_status WHERE time > now() - 5m")
    data = influx_query(q)
    if not data or "results" not in data:
        return None
    sensors = {}
    now_epoch = time.time()
    for series in data.get("results", [{}])[0].get("series", []):
        ts_epoch = parse_influx_ts(series["values"][0][0])
        sensors[series["name"]] = {
            "value": series["values"][0][1],
            "age": now_epoch - ts_epoch,
            "rbe": False,
        }

    # Per-pin fan PWMs (RBE — only logged on change, so age is meaningless for
    # staleness. 12-h window catches the common case where freezer state and
    # gate state haven't transitioned recently).
    q2 = ("SELECT last(value) FROM fan_pwm_circulation, fan_pwm_freezer, "
          "fan_pwm_outlet, fan_pwm_impeller WHERE time > now() - 12h")
    data2 = influx_query(q2)
    if data2 and "results" in data2:
        for series in data2["results"][0].get("series", []):
            ts_epoch = parse_influx_ts(series["values"][0][0])
            sensors[series["name"]] = {
                "value": series["values"][0][1],
                "age": now_epoch - ts_epoch,
                "rbe": True,
            }

    # Room feed (DietPi -> main Pi InfluxDB, ~60s cadence). 30d window is
    # deliberate: a 5-min query returns nothing when the feed dies, making the
    # outage invisible (it was, for 9.5 days, 2026-06-01->11). Age drives a
    # dedicated yellow in validate(); the "room" flag exempts these entries
    # from the generic 90/120s staleness loop.
    q3 = ("SELECT last(value) FROM room_temperature, room_humidity "
          "WHERE time > now() - 30d")
    data3 = influx_query(q3)
    if data3 and "results" in data3:
        for series in data3["results"][0].get("series", []):
            ts_epoch = parse_influx_ts(series["values"][0][0])
            sensors[series["name"]] = {
                "value": series["values"][0][1],
                "age": now_epoch - ts_epoch,
                "rbe": False,
                "room": True,
            }

    return sensors if sensors else None


def get_water_level():
    """Read calibrated water level. ESP publishes a raw value (despite the
    'tank_percent' MQTT topic name) that NR remaps to a true display %.

    Two-point calibration verified 2026-05-23 afternoon
    (memory water-recalib-2026-05-23.md):
      RAW_EMPTY = 29.7   anchor at pump-intake water level (morning dry-fire)
      RAW_AT_60 = 70.2   measured after +23 L fill (~62% of ~37 L usable)
      scale     = 60 / (70.2 - 29.7) = 1.481
                                       (slope drifted from 2026-03-02's 1.676)

    Tank is ~45 L total but ~8 L sit below the pump intake (dead zone). By
    design, display 0% == 0% USABLE (not 0% physical). The water<5 / water<15
    thresholds in validate() are evaluated against this corrected %, never raw.
    NR source: `water_recal_fn_001` function in flows.json — keep both in sync."""
    out, _ = run("mosquitto_sub -t 'esp/mistertank/tank_percent' -C 1 -W 5", timeout=8)
    try:
        raw = float(out)
    except (ValueError, TypeError):
        return None
    RAW_EMPTY = 29.7
    RAW_AT_60 = 70.2
    scale = 60.0 / (RAW_AT_60 - RAW_EMPTY)  # 1.481
    corrected = (raw - RAW_EMPTY) * scale
    return max(0.0, min(100.0, corrected))


def get_service_active(name):
    out, _ = run(f"systemctl is-active {name}")
    return out == "active"


def get_nr_uptime():
    """Service uptime in seconds. Uses the monotonic clock so DST transitions
    don't make us report uptime off by 1 hour (the old version hardcoded CEST
    via datetime, which silently became wrong every Oct-Mar)."""
    out, _ = run("systemctl show nodered --property=ActiveEnterTimestampMonotonic --value")
    try:
        mono_us = int(out.strip())  # microseconds since boot
        if mono_us == 0:
            return None  # service never started
        with open("/proc/uptime") as f:
            sys_uptime_s = float(f.read().split()[0])
        return max(0.0, sys_uptime_s - (mono_us / 1_000_000.0))
    except (ValueError, IOError, OSError):
        return None


def get_nr_errors():
    out, _ = run('journalctl -u nodered --since "10 min ago" --no-pager 2>/dev/null '
                 '| grep -i "\\[error\\]" | grep -iv "callmebot\\|whatsapp-cmb" | tail -3')
    return out or None


def check_nr_http():
    try:
        with urllib.request.urlopen("http://localhost:1880", timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_arduino_status():
    data = influx_query("SELECT last(value) FROM arduino_status WHERE time > now() - 2m")
    if not data:
        return None, None
    series = data.get("results", [{}])[0].get("series", [])
    if not series:
        return None, None
    age = time.time() - parse_influx_ts(series[0]["values"][0][0])
    return series[0]["values"][0][1], age


def get_watchdog_warns():
    out, _ = run('journalctl -u arduino-watchdog --since "30 min ago" --no-pager 2>/dev/null '
                 '| grep -iE "WARN|USB reset|REBOOT" | tail -3')
    return out or None


def get_meross_power():
    data = influx_query("SELECT last(value) FROM power_consumption WHERE time > now() - 5m")
    if not data:
        return None, None
    series = data.get("results", [{}])[0].get("series", [])
    if not series:
        return None, None
    age = time.time() - parse_influx_ts(series[0]["values"][0][0])
    return series[0]["values"][0][1], age


def get_mister_cron_runs():
    out, _ = run('journalctl -t CRON --since "2 min ago" --no-pager 2>/dev/null '
                 '| grep mister-failsafe | wc -l')
    try:
        return int(out)
    except (ValueError, TypeError):
        return 0


def get_wifi_pm():
    out, _ = run("/usr/sbin/iwconfig wlan0 2>/dev/null | grep 'Power Management'")
    if out and "off" in out.lower():
        return "off"
    if out and "on" in out.lower():
        return "on"
    return "unknown"


# ── Smart validation ────────────────────────────────────────────────────

def validate(now_cest, sensors, tapo, pings, water, arduino_age,
             meross_watts, meross_age, nr_active, wd_active, meross_active, state=None):
    """Cross-check values against automation logic for current time."""
    warns = []
    h = now_cest.hour + now_cest.minute / 60.0

    # Services
    if not nr_active:
        warns.append(("red", "Node-RED is DOWN"))
    if not wd_active:
        warns.append(("red", "Arduino watchdog is DOWN"))
    if not meross_active:
        warns.append(("yellow", "Meross daemon is DOWN"))

    # Device reachability
    for name, ms in pings.items():
        if ms is None:
            warns.append(("red", f"{name} plug unreachable"))

    # Arduino serial
    if arduino_age is None:
        warns.append(("red", "No arduino_status in InfluxDB"))
    elif arduino_age > 120:
        warns.append(("red", f"Arduino serial stale ({arduino_age:.0f}s)"))

    if sensors is None:
        warns.append(("red", "InfluxDB unreachable or no recent data"))
        return warns

    temp     = sensors.get("local_temperature", {}).get("value")
    humi     = sensors.get("local_humidity", {}).get("value")
    tgt_t    = sensors.get("target_temperature_computed", {}).get("value")
    tgt_h    = sensors.get("target_humidity_computed", {}).get("value")
    fan_circ = sensors.get("fan_pwm_circulation", {}).get("value")
    fan_frz  = sensors.get("fan_pwm_freezer", {}).get("value")
    frzr     = sensors.get("freezer_status", {}).get("value")
    light    = sensors.get("light_status", {}).get("value")

    # Sensor freshness - RBE channels (fan_pwm_*) are exempt; their age is
    # meaningless because they only log on value change. Room-feed channels
    # have their own dedicated check below.
    for name, s in sensors.items():
        if s.get("rbe"):
            continue
        if s.get("room"):
            continue
        if s["age"] > 120:
            warns.append(("red", f"{name} STALE ({s['age']:.0f}s)"))
        elif s["age"] > 90:
            warns.append(("yellow", f"{name} aging ({s['age']:.0f}s)"))

    # Room feed (DietPi) staleness ladder - longer thresholds than cabinet
    # sensors because the DietPi can be offline for hours without affecting
    # cabinet control, but the operator should know.
    room_age = sensors.get("room_temperature", {}).get("age")
    if room_age is None:
        warns.append(("yellow", "room feed: no data in 30d window (DietPi?)"))
    elif room_age > 86400:
        warns.append(("yellow", f"room feed STALE {room_age/86400:.1f}d (DietPi down?)"))
    elif room_age > 900:
        warns.append(("yellow", f"room feed STALE {room_age/60:.0f}min (DietPi?)"))

    # Lights vs Tapo consistency
    tapo_light = tapo.get("lights", {}).get("on")
    if light is not None and tapo_light is not None:
        if bool(light) != tapo_light:
            warns.append(("red", f"light_status={int(light)} but Tapo {'ON' if tapo_light else 'OFF'}"))

    # Freezer logic
    if frzr is not None and temp is not None and tgt_t is not None:
        if 8 <= h < 20 and frzr == 1:
            warns.append(("red", "Freezer ON during daytime gate (08-20)"))
        if frzr == 1 and temp < tgt_t - 1.0:
            warns.append(("yellow", f"Freezer ON but temp {temp:.1f}C below target {tgt_t:.1f}C"))
        if frzr == 0 and temp > tgt_t + 1.5 and not (8 <= h < 20):
            warns.append(("yellow", f"Freezer OFF but temp {temp:.1f}C >> target {tgt_t:.1f}C"))

    # Freezer vs Tapo consistency (added 2026-05-15 — caught freezer stuck ON
    # while NR commanded OFF for 1h44m; existing power-based stuck check only
    # watches the Tapo→power direction, missing "OFF command never delivered").
    # Uses same hysteresis (3 polls / ~15 min) as the power-based STUCK check
    # to absorb Tapo poll lag during legitimate ON/OFF transitions.
    tapo_fz_state = tapo.get("freezer", {}).get("on")
    if frzr is not None and tapo_fz_state is not None:
        # Mirror the power-based STUCK check: suppress during legitimate
        # ON->OFF / OFF->ON transitions to avoid false-positive while Tapo
        # poll cache catches up to the new cmd. Hysteresis alone (3 samples)
        # could still false-alert under sustained Tapo session-refresh lag.
        if bool(frzr) != tapo_fz_state and not freezer_changed_recently(STUCK_TRANSITION_WINDOW):
            mism_n = (state or {}).get("freezer_state_mismatch_count", 0) + 1
            if state is not None:
                state["freezer_state_mismatch_count"] = mism_n
            if mism_n >= STUCK_HYSTERESIS_SAMPLES:
                warns.append(("red",
                    f"STUCK FREEZER PLUG: NR commands {'ON' if frzr else 'OFF'} but "
                    f"Tapo {'ON' if tapo_fz_state else 'OFF'} for {mism_n} consecutive polls "
                    f"(~{mism_n*5} min) — command not delivered"))
            else:
                warns.append(("yellow",
                    f"Freezer state mismatch: NR={int(frzr)} Tapo="
                    f"{'ON' if tapo_fz_state else 'OFF'} (sample {mism_n}/{STUCK_HYSTERESIS_SAMPLES}) — watching"))
        else:
            if state is not None and state.get("freezer_state_mismatch_count", 0) > 0:
                state["freezer_state_mismatch_count"] = 0

    # Fan baseline tracking — circulation (P12) and freezer-evaporator (P44)
    # fans should track freezer state: 255 when freezer ON, baseline 140 when
    # freezer OFF (current setting since 2026-05-06; was 220 in early May, 200
    # in late April). A non-zero mismatch is a 🟡 — could be a baseline-edit
    # regression in NR, a missed PWM command, or stale RBE that hasn't caught
    # up to a recent freezer transition.
    #
    # Zero values are NOT warned: 0 means an intentional override is active
    # (door safety, mister cycle, or a manual NR-side disable). The cron has
    # no visibility into those — outlet/impeller validation is omitted for
    # the same reason (lights-off/freezer-latched gate + door safety make
    # 5-min cron windows noisy).
    CIRC_FRZ_BASELINE = 140
    if frzr is not None:
        if frzr == 1:
            if fan_circ is not None and int(fan_circ) not in (0, 255):
                warns.append(("yellow",
                    f"fan_pwm_circulation={int(fan_circ)} but freezer ON (expected 255)"))
            if fan_frz is not None and int(fan_frz) not in (0, 255):
                warns.append(("yellow",
                    f"fan_pwm_freezer={int(fan_frz)} but freezer ON (expected 255)"))
        elif frzr == 0:
            if fan_circ is not None and int(fan_circ) not in (0, CIRC_FRZ_BASELINE):
                warns.append(("yellow",
                    f"fan_pwm_circulation={int(fan_circ)} but freezer OFF "
                    f"(expected {CIRC_FRZ_BASELINE})"))
            if fan_frz is not None and int(fan_frz) not in (0, CIRC_FRZ_BASELINE):
                warns.append(("yellow",
                    f"fan_pwm_freezer={int(fan_frz)} but freezer OFF "
                    f"(expected {CIRC_FRZ_BASELINE})"))

    # Mister stuck
    mister = tapo.get("mister", {})
    if mister.get("on") and mister.get("on_time", 0) > 150:
        warns.append(("red", f"Mister ON {mister['on_time']}s (>150s threshold)"))

    # Water level
    if water is not None:
        if water < 5:
            warns.append(("red", f"Water critical: {water:.0f}%"))
        elif water < 15:
            warns.append(("yellow", f"Water low: {water:.0f}%"))
    else:
        warns.append(("yellow", "ESP water level timeout"))

    # Power cross-check v4 (2026-05-11) — only flag the safety-critical
    # "freezer stuck ON" case (cooling the terrarium when it shouldn't).
    #
    # Power model refit 2026-05-11 from 7 days of freezer-OFF + mister-OFF data
    # (`/tmp/fit_lights_model_v2.py`). Old model (slider × 2.0, base 9 W) predicted
    # 149 W at Curve-C peak (slider 70) but the real cabinet draws ~220 W there —
    # off by 71 W, triggering the exact false-positive at the 70 W STUCK threshold.
    #
    # Calibration (freezer + mister OFF, Curve C since 2026-05-04):
    #   - Lights OFF baseline (night): ~17 W (Pi + Arduino + ESP + Meross + idle fans)
    #   - Lights ON, slider 0 (ramp start at 06:30 CEST): ~30 W
    #     → daytime fan + heatsink-fan idle adds ~13 W when lights ON
    #   - Lights ON, slider 70 (Curve C peak, ~13:15 CEST): ~220 W (p10=219, p90=222, n=255)
    #     → LED slope ≈ (220 - 30) / 70 = 2.71 W per slider unit
    #   - Lights ON, slider 50 (mid-ramp ~10:00 CEST): ~186 W → consistent slope
    #
    # New model: P_expected = base + lights_overhead + LED_slope * slider + freezer + mister
    # Conservative (under-estimates slightly so STUCK threshold has headroom).
    # Power cross-check: REQUIRE fresh meross sample. A stale reading (daemon
    # stopped, MQTT broker blip) could miss a real stuck-relay event OR
    # false-alert on a cached pre-stop spike. Cap at 120s = 4 samples at 30s.
    if meross_watts is not None and meross_age is not None and meross_age < 120:
        tapo_fz = tapo.get("freezer", {}).get("on", False)
        tapo_lt = tapo.get("lights", {}).get("on", False)
        tapo_ms = tapo.get("mister", {}).get("on", False)

        slider = get_light_slider()  # 0..100 or None
        base_w           = 9
        daytime_fans_w   = 13 if tapo_lt else 0   # cabinet fans + LED heatsink fans, idle while lights on
        freezer_w        = 110 if tapo_fz else 0
        mister_w         = 30  if tapo_ms else 0  # 2026-05-21: was 5W; misting pump actually draws ~30W (user calibration)
        lights_dim_w     = ((slider or 0) * 2.71) if tapo_lt else 0
        expected_w = base_w + daytime_fans_w + freezer_w + lights_dim_w + mister_w
        excess = meross_watts - expected_w

        # STUCK RELAY check with two false-positive guards (added 2026-05-11):
        #   (a) transition-window suppression: skip if freezer cmd state just changed
        #       (Tapo poll cache + Meross averaging are not synchronous)
        #   (b) N-sample hysteresis: require sustained excess across STUCK_HYSTERESIS_SAMPLES
        #       consecutive cycles before declaring RED (a real stuck compressor runs for hours;
        #       a poll-skew artifact resolves in one cycle)
        if not tapo_fz and excess > 70:
            in_transition = freezer_changed_recently(STUCK_TRANSITION_WINDOW)
            if in_transition:
                # Cmd state changed in the last 2 min — likely poll skew, not a stuck relay.
                # Do not count this towards hysteresis (resets cleanly when transition clears).
                warns.append(("yellow",
                    f"Excess +{excess:.0f}W during freezer cmd transition (suppressed STUCK check, "
                    f"Tapo poll likely stale)"))
            else:
                suspect_n = (state or {}).get("stuck_suspect_count", 0) + 1
                if state is not None:
                    state["stuck_suspect_count"] = suspect_n
                if suspect_n >= STUCK_HYSTERESIS_SAMPLES:
                    warns.append(("red",
                        f"STUCK RELAY: freezer cmd OFF but +{excess:.0f}W excess for {suspect_n} "
                        f"consecutive polls — compressor likely running (observed {meross_watts:.0f}W, "
                        f"expected {expected_w:.0f}W, slider={slider})"))
                else:
                    warns.append(("yellow",
                        f"Suspect stuck freezer relay (+{excess:.0f}W, sample "
                        f"{suspect_n}/{STUCK_HYSTERESIS_SAMPLES}) — watching"))
        else:
            # Clear hysteresis count when condition resolves
            if state is not None and state.get("stuck_suspect_count", 0) > 0:
                state["stuck_suspect_count"] = 0

        if meross_watts > 500:
            warns.append(("yellow", f"High power: {meross_watts:.0f}W"))

    return warns


def get_led_fault_warning():
    """Read /tmp/led-fault.flag if present (written by Node-RED LED watchdog).

    Returns a list of (severity, msg) tuples to append to the warnings list.
    Empty if no flag, or flag is unreadable.
    """
    flag_path = "/tmp/led-fault.flag"
    try:
        if not os.path.exists(flag_path):
            return []
        with open(flag_path) as f:
            data = json.load(f)
        phase = data.get("phase", "?")
        msg = data.get("msg", "LED fault flagged by NR watchdog")
        ts = data.get("ts", "")
        if phase == "LOCKED":
            return [("red", f"LED fault LOCKED: {msg} (since {ts})")]
        else:
            return [("red", f"LED fault active ({phase}): {msg}")]
    except Exception as e:
        return [("yellow", f"LED fault flag unreadable: {e}")]


async def auto_fix_stuck_relay(warnings, state):
    """Cycle stuck Tapo relays detected by power cross-check.

    ON→OFF for relays stuck ON (e.g. freezer compressor won't stop).
    OFF→ON for relays stuck OFF — currently only the ON→OFF (freezer) path is implemented; the lights branch below is reachable code but no validate() warning produces a matching 'lights ... stuck OFF' string, so it never fires (2026-05-18).
    15-min cooldown between attempts.
    """
    stuck = [w for w in warnings if w[1].startswith("STUCK RELAY")]
    if not stuck:
        return []

    now = time.time()
    remaining = POWER_FIX_COOLDOWN - (now - state.get("last_power_fix", 0))
    if remaining > 0:
        return [("yellow", f"Stuck relay detected but auto-fix on cooldown ({remaining:.0f}s left)")]

    extra = []
    try:
        from tapo import ApiClient
        client = ApiClient(TAPO_EMAIL, TAPO_PASS)
    except Exception as e:
        return [("red", f"Auto-fix: Tapo client error: {e}")]

    for _, msg in stuck:
        if "freezer" in msg.lower():
            plug, cycle = "freezer", "on_off"
        elif False and "lights" in msg.lower() and "stuck OFF" in msg:  # NEVER fires — feature not implemented; left in place for future implementation
            plug, cycle = "lights", "off_on"
        else:
            continue

        try:
            dev = await client.p100(PLUGS[plug])

            # Fresh re-poll guard (added 2026-05-11): the cached Tapo state in `tapo`
            # is what triggered STUCK; verify it is still off before cycling. A fresh
            # poll catches the case where the original detection used a stale poll
            # value during a freezer cmd transition.
            try:
                fresh_info = await dev.get_device_info()
                fresh_on = fresh_info.device_on
            except Exception:
                fresh_on = None
            if cycle == "on_off" and fresh_on is False:
                # The plug is genuinely OFF on a fresh poll → the STUCK was a stale
                # cached state. Skip the OFF cycle (it would have been a no-op) but
                # respect the cooldown so we don't loop on the same condition.
                state["last_power_fix"] = now
                extra.append(("yellow",
                    f"AUTO-FIX skipped: {plug} re-polled OFF (stale cached state, "
                    f"false positive cleared)"))
                continue
            if cycle == "off_on" and fresh_on is True:
                state["last_power_fix"] = now
                extra.append(("yellow",
                    f"AUTO-FIX skipped: {plug} re-polled ON (stale cached state)"))
                continue

            if cycle == "on_off":
                await dev.on()
                await asyncio.sleep(3)
                await dev.off()
            else:
                await dev.off()
                await asyncio.sleep(3)
                await dev.on()
            state["last_power_fix"] = now
            direction = "ON→OFF" if cycle == "on_off" else "OFF→ON"
            extra.append(("yellow", f"AUTO-FIX: cycled {plug} {direction} to unstick relay"))
        except Exception as e:
            extra.append(("red", f"AUTO-FIX failed for {plug}: {e}"))

    return extra


# ── Report builder ──────────────────────────────────────────────────────

def fmt_time(seconds):
    if seconds is None:
        return "?"
    h, rem = divmod(int(seconds), 3600)
    m = rem // 60
    return f"{h}h{m:02d}m" if h else f"{m}m"


def worst(*levels):
    if "red" in levels:
        return "🔴"
    if "yellow" in levels:
        return "🟡"
    return "🟢"


def build_report(now_cest, pings, tapo, sensors, water,
                 nr_active, nr_http, nr_uptime, nr_errors,
                 wd_active, wd_warns, arduino_val, arduino_age,
                 meross_active, meross_watts, meross_age,
                 mister_cron, wifi_pm, warnings):
    lines = []

    # ── DEVICES ──
    dev_lvls = []
    ping_parts = []
    for name in ("freezer", "lights", "mister"):
        ms = pings.get(name)
        if ms is not None:
            ping_parts.append(f"{name}={ms:.0f}ms")
        else:
            ping_parts.append(f"{name}=TIMEOUT")
            dev_lvls.append("red")
    wtr = f"esp={water:.0f}%" if water is not None else "esp=TIMEOUT"
    if water is None:
        dev_lvls.append("yellow")
    elif water < 5:
        dev_lvls.append("red")
    elif water < 15:
        dev_lvls.append("yellow")
    lines.append(f"{worst(*dev_lvls)} DEVICES  {'  '.join(ping_parts)}  {wtr}")

    # ── TAPO ──
    tapo_lvls = []
    tapo_parts = []
    for name in ("freezer", "lights", "mister"):
        info = tapo.get(name, {})
        if "error" in info:
            tapo_parts.append(f"{name}=ERR")
            tapo_lvls.append("red")
        elif info.get("on"):
            tapo_parts.append(f"{name}=ON({fmt_time(info.get('on_time'))})")
            if name == "mister" and info.get("on_time", 0) > 150:
                tapo_lvls.append("red")
        else:
            tapo_parts.append(f"{name}=OFF")
    lines.append(f"{worst(*tapo_lvls)} TAPO     {'  '.join(tapo_parts)}")

    # ── SENSORS ──
    if sensors:
        def fv(key, fmt):
            v = sensors.get(key, {}).get("value")
            return format(v, fmt) if isinstance(v, (int, float)) else "?"
        # Only continuous channels count toward staleness; RBE fan_pwm_* are exempt.
        cont_ages = [s["age"] for s in sensors.values() if not s.get("rbe")]
        max_age = max(cont_ages) if cont_ages else 0
        s_lvl = "red" if max_age > 120 else ("yellow" if max_age > 90 else "")
        lines.append(f"{worst(s_lvl)} SENSORS  "
                     f"temp={fv('local_temperature','.1f')}C  "
                     f"humi={fv('local_humidity','.0f')}%  "
                     f"tgt_t={fv('target_temperature_computed','.1f')}C  "
                     f"tgt_h={fv('target_humidity_computed','.0f')}%  "
                     f"fans=circ:{fv('fan_pwm_circulation','.0f')} "
                     f"frz:{fv('fan_pwm_freezer','.0f')} "
                     f"out:{fv('fan_pwm_outlet','.0f')} "
                     f"imp:{fv('fan_pwm_impeller','.0f')}  "
                     f"(cont <{int(max_age)+1}s)")
    else:
        lines.append("🔴 SENSORS  InfluxDB unreachable")

    # ── STATE ──
    st_lvls = []
    frzr_str = lt_str = "?"
    if sensors:
        fz = sensors.get("freezer_status", {}).get("value")
        lt = sensors.get("light_status", {}).get("value")
        frzr_str = "ON" if fz == 1 else ("OFF" if fz == 0 else "?")
        lt_str = "ON" if lt == 1 else ("OFF" if lt == 0 else "?")
    if arduino_age is not None:
        if arduino_age > 120:
            ard_str = f"STALE({arduino_age:.0f}s)"
            st_lvls.append("red")
        elif arduino_age > 60:
            ard_str = f"OK({arduino_age:.0f}s)"
            st_lvls.append("yellow")
        else:
            ard_str = f"OK({arduino_age:.0f}s)"
    else:
        ard_str = "NO DATA"
        st_lvls.append("red")
    lines.append(f"{worst(*st_lvls)} STATE    freezer={frzr_str}  light={lt_str}  arduino={ard_str}")

    # ── NODERED ──
    nr_lvls = []
    if not nr_active:
        nr_lvls.append("red")
        nr_str = "DOWN"
    elif not nr_http:
        nr_lvls.append("red")
        nr_str = "active(no HTTP)"
    else:
        nr_str = "active(200)"
    if nr_uptime is not None and nr_uptime < 600:
        nr_lvls.append("yellow")
    err_str = "none"
    if nr_errors:
        nr_lvls.append("yellow")
        err_str = f"{len(nr_errors.strip().splitlines())} recent"
    lines.append(f"{worst(*nr_lvls)} NODERED  {nr_str}  uptime={fmt_time(nr_uptime)}  errors={err_str}")

    # ── WATCHDOG ──
    wd_lvls = []
    if not wd_active:
        wd_lvls.append("red")
    warn_str = "clean"
    if wd_warns:
        wd_lvls.append("yellow")
        warn_str = wd_warns.strip().splitlines()[-1][:50]
    lines.append(f"{worst(*wd_lvls)} WATCHDOG {'active' if wd_active else 'DOWN'}  "
                 f"serial={ard_str}  {warn_str}")

    # ── MEROSS ──
    mr_lvls = []
    if not meross_active:
        mr_lvls.append("yellow")
        lines.append(f"{worst(*mr_lvls)} MEROSS   DOWN")
    elif meross_watts is not None:
        if meross_age and meross_age > 120:
            mr_lvls.append("yellow")
        age_s = f"{meross_age:.0f}s ago" if meross_age else "?"
        lines.append(f"{worst(*mr_lvls)} MEROSS   active  {meross_watts:.0f}W  ({age_s})")
    else:
        mr_lvls.append("yellow")
        lines.append(f"🟡 MEROSS   active  no data")

    # ── MISTER ──
    mi_lvls = []
    if mister_cron == 0:
        mi_lvls.append("yellow")
    lines.append(f"{worst(*mi_lvls)} MISTER   cron={'OK' if mister_cron > 0 else 'MISSING'}"
                 f"({mister_cron}/2min)")

    # ── WIFI ──
    wi_lvl = "" if wifi_pm == "off" else ("red" if wifi_pm == "on" else "yellow")
    lines.append(f"{worst(wi_lvl)} WIFI     power_mgmt={wifi_pm}")

    # ── WARNINGS ──
    if warnings:
        lines.append("")
        lines.append("⚠️ WARNINGS")
        for level, msg in warnings:
            lines.append(f"{'🔴' if level == 'red' else '🟡'} {msg}")

    overall = "red" if any(w[0] == "red" for w in warnings) else (
              "yellow" if any(w[0] == "yellow" for w in warnings) else "green")
    return "\n".join(lines), overall


# ── State & messaging ──────────────────────────────────────────────────

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_green": 0, "last_alert": 0, "last_alert_hash": "",
                "current_severity": "green"}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def should_send(level, alert_hash, state):
    now = time.time()
    if level == "green":
        return now - state.get("last_green", 0) >= GREEN_INTERVAL
    if alert_hash != state.get("last_alert_hash", ""):
        return True
    return now - state.get("last_alert", 0) >= ALERT_COOLDOWN


def send_gmail(subject, body):
    if GMAIL_APP_PASS == "XXXXXX":
        print("Gmail not configured (APP_PASS placeholder)", file=sys.stderr)
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = GMAIL_TO
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as s:
            s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"Gmail send failed: {e}", file=sys.stderr)
        return False


def send_whatsapp(msg):
    if not CALLMEBOT_KEY:
        return False
    encoded = urllib.parse.quote(msg)
    url = (f"https://api.callmebot.com/whatsapp.php"
           f"?phone={PHONE}&text={encoded}&apikey={CALLMEBOT_KEY}")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            body = resp.read().decode()
            if "banned" in body.lower() or "error" in body.lower():
                print(f"CallMeBot rejected: {body[:100]}", file=sys.stderr)
                return False
            return True
    except Exception as e:
        print(f"WhatsApp send failed: {e}", file=sys.stderr)
        return False


def send_alert(report, overall, subject_override=None):
    """Send via all configured channels. Returns True if at least one succeeded.
    subject_override lets callers send a 'cleared' / 'escalated' subject without
    inventing a fake `overall` level."""
    if subject_override is not None:
        subject = subject_override
    else:
        subject = {
            "green": "🟢 Terrarium OK",
            "yellow": "🟡 Terrarium Warning",
            "red": "🔴 Terrarium Alert",
        }.get(overall, "Terrarium Health")

    ok = False
    ok = send_gmail(subject, report) or ok
    ok = send_whatsapp(report) or ok
    return ok


# ── Main ────────────────────────────────────────────────────────────────

async def main():
    now_cest = datetime.now(CEST)

    # Collect data
    pings = {name: ping_device(ip) for name, ip in PLUGS.items()}
    tapo = await get_tapo_states()
    sensors = get_sensors()
    water = get_water_level()
    nr_active = get_service_active("nodered")
    nr_http = check_nr_http()
    nr_uptime = get_nr_uptime()
    nr_errors = get_nr_errors()
    wd_active = get_service_active("arduino-watchdog")
    wd_warns = get_watchdog_warns()
    arduino_val, arduino_age = get_arduino_status()
    meross_active = get_service_active("meross-daemon")
    meross_watts, meross_age = get_meross_power()
    mister_cron = get_mister_cron_runs()
    wifi_pm = get_wifi_pm()

    # Load state up-front so validate() can mutate hysteresis counters in it
    state = load_state()

    # Validate
    warnings = validate(now_cest, sensors, tapo, pings, water, arduino_age,
                        meross_watts, meross_age, nr_active, wd_active, meross_active, state)

    # External fault flags (NR LED watchdog writes /tmp/led-fault.flag)
    warnings.extend(get_led_fault_warning())

    # Auto-fix stuck relays (power cross-check)
    fix_warns = await auto_fix_stuck_relay(warnings, state)
    if fix_warns:
        warnings.extend(fix_warns)

    # Build report
    report, overall = build_report(
        now_cest, pings, tapo, sensors, water,
        nr_active, nr_http, nr_uptime, nr_errors,
        wd_active, wd_warns, arduino_val, arduino_age,
        meross_active, meross_watts, meross_age,
        mister_cron, wifi_pm, warnings)

    ts = now_cest.strftime("%H:%M CEST")
    full_report = f"🌿 Terrarium — {ts}\n{report}"
    print(full_report)

    # Decide whether to send.
    # Hash by alert *class* — strip numbers so the same anomaly type
    # dedupes across cycles even when W values drift. Also require two
    # consecutive cycles of the same class before firing; transient single-
    # cycle anomalies (compressor inrush, WiFi blip) get swallowed.
    class_text = "\n".join(f"{w[0]}:{w[1]}" for w in warnings)
    class_text = re.sub(r"-?[0-9]+(?:\.[0-9]+)?", "#", class_text)
    alert_hash = hashlib.md5(class_text.encode()).hexdigest()[:8]

    # Severity-aware dispatch (2026-05-22, tag:yellow_edge_trigger_2026_05_22):
    #   - YELLOW is EDGE-TRIGGERED: send once on entry, silent during persistence,
    #     send a "cleared" email on yellow→green. No 30-min repeats while warning
    #     persists. Avoids the alert-fatigue from yellow-as-red.
    #   - RED keeps existing behaviour: 2-cycle persistence then 30-min cooldown
    #     repeats until resolved.
    #   - GREEN periodic report every GREEN_INTERVAL when nothing is wrong.
    prev_severity = state.get("current_severity", "green")

    if overall == "red":
        prev = state.get("last_class_hash", "")
        state["last_class_hash"] = alert_hash
        persistent = (prev == alert_hash)
        if persistent and should_send(overall, alert_hash, state):
            if send_alert(full_report, overall):
                state["last_alert"] = time.time()
                state["last_alert_hash"] = alert_hash
                state["current_severity"] = "red"
    elif overall == "yellow":
        prev = state.get("last_class_hash", "")
        state["last_class_hash"] = alert_hash
        persistent = (prev == alert_hash)
        # Send ONLY on entry into yellow (after the 2-cycle persistence check).
        # Once we have emailed about this yellow episode, stay silent until
        # the warning either escalates to red (handled above) or clears to green.
        if persistent and prev_severity != "yellow":
            if send_alert(full_report, "yellow"):
                state["last_alert"] = time.time()
                state["last_alert_hash"] = alert_hash
                state["current_severity"] = "yellow"
        elif persistent:
            # Already in yellow — keep severity sticky, suppress repeats.
            state["current_severity"] = "yellow"
    else:  # green
        state["last_class_hash"] = ""
        if prev_severity == "yellow":
            # Resolution email — fire once on yellow→green transition.
            cleared_report = ("✅ Previously-yellow warning(s) cleared.\n\n" + full_report)
            if send_alert(cleared_report, "green",
                          subject_override="✅ Terrarium WARNING cleared"):
                state["current_severity"] = "green"
                state["last_green"] = time.time()  # counts as a periodic green too
        else:
            # Already green (or red→green: red doesn't need a resolution email
            # under the current contract — the next periodic green report covers it).
            state["current_severity"] = "green"
            if should_send("green", "", state):
                if send_alert(full_report, overall):
                    state["last_green"] = time.time()

    save_state(state)


if __name__ == "__main__":
    asyncio.run(main())


