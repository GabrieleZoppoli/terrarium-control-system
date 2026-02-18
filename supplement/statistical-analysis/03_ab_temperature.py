#!/usr/bin/env python3
"""
Night A/B experiment: effect of fans on temperature
Night A (even DOY): fans OFF
Night B (odd DOY): outlet+impeller at 80 PWM
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy.stats import ttest_ind, mannwhitneyu
import warnings
warnings.filterwarnings('ignore')

# --- Load data ---
def load_series(name, col_name):
    df = pd.read_csv(f'/home/pi/terrarium-analysis/data/{name}.csv', skiprows=0)
    df.columns = ['_name', 'time', col_name]
    df['time'] = pd.to_numeric(df['time'])
    df = df[['time', col_name]].dropna()
    df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
    return df

series = [
    ('local_humidity', 'humidity'),
    ('local_temperature', 'temp_in'),
    ('room_temperature', 'temp_room'),
    ('room_humidity', 'humi_room'),
    ('fan_speed', 'fan_pwm'),
    ('freezer_status', 'freezer'),
    ('mister_status', 'mister'),
    ('night_test_mode', 'night_mode'),
    ('target_temperature', 'target_temp'),
]

dfs = {}
for filename, colname in series:
    dfs[colname] = load_series(filename, colname)

df = dfs['temp_in']
for colname, other_df in dfs.items():
    if colname == 'temp_in':
        continue
    df = pd.merge_asof(df.sort_values('time'), other_df.sort_values('time'),
                        on='time', tolerance=300_000_000_000)

df = df.dropna()

# Time features
df['hour'] = (df['time'] / 3.6e12) % 24
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
df['daytime'] = ((df['hour'] >= 6.5) & (df['hour'] <= 20.0)).astype(int)
df['timestamp'] = pd.to_datetime(df['time'], unit='ns')

# Night only
df_night = df[df['daytime'] == 0].copy()
df_night['night_B'] = (df_night['night_mode'] > 0.5).astype(int)

# Cooling delta: how much colder is terrarium vs room
df_night['cooling'] = df_night['temp_room'] - df_night['temp_in']

# Night date (00:00-06:30 belongs to previous evening)
df_night['night_date'] = (df_night['timestamp'] - pd.Timedelta(hours=6, minutes=30)).dt.date

print(f"Nighttime observations: {len(df_night)}")
print(f"Night A (fans off): {(df_night['night_B']==0).sum()}")
print(f"Night B (fans=80):  {(df_night['night_B']==1).sum()}")

# ===================================================================
# 1. SIMPLE A/B COMPARISON
# ===================================================================
print(f"\n{'='*70}")
print("1. SIMPLE A/B COMPARISON (all nighttime 5-min observations)")
print('='*70)

for var, label in [('temp_in', 'Terrarium temp (°C)'),
                    ('cooling', 'Cooling delta (room-terr, °C)'),
                    ('temp_room', 'Room temp (°C)'),
                    ('humidity', 'Terrarium humidity (%)'),
                    ('humi_room', 'Room humidity (%)'),
                    ('freezer', 'Freezer duty cycle'),
                    ('fan_pwm', 'Fan PWM (PID output)')]:
    a = df_night.loc[df_night['night_B']==0, var]
    b = df_night.loc[df_night['night_B']==1, var]
    t, p = ttest_ind(b, a, equal_var=False)
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
    print(f"  {label:30s}: A={a.mean():6.2f}  B={b.mean():6.2f}  Δ={b.mean()-a.mean():+.3f}  p={p:.4f} {sig}")

# ===================================================================
# 2. NIGHTLY AGGREGATES
# ===================================================================
print(f"\n{'='*70}")
print("2. NIGHTLY AGGREGATES (one obs per night)")
print('='*70)

nightly = df_night.groupby('night_date').agg({
    'temp_in': 'mean',
    'temp_room': 'mean',
    'humidity': 'mean',
    'humi_room': 'mean',
    'cooling': 'mean',
    'freezer': 'mean',
    'fan_pwm': 'mean',
    'night_B': 'first',
    'night_mode': 'mean',
}).reset_index()

# Only keep clear A or B nights
nightly = nightly[(nightly['night_mode'] < 0.1) | (nightly['night_mode'] > 0.9)]
nightly['night_B'] = (nightly['night_mode'] > 0.5).astype(int)

n_a = (nightly['night_B']==0).sum()
n_b = (nightly['night_B']==1).sum()
print(f"  {len(nightly)} complete nights (A={n_a}, B={n_b})")
print()

for var, label in [('temp_in', 'Terrarium temp'),
                    ('cooling', 'Cooling delta'),
                    ('temp_room', 'Room temp'),
                    ('humidity', 'Humidity'),
                    ('humi_room', 'Room humidity'),
                    ('freezer', 'Freezer duty'),
                    ('fan_pwm', 'Fan PWM')]:
    a = nightly.loc[nightly['night_B']==0, var]
    b = nightly.loc[nightly['night_B']==1, var]
    t, p = ttest_ind(b, a, equal_var=False)
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
    print(f"  {label:18s}: A={a.mean():6.2f}±{a.std():4.2f}  B={b.mean():6.2f}±{b.std():4.2f}  "
          f"Δ={b.mean()-a.mean():+.3f}  p={p:.3f} {sig}")

# ===================================================================
# 3. REGRESSION: temp ~ night_B + room conditions
# ===================================================================
print(f"\n{'='*70}")
print("3. REGRESSION MODELS (5-min level, HC3 robust SE)")
print('='*70)

# Model A: temp_in ~ night_B + temp_room + humi_room + hour
print("\n  Model A: temp_in ~ night_B + temp_room + humi_room + freezer + hour")
X_a = sm.add_constant(df_night[['night_B', 'temp_room', 'humi_room', 'freezer', 'hour_sin', 'hour_cos']])
model_a = sm.OLS(df_night['temp_in'], X_a).fit(cov_type='HC3')
ci = model_a.conf_int()
for var in ['night_B', 'temp_room', 'humi_room', 'freezer']:
    sig = "***" if model_a.pvalues[var] < 0.001 else "**" if model_a.pvalues[var] < 0.01 else "*" if model_a.pvalues[var] < 0.05 else ""
    print(f"    {var:15s}: {model_a.params[var]:+.4f} [{ci.loc[var,0]:+.4f}, {ci.loc[var,1]:+.4f}] p={model_a.pvalues[var]:.4f} {sig}")
print(f"    R² = {model_a.rsquared:.4f}")

# Model B: cooling delta ~ night_B + room conditions
print("\n  Model B: cooling_delta ~ night_B + temp_room + humi_room + freezer + hour")
X_b = sm.add_constant(df_night[['night_B', 'temp_room', 'humi_room', 'freezer', 'hour_sin', 'hour_cos']])
model_b = sm.OLS(df_night['cooling'], X_b).fit(cov_type='HC3')
ci = model_b.conf_int()
for var in ['night_B', 'temp_room', 'humi_room', 'freezer']:
    sig = "***" if model_b.pvalues[var] < 0.001 else "**" if model_b.pvalues[var] < 0.01 else "*" if model_b.pvalues[var] < 0.05 else ""
    print(f"    {var:15s}: {model_b.params[var]:+.4f} [{ci.loc[var,0]:+.4f}, {ci.loc[var,1]:+.4f}] p={model_b.pvalues[var]:.4f} {sig}")
print(f"    R² = {model_b.rsquared:.4f}")

# ===================================================================
# 4. NIGHTLY REGRESSION (proper inference, no autocorrelation)
# ===================================================================
print(f"\n{'='*70}")
print("4. NIGHTLY REGRESSION (aggregated, proper inference)")
print('='*70)

print("\n  temp_in ~ night_B + temp_room + humi_room")
X_n1 = sm.add_constant(nightly[['night_B', 'temp_room', 'humi_room']])
model_n1 = sm.OLS(nightly['temp_in'], X_n1).fit(cov_type='HC3')
ci = model_n1.conf_int()
for var in ['night_B', 'temp_room', 'humi_room']:
    sig = "***" if model_n1.pvalues[var] < 0.001 else "**" if model_n1.pvalues[var] < 0.01 else "*" if model_n1.pvalues[var] < 0.05 else ""
    print(f"    {var:15s}: {model_n1.params[var]:+.4f} [{ci.loc[var,0]:+.4f}, {ci.loc[var,1]:+.4f}] p={model_n1.pvalues[var]:.3f} {sig}")
print(f"    R² = {model_n1.rsquared:.3f}, N = {int(model_n1.nobs)}")

print("\n  cooling_delta ~ night_B + temp_room + humi_room")
X_n2 = sm.add_constant(nightly[['night_B', 'temp_room', 'humi_room']])
model_n2 = sm.OLS(nightly['cooling'], X_n2).fit(cov_type='HC3')
ci = model_n2.conf_int()
for var in ['night_B', 'temp_room', 'humi_room']:
    sig = "***" if model_n2.pvalues[var] < 0.001 else "**" if model_n2.pvalues[var] < 0.01 else "*" if model_n2.pvalues[var] < 0.05 else ""
    print(f"    {var:15s}: {model_n2.params[var]:+.4f} [{ci.loc[var,0]:+.4f}, {ci.loc[var,1]:+.4f}] p={model_n2.pvalues[var]:.3f} {sig}")
print(f"    R² = {model_n2.rsquared:.3f}, N = {int(model_n2.nobs)}")

# ===================================================================
# 5. HOURLY PROFILE: how does temperature evolve through the night?
# ===================================================================
print(f"\n{'='*70}")
print("5. HOURLY TEMPERATURE PROFILE (Night A vs B)")
print('='*70)

# Create hour bins for nighttime
df_night['hour_bin'] = df_night['hour'].apply(lambda h: int(h) if h >= 20 else int(h) + 24)

print(f"\n  {'Hour':<8} {'A temp':>8} {'B temp':>8} {'Δ temp':>8} {'A cool':>8} {'B cool':>8} {'Δ cool':>8}")
print(f"  {'─'*56}")

for hb in sorted(df_night['hour_bin'].unique()):
    mask_a = (df_night['night_B']==0) & (df_night['hour_bin']==hb)
    mask_b = (df_night['night_B']==1) & (df_night['hour_bin']==hb)
    if mask_a.sum() < 3 or mask_b.sum() < 3:
        continue

    a_temp = df_night.loc[mask_a, 'temp_in'].mean()
    b_temp = df_night.loc[mask_b, 'temp_in'].mean()
    a_cool = df_night.loc[mask_a, 'cooling'].mean()
    b_cool = df_night.loc[mask_b, 'cooling'].mean()

    # Display hour label
    display_h = hb if hb < 24 else hb - 24
    print(f"  {display_h:02d}:00   {a_temp:8.2f} {b_temp:8.2f} {b_temp-a_temp:+8.3f} "
          f"{a_cool:8.2f} {b_cool:8.2f} {b_cool-a_cool:+8.3f}")

# ===================================================================
# 6. TEMPERATURE TRAJECTORY: evening cooldown rate
# ===================================================================
print(f"\n{'='*70}")
print("6. COOLING RATE ANALYSIS")
print('='*70)

# For each night, compute: temp at 20:30, temp at 06:00, total drop, rate
night_trajectories = []
for date in nightly['night_date']:
    mask = df_night['night_date'] == date
    night_data = df_night[mask].sort_values('hour_bin')
    if len(night_data) < 10:
        continue

    # Early night (20:00-22:00) and late night (04:00-06:00)
    early = night_data[night_data['hour_bin'].between(20, 22)]
    late = night_data[night_data['hour_bin'].between(28, 30)]  # 04:00-06:00

    if len(early) < 3 or len(late) < 3:
        continue

    t_early = early['temp_in'].mean()
    t_late = late['temp_in'].mean()
    r_early = early['temp_room'].mean()
    r_late = late['temp_room'].mean()
    drop = t_early - t_late
    hours = 8  # approx 20:00 to 04:00
    mode = night_data['night_B'].iloc[0]

    night_trajectories.append({
        'date': date, 'night_B': mode,
        'temp_early': t_early, 'temp_late': t_late,
        'room_early': r_early, 'room_late': r_late,
        'temp_drop': drop, 'rate': drop / hours,
        'cool_early': r_early - t_early, 'cool_late': r_late - t_late,
    })

traj = pd.DataFrame(night_trajectories)

if len(traj) > 0:
    for var, label, unit in [
        ('temp_early', 'Temp at 20-22h', '°C'),
        ('temp_late', 'Temp at 04-06h', '°C'),
        ('temp_drop', 'Overnight drop', '°C'),
        ('rate', 'Cooling rate', '°C/h'),
        ('cool_early', 'Cooling Δ at 20-22h', '°C'),
        ('cool_late', 'Cooling Δ at 04-06h', '°C'),
    ]:
        a = traj.loc[traj['night_B']==0, var]
        b = traj.loc[traj['night_B']==1, var]
        if len(a) > 1 and len(b) > 1:
            t, p = ttest_ind(b, a, equal_var=False)
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
            print(f"  {label:25s}: A={a.mean():.2f}±{a.std():.2f}  B={b.mean():.2f}±{b.std():.2f}  "
                  f"Δ={b.mean()-a.mean():+.3f} {unit}  p={p:.3f} {sig}")

# ===================================================================
# SUMMARY
# ===================================================================
print(f"\n{'='*70}")
print("SUMMARY")
print('='*70)

m_a_temp = df_night.loc[df_night['night_B']==0, 'temp_in'].mean()
m_b_temp = df_night.loc[df_night['night_B']==1, 'temp_in'].mean()
m_a_cool = df_night.loc[df_night['night_B']==0, 'cooling'].mean()
m_b_cool = df_night.loc[df_night['night_B']==1, 'cooling'].mean()
reg_temp = model_a.params['night_B']
reg_cool = model_b.params['night_B']
nightly_temp = model_n1.params['night_B']
nightly_cool = model_n2.params['night_B']

print(f"""
  Night A = fans OFF at night
  Night B = outlet + impeller at 80 PWM at night

  ───────────────────────────────────────────────────────────────────
  Temperature effect of Night B (fans=80 PWM):
    Raw difference (5-min):        {m_b_temp - m_a_temp:+.3f}°C  (B is {'cooler' if m_b_temp < m_a_temp else 'warmer'})
    Regression (5-min, controls):  {reg_temp:+.3f}°C  p={model_a.pvalues['night_B']:.4f}
    Nightly aggregate (controls):  {nightly_temp:+.3f}°C  p={model_n1.pvalues['night_B']:.3f}

  Cooling delta effect (room-terrarium gap):
    Raw difference (5-min):        {m_b_cool - m_a_cool:+.3f}°C  (B has {'more' if m_b_cool > m_a_cool else 'less'} cooling)
    Regression (5-min, controls):  {reg_cool:+.3f}°C  p={model_b.pvalues['night_B']:.4f}
    Nightly aggregate (controls):  {nightly_cool:+.3f}°C  p={model_n2.pvalues['night_B']:.3f}

  Interpretation:
    Fans at 80 PWM {'lower' if reg_temp < 0 else 'raise'} terrarium temperature by ~{abs(reg_temp):.2f}°C
    and {'increase' if reg_cool > 0 else 'decrease'} the cooling gap by ~{abs(reg_cool):.2f}°C
  ───────────────────────────────────────────────────────────────────
""")
