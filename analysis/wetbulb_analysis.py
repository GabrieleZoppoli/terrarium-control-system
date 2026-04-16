#!/usr/bin/env python3
"""
Wet-bulb temperature analysis: compare room wet-bulb to terrarium temperature
in relation to fan and freezer state.
"""

import subprocess
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# --- Wet-bulb calculation (Stull 2011 approximation) ---
def wet_bulb(T, RH):
    """Calculate wet-bulb temperature from dry-bulb T (°C) and RH (%).
    Stull (2011), accurate to ~0.3°C for typical conditions."""
    return (T * np.arctan(0.151977 * (RH + 8.313659)**0.5)
            + np.arctan(T + RH)
            - np.arctan(RH - 1.676331)
            + 0.00391838 * RH**1.5 * np.arctan(0.023101 * RH)
            - 4.686035)

# --- Query InfluxDB ---
def query_influx(measurement, days=18):
    """Query a measurement from InfluxDB, return DataFrame with time index."""
    cmd = f'influx -database highland -execute "SELECT value FROM {measurement} WHERE time > now() - {days}d" -format csv'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    from io import StringIO
    df = pd.read_csv(StringIO(result.stdout))
    if df.empty:
        print(f"WARNING: No data for {measurement}")
        return pd.DataFrame()
    # Time is in nanoseconds
    df['time'] = pd.to_datetime(df['time'].astype(int), unit='ns', utc=True)
    df['time'] = df['time'].dt.tz_convert('Europe/Rome')
    df = df.set_index('time')
    df = df[['value']].rename(columns={'value': measurement})
    return df

print("Querying InfluxDB...")
room_t = query_influx('room_temperature')
room_h = query_influx('room_humidity')
local_t = query_influx('local_temperature')
local_h = query_influx('local_humidity')
fan = query_influx('fan_speed')
freezer = query_influx('freezer_status')

print(f"Room T: {len(room_t)} points, Local T: {len(local_t)} points")
print(f"Fan: {len(fan)} points, Freezer: {len(freezer)} points")

# --- Resample all to 5-minute intervals for alignment ---
freq = '5min'
room_t_r = room_t.resample(freq).mean()
room_h_r = room_h.resample(freq).mean()
local_t_r = local_t.resample(freq).mean()
local_h_r = local_h.resample(freq).mean()
fan_r = fan.resample(freq).mean()
freezer_r = freezer.resample(freq).mean()

# Merge everything
df = pd.concat([room_t_r, room_h_r, local_t_r, local_h_r, fan_r, freezer_r], axis=1)
df.columns = ['room_t', 'room_h', 'local_t', 'local_h', 'fan_speed', 'freezer']
df = df.dropna(subset=['room_t', 'room_h', 'local_t'])

print(f"Merged: {len(df)} aligned data points from {df.index.min()} to {df.index.max()}")

# --- Calculate wet-bulb ---
df['room_wb'] = wet_bulb(df['room_t'], df['room_h'])
df['local_wb'] = wet_bulb(df['local_t'], df['local_h'])
df['t_minus_wb'] = df['local_t'] - df['room_wb']  # terrarium T minus room wet-bulb

# Fan state: use actual schedule (05:00-00:00 = ON, 00:00-05:00 = OFF)
# Note: fan_speed global is STALE at night (keeps last PID value), so we use schedule
df['fans_on'] = (df.index.hour >= 5)  # 05:00-23:59 = True, 00:00-04:59 = False
# Freezer: 1 = on
df['freezer_on'] = df['freezer'] > 0.5

df['hour'] = df.index.hour + df.index.minute / 60.0

print(f"\n--- Summary Statistics ---")
print(f"Room T: {df['room_t'].mean():.1f} ± {df['room_t'].std():.1f}°C")
print(f"Room RH: {df['room_h'].mean():.1f} ± {df['room_h'].std():.1f}%")
print(f"Room wet-bulb: {df['room_wb'].mean():.1f} ± {df['room_wb'].std():.1f}°C")
print(f"Terrarium T: {df['local_t'].mean():.1f} ± {df['local_t'].std():.1f}°C")
print(f"Terrarium minus room wet-bulb: {df['t_minus_wb'].mean():.1f} ± {df['t_minus_wb'].std():.1f}°C")

# --- Stats by fan/freezer state ---
for label, mask in [("Fans ON", df['fans_on']), ("Fans OFF", ~df['fans_on'])]:
    sub = df[mask]
    if len(sub) > 0:
        print(f"\n{label} ({len(sub)} points):")
        print(f"  Terrarium T: {sub['local_t'].mean():.2f}°C")
        print(f"  Room wet-bulb: {sub['room_wb'].mean():.2f}°C")
        print(f"  T - Twb: {sub['t_minus_wb'].mean():.2f}°C")
        print(f"  Terrarium RH: {sub['local_h'].mean():.1f}%")

for label, mask in [("Freezer ON", df['freezer_on']), ("Freezer OFF", ~df['freezer_on'])]:
    sub = df[mask]
    if len(sub) > 0:
        print(f"\n{label} ({len(sub)} points):")
        print(f"  Terrarium T: {sub['local_t'].mean():.2f}°C")
        print(f"  Room wet-bulb: {sub['room_wb'].mean():.2f}°C")
        print(f"  T - Twb: {sub['t_minus_wb'].mean():.2f}°C")

# --- Hourly profile ---
hourly = df.groupby(df.index.hour).agg({
    'local_t': 'mean',
    'room_t': 'mean',
    'room_wb': 'mean',
    'room_h': 'mean',
    'local_h': 'mean',
    't_minus_wb': 'mean',
    'fans_on': 'mean',
    'freezer_on': 'mean'
})

print(f"\n--- Hourly Profile ---")
print(f"{'Hour':>4} {'Terr_T':>7} {'Room_T':>7} {'Room_WB':>8} {'T-Twb':>6} {'Fans%':>6} {'Frzr%':>6} {'Terr_H':>7}")
for h in range(24):
    if h in hourly.index:
        r = hourly.loc[h]
        print(f"{h:4d} {r['local_t']:7.2f} {r['room_t']:7.2f} {r['room_wb']:8.2f} {r['t_minus_wb']:6.2f} {r['fans_on']*100:5.0f}% {r['freezer_on']*100:5.0f}% {r['local_h']:6.1f}%")

# ============================
# PLOTS
# ============================

# --- Figure 1: Time series (last 5 days) ---
recent = df[df.index > df.index.max() - timedelta(days=5)].copy()
recent.index = recent.index.tz_localize(None)

fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
fig1.suptitle('Wet-Bulb Temperature Analysis: Last 5 Days', fontsize=14, fontweight='bold')

ax1.plot(recent.index, recent['room_t'], color='green', alpha=0.6, linewidth=0.8, label='Room T (dry-bulb)')
ax1.plot(recent.index, recent['room_wb'], color='blue', alpha=0.8, linewidth=1.2, label='Room T (wet-bulb)')
ax1.plot(recent.index, recent['local_t'], color='red', alpha=0.8, linewidth=1.0, label='Terrarium T')
for day in pd.date_range(recent.index.min().date(), recent.index.max().date()):
    ax1.axvspan(day, day + timedelta(hours=5), alpha=0.08, color='navy')
ax1.set_ylabel('Temperature (°C)')
ax1.legend(loc='upper right', fontsize=9)
ax1.set_title('Room dry-bulb, wet-bulb, and terrarium temperature')
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax1.xaxis.set_minor_formatter(mdates.DateFormatter('%H:%M'))
ax1.xaxis.set_major_locator(mdates.DayLocator())
ax1.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18]))

colors = ['steelblue' if f else 'salmon' for f in recent['fans_on']]
ax2.scatter(recent.index, recent['t_minus_wb'], c=colors, s=3, alpha=0.5)
ax2.axhline(y=0, color='black', linestyle='--', linewidth=1, label='T = Room wet-bulb')
for day in pd.date_range(recent.index.min().date(), recent.index.max().date()):
    ax2.axvspan(day, day + timedelta(hours=5), alpha=0.08, color='navy')
ax2.set_ylabel('Terrarium T − Room Twb (°C)')
ax2.set_title('Distance from wet-bulb limit (blue=fans ON, red=fans OFF, shaded=night 00-05)')
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax2.xaxis.set_major_locator(mdates.DayLocator())

fig1.tight_layout()
fig1.savefig('/home/pi/terrarium-analysis/wetbulb_timeseries.png', dpi=150, bbox_inches='tight')
print(f"\nTime series saved to /home/pi/terrarium-analysis/wetbulb_timeseries.png")

# --- Figure 2: Hourly profiles ---
fig2, (ax3, ax4) = plt.subplots(2, 1, figsize=(14, 10))
fig2.suptitle('Wet-Bulb Temperature Analysis: Mean Hourly Profiles', fontsize=14, fontweight='bold')

hours = hourly.index
ax3.plot(hours, hourly['room_t'], 'g-o', markersize=5, label='Room T (dry-bulb)')
ax3.plot(hours, hourly['room_wb'], 'b-s', markersize=5, label='Room T (wet-bulb)')
ax3.plot(hours, hourly['local_t'], 'r-^', markersize=5, label='Terrarium T')
ax3.axvspan(0, 5, alpha=0.08, color='navy', label='Night (fans OFF)')
ax3.set_ylabel('Temperature (°C)')
ax3.set_title('Mean hourly temperature profile')
ax3.legend(loc='upper right', fontsize=9)
ax3.set_xticks(range(0, 24))
ax3.set_xlim(-0.5, 23.5)
ax3.grid(True, alpha=0.3)

ax4b = ax4.twinx()
bars = ax4.bar(hours, hourly['t_minus_wb'],
               color=['salmon' if h < 5 else 'steelblue' for h in hours],
               alpha=0.7, label='T − Room Twb')
ax4.axhline(y=0, color='black', linestyle='--', linewidth=1)
ax4b.plot(hours, hourly['fans_on'] * 100, 'orange', linewidth=2.5, marker='o', markersize=4, label='Fans ON %')
ax4b.plot(hours, hourly['freezer_on'] * 100, 'cyan', linewidth=2.5, linestyle='--', marker='s', markersize=4, label='Freezer ON %')
ax4.axvspan(0, 5, alpha=0.06, color='navy')
ax4.set_xlabel('Hour of day')
ax4.set_ylabel('T − Room Twb (°C)')
ax4b.set_ylabel('Actuator active (%)')
ax4b.set_ylim(-5, 110)
ax4.set_title('Distance from wet-bulb vs fan/freezer activity')
ax4.set_xticks(range(0, 24))
ax4.set_xlim(-0.5, 23.5)
ax4.legend(loc='upper left', fontsize=9)
ax4b.legend(loc='right', fontsize=9)
ax4.grid(True, alpha=0.3)

fig2.tight_layout()
fig2.savefig('/home/pi/terrarium-analysis/wetbulb_hourly.png', dpi=150, bbox_inches='tight')
print(f"Hourly profiles saved to /home/pi/terrarium-analysis/wetbulb_hourly.png")

# --- Scatter: T-Twb vs fan speed ---
fig2, axes2 = plt.subplots(1, 2, figsize=(14, 6))

# Night hours only (22:00-06:00) - the transition period
night = df[(df['hour'] >= 22) | (df['hour'] <= 6)]

ax = axes2[0]
sc = ax.scatter(night['fan_speed'], night['t_minus_wb'], c=night['hour'],
                cmap='twilight', s=8, alpha=0.4)
plt.colorbar(sc, ax=ax, label='Hour of day')
ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
ax.set_xlabel('Fan speed (PWM)')
ax.set_ylabel('Terrarium T - Room Twb (°C)')
ax.set_title('Night hours (22:00-06:00): Fan speed vs distance from wet-bulb')
ax.grid(True, alpha=0.3)

# Freezer effectiveness vs T-Twb
freezer_on = df[df['freezer_on']]
ax = axes2[1]
if len(freezer_on) > 0:
    sc = ax.scatter(freezer_on['t_minus_wb'], freezer_on['local_t'],
                    c=freezer_on['hour'], cmap='twilight', s=8, alpha=0.4)
    plt.colorbar(sc, ax=ax, label='Hour of day')
    ax.axvline(x=0, color='black', linestyle='--', linewidth=1)
    ax.set_xlabel('T - Room Twb (°C) when freezer ON')
    ax.set_ylabel('Terrarium T (°C)')
    ax.set_title('Freezer active: terrarium T vs distance from wet-bulb')
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('/home/pi/terrarium-analysis/wetbulb_scatter.png', dpi=150, bbox_inches='tight')
print(f"Scatter saved to /home/pi/terrarium-analysis/wetbulb_scatter.png")
