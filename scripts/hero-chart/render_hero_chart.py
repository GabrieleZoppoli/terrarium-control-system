#!/usr/bin/env python3
"""Render the highland hero chart (last 24 h) straight from InfluxDB.

Replaces the Grafana screenshot on the website's highland hero tile.
Cron runs it every minute; the PNG is written atomically to
/home/pi/snapshots/hero-chart.png and served by conditions-server.py at
/highland/hero-chart.png.
"""
import os, tempfile
import json, urllib.request, urllib.parse, datetime as dt
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.dates as md
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Rome")
def q(meas, agg="mean", every="5m"):
    s = f'SELECT {agg}("value") FROM "{meas}" WHERE time > now() - 24h GROUP BY time({every}) fill(previous)'
    u = "http://127.0.0.1:8086/query?" + urllib.parse.urlencode({"db": "highland", "q": s, "epoch": "s"})
    v = json.load(urllib.request.urlopen(u, timeout=20))["results"][0]["series"][0]["values"]
    return [dt.datetime.fromtimestamp(t, TZ) for t, x in v if x is not None], [x for t, x in v if x is not None]
T, H, V = q("local_temperature"), q("local_humidity"), q("vpd")
L, F, M = q("light_status", "max"), q("freezer_status", "max", "2m"), q("mister_status", "max", "1m")
TT, TH = q("target_temperature_computed"), q("target_humidity_computed")
BG, FG, MUTED, GRID = "#111217", "#e8e8ea", "#8a8d98", "#24262d"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": FG, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED})
fig = plt.figure(figsize=(16, 12), dpi=100, facecolor=BG)
gs = fig.add_gridspec(5, 1, height_ratios=[3.2, 3.2, 2.4, .55, .55], hspace=.62, left=.06, right=.97, top=.84, bottom=.04)
nights = []
on = None
for t, x in zip(*L):
    if x < .5 and on is None: on = t
    if x >= .5 and on is not None: nights.append((on, t)); on = None
if on is not None: nights.append((on, L[0][-1]))
def panel(ax, xy, color, unit, fmt, title, target=None):
    ax.set_facecolor(BG)
    for a, b in nights: ax.axvspan(a, b, color="#1b2236", zorder=0, lw=0)
    if target: ax.plot(*target, color=color, lw=1.2, ls=(0, (4, 4)), alpha=.55, zorder=2)
    ax.plot(*xy, color=color, lw=2.2, zorder=3)
    ax.fill_between(*xy, min(xy[1]) - (max(xy[1]) - min(xy[1])) * .15, color=color, alpha=.10, zorder=1)
    ax.grid(axis="y", color=GRID, lw=.8); ax.tick_params(labelsize=13, length=0)
    for s in ax.spines.values(): s.set_visible(False)
    ax.xaxis.set_major_locator(md.HourLocator(byhour=range(0, 24, 4), tz=TZ))
    ax.xaxis.set_major_formatter(md.DateFormatter("%H:%M", tz=TZ))
    ax.text(0, 1.07, title, transform=ax.transAxes, fontsize=16, color=MUTED, va="bottom")
    ax.text(1, 1.06, f"{fmt.format(xy[1][-1])} {unit}", transform=ax.transAxes, ha="right", va="bottom",
            fontsize=30, color=color, fontweight="bold")
    ax.text(.80, 1.07, f"24 h  {fmt.format(min(xy[1]))} – {fmt.format(max(xy[1]))}", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=13, color=MUTED)
    ax.margins(x=0)
panel(fig.add_subplot(gs[0]), T, "#ff9f5a", "°C", "{:.1f}", "Temperature", TT)
panel(fig.add_subplot(gs[1]), H, "#5ab4ff", "%", "{:.0f}", "Humidity", TH)
panel(fig.add_subplot(gs[2]), V, "#7ddc8c", "kPa", "{:.2f}", "VPD")
for i, (xy, color, name) in enumerate([(F, "#4fd1e8", "Freezer"), (M, "#b9f08a", "Mister")]):
    ax = fig.add_subplot(gs[3 + i]); ax.set_facecolor(BG)
    for a, b in nights: ax.axvspan(a, b, color="#1b2236", lw=0)
    ax.fill_between(*xy, 0, step="post", color=color, alpha=.85, lw=0)
    ax.set_ylim(0, 1.05); ax.set_yticks([]); ax.margins(x=0)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_xticks([]); ax.text(-.005, .5, name, transform=ax.transAxes, ha="right", va="center", fontsize=13, color=MUTED)
fig.text(.06, .945, "RORAIMA", fontsize=30, fontweight="bold", color=FG)
fig.text(.235, .945, "· live", fontsize=30, color="#ff5a5f")
fig.text(.06, .91, "Last 24 h · night shaded · dashed = target", fontsize=14, color=MUTED)
OUT = os.environ.get("HERO_CHART_OUT", "/home/pi/snapshots/hero-chart.png")
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(OUT), suffix=".png")
os.close(fd)
fig.savefig(tmp, facecolor=BG)
os.chmod(tmp, 0o644)
os.replace(tmp, OUT)
