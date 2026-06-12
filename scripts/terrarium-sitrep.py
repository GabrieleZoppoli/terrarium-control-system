#!/usr/bin/env python3
"""
Terrarium sitrep generator. Produces a 5-section status report.

Sections:
  1. Operating envelope (current readings + control regime)
  2. Stack health (services, watchdogs, ingest, resources)
  3. Pending checkpoints (timers, due flags)
  4. Recent activity (last 12h: freezer cycles, mist events, extremes, alerts)
  5. No-go signals (anything currently yellow or red)

Modes:
  default          print all sections (markdown) to stdout
  --section N      print only section N (1-5) to stdout
  --email          send HTML version of all sections via Gmail

Used by:
  - /health Claude skill (terminal/markdown)
  - 7AM + 9PM cron digests (email mode)
"""

import argparse
import json
import os
import smtplib
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_ADDRESS  = "REDACTED — Gmail sender address"
GMAIL_APP_PASS = "REDACTED — set Gmail app password before deployment"
GMAIL_TO       = "REDACTED — Gmail recipient address"

INFLUX_URL = "http://localhost:8086"
DB = "highland"
NR_GLOBAL_PATH = "/home/pi/.node-red/context/global/global.json"


def influx_query(q, db=DB, timeout=10):
    url = f"{INFLUX_URL}/query?db={db}&q={urllib.parse.quote(q)}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.load(r)
    except Exception as e:
        return {"error": str(e)}


def influx_last(measurement, window="5m"):
    q = f"SELECT last(value) FROM {measurement} WHERE time > now() - {window}"
    r = influx_query(q)
    try:
        s = r["results"][0]["series"][0]
        ts_str = s["values"][0][0]
        val    = s["values"][0][1]
        ts_str = ts_str.rstrip("Z")
        if "." in ts_str:
            base, frac = ts_str.split(".", 1)
            ts_str = base + "." + frac[:6]
        dt = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
        age = time.time() - dt.timestamp()
        return val, age
    except (KeyError, IndexError, TypeError):
        return None, None


def influx_count(measurement, window="12h"):
    q = f"SELECT count(*) FROM {measurement} WHERE time > now() - {window}"
    r = influx_query(q)
    try:
        return r["results"][0]["series"][0]["values"][0][1] or 0
    except (KeyError, IndexError):
        return 0


def systemctl_active(unit):
    try:
        r = subprocess.run(["systemctl", "is-active", unit],
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except Exception:
        return "unknown"


def nr_globals():
    try:
        with open(NR_GLOBAL_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def journalctl_last_health():
    try:
        r = subprocess.run(
            ["journalctl", "-t", "terrarium-health",
             "--since", "10 min ago", "--no-pager"],
            capture_output=True, text=True, timeout=10
        )
        return r.stdout
    except Exception:
        return ""


def list_timers_terrarium():
    try:
        r = subprocess.run(
            ["systemctl", "list-timers", "--all", "--no-pager"],
            capture_output=True, text=True, timeout=5
        )
        out = []
        for line in r.stdout.splitlines():
            low = line.lower()
            if any(k in low for k in ("experiment", "outlet", "light-curve",
                                       "terrarium", "mister", "sd-backup")):
                out.append(line)
        return out
    except Exception:
        return []


def due_flags():
    flags = []
    base = "/home/pi/.claude"
    try:
        for n in os.listdir(base):
            if n.endswith("-due") and n.startswith("."):
                flags.append(n)
    except Exception:
        pass
    return flags


def section1_envelope():
    out = ["## 1/5 — Operating envelope (current)\n"]
    out.append("| Metric | Reading | Status |")
    out.append("|---|---|---|")

    t, _   = influx_last("local_temperature")
    h, _   = influx_last("local_humidity")
    vpd, _ = influx_last("vpd")
    fs, _  = influx_last("fan_speed")
    pwr, _ = influx_last("power_consumption")
    tnk, _ = influx_last("water_level_local")
    g = nr_globals()
    p = g.get("payload", {})
    tgt_t = p.get("target_temp")
    tgt_h = p.get("target_humi")
    frz   = p.get("freezer_status")
    lgt   = p.get("light_status")
    mst   = p.get("mister_status")
    room_t = p.get("room_temperature")
    room_h = p.get("room_humidity")
    room_w = p.get("room_wbt")
    pid_m  = p.get("pid_control_mode")

    if t is not None:
        if t < 24:    regime = "Normal (T<24°C) — H-PID"
        elif t < 25:  regime = "Warm (24-25°C) — T-PID active"
        else:         regime = "Hot (≥25°C) — H-PID + freezer"
    else:
        regime = "unknown"

    if t is not None:
        out.append(f"| Local temp | **{t:.2f}°C** | {regime} |")
    else:
        out.append("| Local temp | n/a | — |")
    if h is not None and tgt_h is not None:
        diff = h - tgt_h
        sign = "+" if diff >= 0 else ""
        out.append(f"| Local humidity | **{h:.1f}%** | Target {tgt_h}% ({sign}{diff:.1f} pp) |")
    else:
        out.append(f"| Local humidity | {h} | Target {tgt_h} |")
    out.append(f"| Target temp (control) | {tgt_t}°C | PID mode = {pid_m} |")
    if vpd is not None:
        zone = ("wet (<0.4)" if vpd < 0.4 else
                "comfort (0.4–0.8)" if vpd < 0.8 else
                "dry (>0.8)")
        out.append(f"| VPD | {vpd:.2f} kPa | {zone} |")
    else:
        out.append("| VPD | n/a | — |")
    out.append(f"| Room | {room_t}°C / {room_h}% / WBT {room_w}°C | Genoa indoor |")
    if tnk is not None:
        flag = "low" if tnk < 15 else "OK"
        out.append(f"| Water tank | {tnk}% | {flag} |")
    else:
        out.append("| Water tank | n/a | — |")
    if pwr is not None:
        out.append(f"| Power draw | {pwr:.0f} W | from Meross MSS310 |")
    else:
        out.append("| Power draw | n/a | — |")
    out.append(f"| Fan speed (PID) | {fs} | per-pin in section 2 |")
    out.append(f"| Freezer / Light / Mister | {frz} / {lgt} / {mst} | — |")
    return "\n".join(out)


def section2_stack():
    out = ["## 2/5 — Stack health\n"]
    out.append("| Layer | State |")
    out.append("|---|---|")

    services = ["nodered", "influxdb", "grafana-server",
                "meross-daemon", "conditions-server", "arduino-watchdog"]
    states = {s: systemctl_active(s) for s in services}
    svc_summary = ", ".join(f"{s}={st}" for s, st in states.items())
    all_ok = all(st == "active" for st in states.values())
    out.append(f"| Services | {'all `active`' if all_ok else svc_summary} |")

    hj = journalctl_last_health()
    latest_lines = [l for l in hj.strip().splitlines()
                    if "🟢" in l or "🟡" in l or "🔴" in l]
    if latest_lines:
        for line in latest_lines[-9:]:
            parts = line.split(":", 3)
            msg = parts[-1].strip() if len(parts) >= 4 else line
            out.append(f"| terrarium-health | {msg} |")

    pwm_c, _ = influx_last("fan_pwm_circulation", "24h")
    pwm_f, _ = influx_last("fan_pwm_freezer", "24h")
    pwm_o, _ = influx_last("fan_pwm_outlet", "24h")
    pwm_i, _ = influx_last("fan_pwm_impeller", "24h")
    out.append(f"| Fan PWMs (last RBE) | circ:{pwm_c} frz:{pwm_f} out:{pwm_o} imp:{pwm_i} |")

    conn_ok, _ = influx_last("connectivity_ok")
    dns_ms, _  = influx_last("connectivity_dns_ms")
    out.append(f"| Connectivity | ok={conn_ok}, DNS {dns_ms} ms |")

    nw = "n/a"
    try:
        with open("/var/lib/net-watchdog/state") as f:
            nw = f.read().strip()
    except Exception:
        pass
    out.append(f"| Net-watchdog state | `{nw}` |")

    led_msg = "n/a"
    try:
        with open("/tmp/led-transient-rate.flag") as f:
            d = json.load(f)
            led_msg = f"date={d.get('date')}, count={d.get('count')}, last_peak={d.get('last_peak')}W"
    except Exception:
        pass
    out.append(f"| LED transient counter | {led_msg} |")

    cnt = influx_count("local_temperature", "1h")
    out.append(f"| Influx ingest | {cnt} samples/hr (target ~60) |")

    mist_n = influx_count("mist_event", "12h")
    out.append(f"| Mist events (12h) | {mist_n} |")

    disk = "n/a"
    try:
        df = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        df_line = df.stdout.splitlines()[-1].split()
        disk = f"{df_line[2]} / {df_line[1]} ({df_line[4]})"
    except Exception:
        pass
    ram = "n/a"
    try:
        free = subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=5)
        mem_line = [l for l in free.stdout.splitlines() if l.startswith("Mem:")]
        if mem_line:
            parts = mem_line[0].split()
            ram = f"{parts[2]} / {parts[1]} ({parts[5]} cache)"
    except Exception:
        pass
    out.append(f"| Disk | {disk} |")
    out.append(f"| RAM | {ram} |")
    return "\n".join(out)


def section3_pending():
    out = ["## 3/5 — Pending checkpoints\n"]
    timers = list_timers_terrarium()
    if timers:
        out.append("**Active terrarium-related timers:**\n")
        out.append("```")
        for line in timers[:8]:
            out.append(line)
        out.append("```\n")
    else:
        out.append("**Active timers:** none.\n")

    flags = due_flags()
    if flags:
        out.append("**🟡 Surface-now flags present:**")
        for f in flags:
            out.append(f"- `{f}`")
    else:
        out.append("**Surface-now flags:** none.")
    return "\n".join(out)


def section4_recent():
    out = ["## 4/5 — Recent activity (last 12h)\n"]

    r = influx_query("SELECT count(*) FROM freezer_status WHERE value=1 AND time > now() - 12h")
    try:
        on_samples = r["results"][0]["series"][0]["values"][0][1] or 0
    except (KeyError, IndexError):
        on_samples = 0

    r2 = influx_query("SELECT difference(last(value)) FROM freezer_status WHERE time > now() - 12h GROUP BY time(1m) fill(previous)")
    cycles = 0
    try:
        for row in r2["results"][0]["series"][0]["values"]:
            if row[1] == 1:
                cycles += 1
    except (KeyError, IndexError):
        pass
    on_hours = on_samples / 60.0
    out.append(f"- Freezer: ~{on_hours:.1f}h ON, {cycles} cycles starting (12h)")

    mist_n = influx_count("mist_event", "12h")
    out.append(f"- Mist events fired: {mist_n}")

    rt = influx_query("SELECT min(value), max(value) FROM local_temperature WHERE time > now() - 12h")
    rh = influx_query("SELECT min(value), max(value) FROM local_humidity WHERE time > now() - 12h")
    try:
        tmin, tmax = rt["results"][0]["series"][0]["values"][0][1:3]
        out.append(f"- Temp range: {tmin:.2f}°C → {tmax:.2f}°C")
    except (KeyError, IndexError):
        pass
    try:
        hmin, hmax = rh["results"][0]["series"][0]["values"][0][1:3]
        out.append(f"- Humi range: {hmin:.1f}% → {hmax:.1f}%")
    except (KeyError, IndexError):
        pass

    rp = influx_query("SELECT mean(value), max(value) FROM power_consumption WHERE time > now() - 12h")
    try:
        pavg, ppeak = rp["results"][0]["series"][0]["values"][0][1:3]
        out.append(f"- Power: avg {pavg:.0f} W, peak {ppeak:.0f} W")
    except (KeyError, IndexError):
        pass

    try:
        r = subprocess.run(
            ["journalctl", "-t", "terrarium-health", "--since", "12 hours ago", "--no-pager"],
            capture_output=True, text=True, timeout=10
        )
        yellow = sum(1 for l in r.stdout.splitlines() if "🟡" in l)
        red    = sum(1 for l in r.stdout.splitlines() if "🔴" in l)
        out.append(f"- terrarium-health alerts (12h): 🟡 {yellow}, 🔴 {red}")
    except Exception:
        pass

    return "\n".join(out)


def section5_nogo():
    out = ["## 5/5 — No-go signals\n"]
    hj = journalctl_last_health()
    last_block = []
    cur = []
    for line in hj.strip().splitlines():
        if "🌿 Terrarium" in line:
            cur = [line]
        else:
            cur.append(line)
        last_block = cur

    bad = [l for l in last_block if "🟡" in l or "🔴" in l]
    if not bad:
        out.append("Nothing red. All categories green in latest terrarium-health cycle.")
    else:
        out.append("Currently flagged:")
        for line in bad:
            parts = line.split(":", 3)
            msg = parts[-1].strip() if len(parts) >= 4 else line
            out.append(f"- {msg}")
    return "\n".join(out)


SECTIONS = [section1_envelope, section2_stack, section3_pending,
            section4_recent, section5_nogo]


def render_all(html=False):
    md_blocks = [fn() for fn in SECTIONS]
    if not html:
        return "\n\n".join(md_blocks)

    import re
    html_blocks = []
    for md in md_blocks:
        h = md
        h = re.sub(r'^## (.+)$', r'<h2 style="margin:18px 0 6px;color:#2c5e2c">\1</h2>',
                   h, flags=re.M)
        lines = h.split("\n")
        rendered = []
        in_table = False
        for ln in lines:
            if ln.startswith("|") and "|" in ln[1:]:
                cells = [c.strip() for c in ln.strip("|").split("|")]
                if all(set(c) <= set("-:") for c in cells if c):
                    continue
                if not in_table:
                    rendered.append('<table style="border-collapse:collapse;margin:6px 0;font-family:monospace;font-size:13px"><thead><tr>')
                    for c in cells:
                        rendered.append(f'<th style="border:1px solid #ccc;padding:3px 8px;background:#eee;text-align:left">{c}</th>')
                    rendered.append("</tr></thead><tbody>")
                    in_table = True
                else:
                    rendered.append("<tr>")
                    for c in cells:
                        rendered.append(f'<td style="border:1px solid #ccc;padding:3px 8px">{c}</td>')
                    rendered.append("</tr>")
            else:
                if in_table:
                    rendered.append("</tbody></table>")
                    in_table = False
                if ln.strip():
                    rendered.append(f"<div>{ln}</div>")
                else:
                    rendered.append("<br>")
        if in_table:
            rendered.append("</tbody></table>")
        h = "\n".join(rendered)
        h = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', h)
        h = re.sub(r'`([^`]+)`', r'<code style="background:#f0f0f0;padding:1px 4px;border-radius:3px">\1</code>', h)
        html_blocks.append(h)
    body = (
        '<html><body style="font-family:Segoe UI,Helvetica,Arial,sans-serif;'
        'color:#222;line-height:1.4;max-width:780px">'
        + "\n<hr>\n".join(html_blocks)
        + '</body></html>'
    )
    return body


def send_email(html):
    subject = f"🌿 Terrarium Sitrep — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = GMAIL_TO
        plain = render_all(html=False)
        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as s:
            s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"send_email failed: {e}", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--section", type=int, choices=range(1, 6),
                    help="Print only section N (1-5)")
    ap.add_argument("--email", action="store_true", help="Send via Gmail")
    args = ap.parse_args()

    if args.email:
        html = render_all(html=True)
        ok = send_email(html)
        sys.exit(0 if ok else 1)

    if args.section:
        print(SECTIONS[args.section - 1]())
    else:
        print(render_all(html=False))


if __name__ == "__main__":
    main()
