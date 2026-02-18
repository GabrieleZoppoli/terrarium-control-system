#!/usr/bin/env python3
"""
IV/2SLS Model: Causal effect of fan PWM on humidity
Instrument: Night A/B experiment (day-of-year parity)
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from linearmodels.iv import IV2SLS
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
]

dfs = {}
for filename, colname in series:
    dfs[colname] = load_series(filename, colname)

df = dfs['humidity']
for colname, other_df in dfs.items():
    if colname == 'humidity':
        continue
    df = pd.merge_asof(df.sort_values('time'), other_df.sort_values('time'),
                        on='time', tolerance=300_000_000_000)

df = df.dropna()

# Derive time features
df['hour'] = (df['time'] / 3.6e12) % 24
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
df['daytime'] = ((df['hour'] >= 6.5) & (df['hour'] <= 20.0)).astype(int)

# Night mode: 0 = Night A (fans off), 1 = Night B (fans at 80)
# Filter to NIGHTTIME only for the IV analysis (instrument only valid at night)
df_night = df[df['daytime'] == 0].copy()
# Also need night_mode to be 0 or 1 (not intermediate from 5-min averaging)
df_night['night_B'] = (df_night['night_mode'] > 0.5).astype(int)

print(f"Full dataset: {len(df)} rows")
print(f"Nighttime subset: {len(df_night)} rows")
print(f"Night A (fans off): {(df_night['night_B']==0).sum()} rows")
print(f"Night B (fans=80):  {(df_night['night_B']==1).sum()} rows")

# ===================================================================
# SIMPLE A/B COMPARISON (no regression, just means)
# ===================================================================
print(f"\n{'='*70}")
print("SIMPLE A/B COMPARISON (nighttime only)")
print('='*70)

for var in ['humidity', 'fan_pwm', 'temp_in', 'temp_room', 'humi_room', 'freezer']:
    a = df_night.loc[df_night['night_B']==0, var]
    b = df_night.loc[df_night['night_B']==1, var]
    diff = b.mean() - a.mean()
    # Welch t-test
    from scipy.stats import ttest_ind
    t, p = ttest_ind(b, a, equal_var=False)
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
    print(f"  {var:15s}: Night A={a.mean():.2f}, Night B={b.mean():.2f}, "
          f"Δ={diff:+.2f}, t={t:.2f}, p={p:.4f} {sig}")

# ===================================================================
# STAGE 1: fan_pwm ~ night_B + covariates (first stage)
# ===================================================================
print(f"\n{'='*70}")
print("STAGE 1: fan_pwm ~ night_B + temp_room + humi_room + freezer + hour_sin/cos")
print('='*70)

exog_cols = ['temp_room', 'humi_room', 'freezer', 'hour_sin', 'hour_cos']
X_s1 = sm.add_constant(df_night[['night_B'] + exog_cols])
y_s1 = df_night['fan_pwm']

stage1 = sm.OLS(y_s1, X_s1).fit(cov_type='HC3')
print(stage1.summary())

# F-statistic on the instrument
f_stat = stage1.wald_test('night_B = 0', scalar=True).statistic
print(f"\n  Instrument F-statistic: {f_stat:.1f} (>10 = strong instrument)")

# ===================================================================
# IV/2SLS: humidity ~ fan_pwm(instrumented) + covariates
# ===================================================================
print(f"\n{'='*70}")
print("IV/2SLS: humidity ~ fan_pwm[instrumented by night_B] + covariates")
print('='*70)

# Using linearmodels IV2SLS
# Dependent: humidity
# Endogenous: fan_pwm (instrumented by night_B)
# Exogenous controls: temp_room, humi_room, freezer, hour_sin, hour_cos

df_iv = df_night.copy()
df_iv.index = range(len(df_iv))

dependent = df_iv['humidity']
endog = df_iv[['fan_pwm']]
exog = sm.add_constant(df_iv[exog_cols])
instruments = df_iv[['night_B']]

iv_model = IV2SLS(dependent, exog, endog, instruments).fit(cov_type='robust')
print(iv_model.summary)

# ===================================================================
# OLS for comparison (same nighttime sample)
# ===================================================================
print(f"\n{'='*70}")
print("OLS COMPARISON (same nighttime sample, no instrument)")
print('='*70)

X_ols = sm.add_constant(df_night[['fan_pwm'] + exog_cols])
y_ols = df_night['humidity']
ols_night = sm.OLS(y_ols, X_ols).fit(cov_type='HC3')

iv_ci = iv_model.conf_int()
print(f"  OLS  fan_pwm coef: {ols_night.params['fan_pwm']:+.4f} "
      f"[{ols_night.conf_int().loc['fan_pwm',0]:+.4f}, {ols_night.conf_int().loc['fan_pwm',1]:+.4f}]")
print(f"  IV   fan_pwm coef: {iv_model.params['fan_pwm']:+.4f} "
      f"[{iv_ci.loc['fan_pwm','lower']:+.4f}, {iv_ci.loc['fan_pwm','upper']:+.4f}]")

print(f"\n  OLS says +10 PWM → {ols_night.params['fan_pwm']*10:+.2f}% humidity (biased: simultaneity)")
print(f"  IV  says +10 PWM → {iv_model.params['fan_pwm']*10:+.2f}% humidity (causal estimate)")

# ===================================================================
# REDUCED FORM: direct effect of night_B on humidity
# ===================================================================
print(f"\n{'='*70}")
print("REDUCED FORM: humidity ~ night_B + covariates (no fan_pwm)")
print('='*70)

X_rf = sm.add_constant(df_night[['night_B'] + exog_cols])
rf_model = sm.OLS(df_night['humidity'], X_rf).fit(cov_type='HC3')

print(f"  night_B coefficient: {rf_model.params['night_B']:+.3f} "
      f"[{rf_model.conf_int().loc['night_B',0]:+.3f}, {rf_model.conf_int().loc['night_B',1]:+.3f}] "
      f"p={rf_model.pvalues['night_B']:.4f}")
print(f"\n  Interpretation: Night B (fans=80) vs Night A (fans=0) → "
      f"{rf_model.params['night_B']:+.2f}% humidity")
print(f"  This is the intention-to-treat (ITT) effect.")

# Wald/IV estimate = reduced form / first stage
rf_coef = rf_model.params['night_B']
fs_coef = stage1.params['night_B']
wald = rf_coef / fs_coef
print(f"\n  Wald estimator (RF/FS): {rf_coef:.4f} / {fs_coef:.4f} = {wald:.4f} per PWM unit")
print(f"  = {wald*10:+.3f}% humidity per +10 PWM (should match IV coefficient)")

# ===================================================================
# NIGHTLY AGGREGATES (robustness: avoids autocorrelation)
# ===================================================================
print(f"\n{'='*70}")
print("NIGHTLY AGGREGATES (one observation per night, avoids autocorrelation)")
print('='*70)

# Create date column (night = date of the evening, so 00:00-06:30 belongs to previous day)
df_night['timestamp'] = pd.to_datetime(df_night['time'], unit='ns')
df_night['night_date'] = (df_night['timestamp'] - pd.Timedelta(hours=6, minutes=30)).dt.date

nightly = df_night.groupby('night_date').agg({
    'humidity': 'mean',
    'fan_pwm': 'mean',
    'temp_in': 'mean',
    'temp_room': 'mean',
    'humi_room': 'mean',
    'freezer': 'mean',
    'night_B': 'first',
    'night_mode': 'mean',
}).reset_index()

# Only keep nights with clear A or B assignment
nightly = nightly[(nightly['night_mode'] < 0.1) | (nightly['night_mode'] > 0.9)]
nightly['night_B'] = (nightly['night_mode'] > 0.5).astype(int)

print(f"  {len(nightly)} complete nights")
print(f"  Night A: {(nightly['night_B']==0).sum()}, Night B: {(nightly['night_B']==1).sum()}")
print()

for var in ['humidity', 'fan_pwm', 'temp_in', 'temp_room', 'humi_room']:
    a = nightly.loc[nightly['night_B']==0, var]
    b = nightly.loc[nightly['night_B']==1, var]
    t, p = ttest_ind(b, a, equal_var=False)
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
    print(f"  {var:15s}: A={a.mean():.1f}±{a.std():.1f}, B={b.mean():.1f}±{b.std():.1f}, "
          f"Δ={b.mean()-a.mean():+.2f}, p={p:.3f} {sig}")

# Night-level regression
print(f"\n  Night-level OLS: humidity ~ night_B + temp_room + humi_room")
X_nightly = sm.add_constant(nightly[['night_B', 'temp_room', 'humi_room']])
nightly_model = sm.OLS(nightly['humidity'], X_nightly).fit(cov_type='HC3')
for var in ['night_B', 'temp_room', 'humi_room']:
    ci = nightly_model.conf_int()
    print(f"    {var:15s}: {nightly_model.params[var]:+.3f} "
          f"[{ci.loc[var,0]:+.3f}, {ci.loc[var,1]:+.3f}] p={nightly_model.pvalues[var]:.3f}")
print(f"    R² = {nightly_model.rsquared:.3f}")

print(f"\n{'='*70}")
print("SUMMARY")
print('='*70)
print(f"""
  Method                        fan_pwm effect (per +10 PWM)
  ─────────────────────────────────────────────────────────
  OLS (biased)                  {ols_night.params['fan_pwm']*10:+.3f}%  (simultaneity bias → positive)
  IV/2SLS (causal)              {iv_model.params['fan_pwm']*10:+.3f}%
  Reduced form (Night B effect) {rf_model.params['night_B']:+.2f}% for 80 PWM increase
  Nightly aggregate             {nightly.loc[nightly['night_B']==1,'humidity'].mean() - nightly.loc[nightly['night_B']==0,'humidity'].mean():+.2f}% raw difference

  The IV estimate should be interpreted as:
  Each +10 PWM of fan speed CAUSES humidity to change by ~{iv_model.params['fan_pwm']*10:+.2f}%

  At 80 PWM (Night B level): {iv_model.params['fan_pwm']*80:+.2f}% vs fans off
""")
