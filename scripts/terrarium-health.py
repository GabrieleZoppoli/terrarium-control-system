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
GMAIL_ADDRESS = "REDACTED — Gmail sender address"
GMAIL_APP_PASS = "REDACTED — set Gmail app password before deployment"
GMAIL_TO = "REDACTED — Gmail recipient address"

PHONE = "REDACTED — E.164 phone for WhatsApp alerts"
CALLMEBOT_KEY = "REDACTED — get from callmebot.com"  # Set to "" to disable WhatsApp

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
TAPO_PASS = "REDACTED — Tapo account password"
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
    q = ("SELECT last(value) FROM local_temperature, local_humidity, "
         "target_temperature_computed, target_humidity_computed, "
         "fan_speed, freezer_status, light_status WHERE time > now() - 5m")
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
        }
    return sensors if sensors else None


def get_water_level():
    out, _ = run("mosquitto_sub -t 'esp/mistertank/tank_percent' -C 1 -W 5", timeout=8)
    try:
        return float(out)
    except (ValueError, TypeError):
        return None


def get_service_active(name):
    out, _ = run(f"systemctl is-active {name}")
    return out == "active"


def get_nr_uptime():
    out, _ = run("systemctl show nodered --property=ActiveEnterTimestamp")
    m = re.search(r"=(.+)$", out)
    if not m:
        return None
    try:
        parts = m.group(1).strip().split()
        dt = datetime.strptime(" ".join(parts[1:3]), "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=CEST)
        return time.time() - dt.timestamp()
    except Exception:
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
             meross_watts, nr_active, wd_active, meross_active, state=None):
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

    temp   = sensors.get("local_temperature", {}).get("value")
    humi   = sensors.get("local_humidity", {}).get("value")
    tgt_t  = sensors.get("target_temperature_computed", {}).get("value")
    tgt_h  = sensors.get("target_humidity_computed", {}).get("value")
    fans   = sensors.get("fan_speed", {}).get("value")
    frzr   = sensors.get("freezer_status", {}).get("value")
    light  = sensors.get("light_status", {}).get("value")

    # Sensor freshness
    for name, s in sensors.items():
        if s["age"] > 120:
            warns.append(("red", f"{name} STALE ({s['age']:.0f}s)"))
        elif s["age"] > 90:
            warns.append(("yellow", f"{name} aging ({s['age']:.0f}s)"))

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

    # Fan schedule — NOTE: fan_speed global is stale at night (keeps last PID
    # value, not actual GPIO output), so we cannot reliably detect fan anomalies
    # from this value alone. Only warn if fans are clearly wrong AND fresh.

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
    if meross_watts is not None:
        tapo_fz = tapo.get("freezer", {}).get("on", False)
        tapo_lt = tapo.get("lights", {}).get("on", False)
        tapo_ms = tapo.get("mister", {}).get("on", False)

        slider = get_light_slider()  # 0..100 or None
        base_w           = 9
        daytime_fans_w   = 13 if tapo_lt else 0   # cabinet fans + LED heatsink fans, idle while lights on
        freezer_w        = 110 if tapo_fz else 0
        mister_w         = 5   if tapo_ms else 0
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
    OFF→ON for relays stuck OFF (e.g. lights not receiving power).
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
        elif "lights" in msg.lower() and "stuck OFF" in msg:
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
        max_age = max(s["age"] for s in sensors.values())
        s_lvl = "red" if max_age > 120 else ("yellow" if max_age > 90 else "")
        lines.append(f"{worst(s_lvl)} SENSORS  "
                     f"temp={fv('local_temperature','.1f')}C  "
                     f"humi={fv('local_humidity','.0f')}%  "
                     f"tgt_t={fv('target_temperature_computed','.1f')}C  "
                     f"tgt_h={fv('target_humidity_computed','.0f')}%  "
                     f"fans={fv('fan_speed','.0f')}  "
                     f"(all <{int(max_age)+1}s)")
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
        return {"last_green": 0, "last_alert": 0, "last_alert_hash": ""}


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


def send_alert(report, overall):
    """Send via all configured channels. Returns True if at least one succeeded."""
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
                        meross_watts, nr_active, wd_active, meross_active, state)

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

    if overall in ("red", "yellow"):
        prev = state.get("last_class_hash", "")
        state["last_class_hash"] = alert_hash
        # Require two consecutive cycles of the same anomaly class.
        persistent = (prev == alert_hash)
        if persistent and should_send(overall, alert_hash, state):
            if send_alert(full_report, overall):
                state["last_alert"] = time.time()
                state["last_alert_hash"] = alert_hash
    else:
        state["last_class_hash"] = ""
        if should_send("green", "", state):
            if send_alert(full_report, overall):
                state["last_green"] = time.time()

    save_state(state)


if __name__ == "__main__":
    asyncio.run(main())


