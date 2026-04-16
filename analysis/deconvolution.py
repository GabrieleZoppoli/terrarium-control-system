#!/usr/bin/env python3
"""
Deconvolve fan vs freezer cooling contributions using:
1. Regime analysis (cooling rates by actuator state)
2. Heat-balance regression: dT/dt = f(T_diff, fans, freezer, lights)
"""

import subprocess
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import StringIO

def query_influx(measurement, days=18):
    cmd = f'influx -database highland -execute "SELECT value FROM {measurement} WHERE time > now() - {days}d" -format csv'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    df = pd.read_csv(StringIO(result.stdout))
    if df.empty:
        return pd.DataFrame()
    df['time'] = pd.to_datetime(df['time'].astype(int), unit='ns', utc=True)
    df['time'] = df['time'].dt.tz_convert('Europe/Rome')
    df = df.set_index('time')
    df = df[['value']].rename(columns={'value': measurement})
    return df

def wet_bulb(T, RH):
    return (T * np.arctan(0.151977 * (RH + 8.313659)**0.5)
            + np.arctan(T + RH) - np.arctan(RH - 1.676331)
            + 0.00391838 * RH**1.5 * np.arctan(0.023101 * RH) - 4.686035)

print("Querying data...")
room_t = query_influx('room_temperature')
room_h = query_influx('room_humidity')
local_t = query_influx('local_temperature')
local_h = query_influx('local_humidity')
freezer = query_influx('freezer_status')
light = query_influx('light_status')

# Resample to 5-min
freq = '5min'
df = pd.concat([
    room_t.resample(freq).mean(),
    room_h.resample(freq).mean(),
    local_t.resample(freq).mean(),
    local_h.resample(freq).mean(),
    freezer.resample(freq).mean(),
    light.resample(freq).mean(),
], axis=1)
df.columns = ['room_t', 'room_h', 'local_t', 'local_h', 'freezer', 'light']
df = df.dropna(subset=['room_t', 'local_t'])

# Derived variables
df['room_wb'] = wet_bulb(df['room_t'], df['room_h'])
df['t_diff_room'] = df['room_t'] - df['local_t']       # room-to-terrarium gradient
df['t_above_wb'] = df['local_t'] - df['room_wb']        # how far above wet-bulb
df['fans_on'] = (df.index.hour >= 5).astype(float)       # schedule-based
df['freezer_on'] = (df['freezer'] > 0.5).astype(float)
df['light_on'] = (df['light'] > 0.5).astype(float)

# Calculate dT/dt (°C per hour) using centered difference
df['dT_dt'] = df['local_t'].diff(periods=2) / (10/60)  # 2 steps × 5min = 10min → per hour
df['dT_dt'] = df['dT_dt'].shift(-1)  # center it

# Remove outliers in dT/dt (sensor glitches)
df = df[df['dT_dt'].abs() < 10]

# Define regimes
df['regime'] = 'transition'
df.loc[(df['fans_on'] == 1) & (df['freezer_on'] == 0) & (df['light_on'] == 1), 'regime'] = 'fans+lights'
df.loc[(df['fans_on'] == 1) & (df['freezer_on'] == 0) & (df['light_on'] == 0), 'regime'] = 'fans_only'
df.loc[(df['fans_on'] == 1) & (df['freezer_on'] == 1), 'regime'] = 'fans+freezer'
df.loc[(df['fans_on'] == 0) & (df['freezer_on'] == 1), 'regime'] = 'freezer_only'
df.loc[(df['fans_on'] == 0) & (df['freezer_on'] == 0), 'regime'] = 'nothing'

print(f"\nMerged: {len(df)} data points")
print(f"\n{'='*70}")
print("REGIME ANALYSIS")
print(f"{'='*70}")
print(f"\n{'Regime':<16} {'N':>5} {'dT/dt':>8} {'Terr_T':>8} {'T-Twb':>7} {'T_diff':>7} {'Hours'}")
print(f"{'-'*16} {'-'*5} {'-'*8} {'-'*8} {'-'*7} {'-'*7} {'-'*20}")

for regime in ['fans+lights', 'fans_only', 'fans+freezer', 'freezer_only', 'nothing', 'transition']:
    sub = df[df['regime'] == regime]
    if len(sub) > 10:
        # typical hours
        hours = sub.index.hour.value_counts().sort_index()
        hr_range = f"{hours.index.min():02d}-{hours.index.max():02d}"
        print(f"{regime:<16} {len(sub):5d} {sub['dT_dt'].mean():+8.3f} {sub['local_t'].mean():8.2f} "
              f"{sub['t_above_wb'].mean():+7.2f} {sub['t_diff_room'].mean():+7.2f} {hr_range}")

# ============================================================
# REGRESSION: Heat balance model
# dT/dt = a0 + a1*(T_room - T_terr) + a2*fans + a3*freezer + a4*lights
#        + a5*fans*freezer (interaction)
# ============================================================
print(f"\n{'='*70}")
print("HEAT BALANCE REGRESSION")
print(f"{'='*70}")

from numpy.linalg import lstsq

valid = df.dropna(subset=['dT_dt', 't_diff_room'])

X = np.column_stack([
    np.ones(len(valid)),              # intercept
    valid['t_diff_room'].values,      # passive heat exchange
    valid['fans_on'].values,          # fan cooling effect
    valid['freezer_on'].values,       # freezer cooling effect
    valid['light_on'].values,         # light heating effect
    valid['fans_on'].values * valid['freezer_on'].values,  # interaction
])

y = valid['dT_dt'].values

coeffs, residuals, rank, sv = lstsq(X, y, rcond=None)
y_pred = X @ coeffs
ss_res = np.sum((y - y_pred)**2)
ss_tot = np.sum((y - y.mean())**2)
r_squared = 1 - ss_res / ss_tot

labels = ['Intercept', 'T_diff (room-terr)', 'Fans ON', 'Freezer ON', 'Lights ON', 'Fans×Freezer']
print(f"\nModel: dT/dt (°C/hr) = sum of effects")
print(f"R² = {r_squared:.4f}  (N = {len(valid)})")
print(f"\n{'Variable':<20} {'Coeff':>8} {'Unit':<20} Interpretation")
print(f"{'-'*20} {'-'*8} {'-'*20} {'-'*40}")
for label, c in zip(labels, coeffs):
    if label == 'Intercept':
        print(f"{label:<20} {c:+8.4f} {'°C/hr':<20} baseline drift")
    elif label == 'T_diff (room-terr)':
        print(f"{label:<20} {c:+8.4f} {'°C/hr per °C diff':<20} passive heat exchange rate")
    elif label == 'Fans ON':
        print(f"{label:<20} {c:+8.4f} {'°C/hr':<20} fan evaporative cooling")
    elif label == 'Freezer ON':
        print(f"{label:<20} {c:+8.4f} {'°C/hr':<20} mechanical cooling")
    elif label == 'Lights ON':
        print(f"{label:<20} {c:+8.4f} {'°C/hr':<20} radiative heating")
    elif label == 'Fans×Freezer':
        print(f"{label:<20} {c:+8.4f} {'°C/hr':<20} interaction (fans counteract freezer?)")

# Predicted steady-state effects
print(f"\n--- Implied cooling contributions (at mean conditions) ---")
mean_tdiff = valid['t_diff_room'].mean()
print(f"Mean room-terrarium gradient: {mean_tdiff:+.2f}°C")
print(f"Passive heat exchange contribution: {coeffs[1]*mean_tdiff:+.3f} °C/hr")
print(f"Fan-only cooling: {coeffs[2]:+.3f} °C/hr")
print(f"Freezer-only cooling: {coeffs[3]:+.3f} °C/hr")
print(f"Lights heating: {coeffs[4]:+.3f} °C/hr")
print(f"Fan+Freezer interaction: {coeffs[5]:+.3f} °C/hr")
print(f"Net freezer effect with fans running: {coeffs[3]+coeffs[5]:+.3f} °C/hr")
print(f"Net freezer effect without fans: {coeffs[3]:+.3f} °C/hr")

# ============================================================
# Extended model with t_above_wb interaction
# ============================================================
print(f"\n{'='*70}")
print("EXTENDED MODEL: Fan effectiveness vs wet-bulb distance")
print(f"{'='*70}")

X2 = np.column_stack([
    np.ones(len(valid)),
    valid['t_diff_room'].values,
    valid['fans_on'].values,
    valid['freezer_on'].values,
    valid['light_on'].values,
    valid['fans_on'].values * valid['freezer_on'].values,
    valid['fans_on'].values * valid['t_above_wb'].values,  # fan effect depends on distance from wb
])

coeffs2, _, _, _ = lstsq(X2, y, rcond=None)
y_pred2 = X2 @ coeffs2
r2_ext = 1 - np.sum((y - y_pred2)**2) / ss_tot

labels2 = labels + ['Fans × T_above_wb']
print(f"\nR² = {r2_ext:.4f}  (vs {r_squared:.4f} base model)")
print(f"\n{'Variable':<20} {'Coeff':>8}")
print(f"{'-'*20} {'-'*8}")
for label, c in zip(labels2, coeffs2):
    print(f"{label:<20} {c:+8.4f}")

print(f"\nInterpretation of Fans × T_above_wb: {coeffs2[6]:+.4f}")
if coeffs2[6] < 0:
    print("  → Fans cool MORE when terrarium is further above wet-bulb (more evaporative headroom)")
    print("  → Fans cool LESS (or warm) when terrarium is near/below wet-bulb")
else:
    print("  → Fans warm MORE when terrarium is above wet-bulb")

wb_zero = -coeffs2[2] / coeffs2[6] if abs(coeffs2[6]) > 0.001 else float('inf')
print(f"  → Fan cooling goes to zero when T_above_wb ≈ {wb_zero:.1f}°C")

# ============================================================
# PLOTS
# ============================================================

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Deconvolving Fan vs Freezer Cooling Effects', fontsize=14, fontweight='bold')

# Plot 1: dT/dt by regime (box plot style)
ax = axes[0, 0]
regimes_order = ['fans+lights', 'fans_only', 'fans+freezer', 'freezer_only', 'nothing']
regime_labels = ['Fans+Lights\n(day)', 'Fans only\n(dawn/dusk)', 'Fans+Freezer\n(evening)',
                 'Freezer only\n(night)', 'Nothing\n(rare)']
regime_data = [df[df['regime'] == r]['dT_dt'].dropna() for r in regimes_order]
regime_data_filtered = [(d, l) for d, l in zip(regime_data, regime_labels) if len(d) > 10]
if regime_data_filtered:
    data_list, label_list = zip(*regime_data_filtered)
    bp = ax.boxplot(data_list, labels=label_list, patch_artist=True, showfliers=False,
                    medianprops=dict(color='black', linewidth=2))
    colors_box = ['#FFD700', '#FFA500', '#4169E1', '#00CED1', '#808080']
    for patch, color in zip(bp['boxes'], colors_box[:len(bp['boxes'])]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
ax.axhline(y=0, color='black', linestyle='--', linewidth=0.8)
ax.set_ylabel('dT/dt (°C/hr)')
ax.set_title('Temperature change rate by regime')
ax.grid(True, alpha=0.3, axis='y')

# Plot 2: dT/dt vs T_above_wb, colored by regime
ax = axes[0, 1]
for regime, color, marker in [('fans+lights', '#FFD700', 'o'), ('fans+freezer', '#4169E1', 's'),
                                ('freezer_only', '#00CED1', '^'), ('fans_only', '#FFA500', 'D')]:
    sub = df[df['regime'] == regime].dropna(subset=['dT_dt'])
    if len(sub) > 10:
        ax.scatter(sub['t_above_wb'], sub['dT_dt'], c=color, s=8, alpha=0.3,
                   label=regime, marker=marker)
ax.axhline(y=0, color='black', linestyle='--', linewidth=0.8)
ax.axvline(x=0, color='red', linestyle='--', linewidth=0.8, alpha=0.5, label='T = wet-bulb')
ax.set_xlabel('Terrarium T − Room Twb (°C)')
ax.set_ylabel('dT/dt (°C/hr)')
ax.set_title('Cooling rate vs distance from wet-bulb')
ax.legend(fontsize=8, markerscale=2)
ax.grid(True, alpha=0.3)
ax.set_xlim(-5, 7)
ax.set_ylim(-4, 4)

# Plot 3: Hourly mean dT/dt by regime components
ax = axes[1, 0]
hourly_dt = df.groupby(df.index.hour).agg({
    'dT_dt': 'mean',
    'fans_on': 'mean',
    'freezer_on': 'mean',
    'light_on': 'mean',
    't_diff_room': 'mean',
    't_above_wb': 'mean',
}).dropna()

# Decompose using regression coefficients
h = hourly_dt.index
passive = coeffs[1] * hourly_dt['t_diff_room']
fan_eff = coeffs[2] * hourly_dt['fans_on']
freezer_eff = coeffs[3] * hourly_dt['freezer_on']
light_eff = coeffs[4] * hourly_dt['light_on']
interaction = coeffs[5] * hourly_dt['fans_on'] * hourly_dt['freezer_on']

ax.bar(h, passive, label=f'Passive exchange', color='gray', alpha=0.6)
ax.bar(h, fan_eff, bottom=passive, label=f'Fans ({coeffs[2]:+.2f}°C/hr)', color='orange', alpha=0.6)
ax.bar(h, freezer_eff, bottom=passive+fan_eff, label=f'Freezer ({coeffs[3]:+.2f}°C/hr)', color='cyan', alpha=0.6)
ax.bar(h, light_eff, bottom=passive+fan_eff+freezer_eff, label=f'Lights ({coeffs[4]:+.2f}°C/hr)', color='gold', alpha=0.6)
ax.bar(h, interaction, bottom=passive+fan_eff+freezer_eff+light_eff,
       label=f'Fan×Freezer ({coeffs[5]:+.2f}°C/hr)', color='red', alpha=0.4)
ax.plot(h, hourly_dt['dT_dt'], 'k-o', markersize=4, linewidth=2, label='Actual dT/dt')
ax.axhline(y=0, color='black', linestyle='--', linewidth=0.8)
ax.set_xlabel('Hour of day')
ax.set_ylabel('dT/dt (°C/hr)')
ax.set_title('Hourly decomposition of heating/cooling')
ax.legend(fontsize=7, loc='upper left')
ax.set_xticks(range(0, 24))
ax.set_xlim(-0.5, 23.5)
ax.grid(True, alpha=0.3, axis='y')

# Plot 4: Regression model coefficients as bar chart
ax = axes[1, 1]
effect_labels = ['Passive\nheat exch.', 'Fans', 'Freezer', 'Lights', 'Fan×Freezer\ninteraction']
effect_values = [coeffs[1] * mean_tdiff, coeffs[2], coeffs[3], coeffs[4], coeffs[5]]
effect_colors = ['gray', 'orange', 'cyan', 'gold', 'red']
bars = ax.bar(effect_labels, effect_values, color=effect_colors, alpha=0.7, edgecolor='black')
ax.axhline(y=0, color='black', linewidth=0.8)
for bar, val in zip(bars, effect_values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02 * np.sign(val),
            f'{val:+.3f}', ha='center', va='bottom' if val > 0 else 'top', fontsize=10, fontweight='bold')
ax.set_ylabel('Effect on dT/dt (°C/hr)')
ax.set_title(f'Regression coefficients (R²={r_squared:.3f})')
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('/home/pi/terrarium-analysis/deconvolution.png', dpi=150, bbox_inches='tight')
print(f"\nPlot saved to /home/pi/terrarium-analysis/deconvolution.png")
