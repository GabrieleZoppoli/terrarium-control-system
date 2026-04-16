#!/usr/bin/env python3
"""
PID Humidity Model for Terrarium
Outcome: local_humidity
Main variable: fan_speed (PID PWM output)
Covariates: local_temperature, room_temperature, room_humidity, freezer_status, mister_status
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson
import warnings
warnings.filterwarnings('ignore')

# --- Load and merge data ---
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
    ('target_humidity', 'target_humi'),
    ('target_temperature', 'target_temp'),
    ('vpd', 'vpd'),
    ('night_test_mode', 'night_mode'),
]

dfs = {}
for filename, colname in series:
    try:
        dfs[colname] = load_series(filename, colname)
        print(f"  {colname}: {len(dfs[colname])} rows")
    except Exception as e:
        print(f"  {colname}: FAILED - {e}")

# Merge all on time
df = dfs['humidity']
for colname, other_df in dfs.items():
    if colname == 'humidity':
        continue
    df = pd.merge_asof(df.sort_values('time'), other_df.sort_values('time'),
                        on='time', tolerance=300_000_000_000)  # 5 min tolerance in ns

print(f"\nMerged dataset: {len(df)} rows, {df.columns.tolist()}")
print(f"Missing values:\n{df.isnull().sum()}")
df = df.dropna()
print(f"After dropna: {len(df)} rows")

# --- Derive features ---
# Temperature differential (room - terrarium) — NOT a tautology since outcome is humidity
df['temp_delta'] = df['temp_room'] - df['temp_in']
# Hour of day (cyclic encoding)
df['hour'] = (df['time'] / 3.6e12) % 24
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
# Is daytime (06:30-20:00)
df['daytime'] = ((df['hour'] >= 6.5) & (df['hour'] <= 20.0)).astype(int)
# Interaction: fan effect may differ when freezer is on (cold air = more condensation)
df['fan_x_freezer'] = df['fan_pwm'] * df['freezer']
# Lagged humidity (previous 5min period) — captures autocorrelation / inertia
df['humidity_lag1'] = df['humidity'].shift(1)
df['humidity_lag2'] = df['humidity'].shift(2)
# Change in humidity (proxy for system dynamics)
df['humidity_change'] = df['humidity'] - df['humidity'].shift(1)
df = df.dropna()

print(f"Final dataset: {len(df)} rows")
print(f"\n{'='*70}")
print("DESCRIPTIVE STATISTICS")
print('='*70)
desc_cols = ['humidity', 'fan_pwm', 'temp_in', 'temp_room', 'humi_room',
             'freezer', 'mister', 'temp_delta']
print(df[desc_cols].describe().round(2))

# Quick correlation check
print(f"\n{'='*70}")
print("CORRELATIONS WITH HUMIDITY")
print('='*70)
corr_cols = ['fan_pwm', 'temp_in', 'temp_room', 'humi_room', 'freezer',
             'mister', 'temp_delta', 'daytime']
for c in corr_cols:
    r = df['humidity'].corr(df[c])
    print(f"  {c:20s}: r = {r:+.3f}")

# ===================================================================
# MODEL 1: Cross-sectional OLS (no lags)
# humidity ~ fan_pwm + temp_in + temp_room + humi_room + freezer + mister
# ===================================================================
print(f"\n{'='*70}")
print("MODEL 1: Static OLS")
print("humidity ~ fan_pwm + temp_in + temp_room + humi_room + freezer + mister")
print('='*70)

X1_cols = ['fan_pwm', 'temp_in', 'temp_room', 'humi_room', 'freezer', 'mister']
X1 = sm.add_constant(df[X1_cols])
y = df['humidity']

model1 = sm.OLS(y, X1).fit(cov_type='HC3')
print(model1.summary())

# ===================================================================
# MODEL 2: Richer static model with time + interaction
# ===================================================================
print(f"\n{'='*70}")
print("MODEL 2: Enriched static OLS")
print("+ temp_delta + hour_sin/cos + daytime + fan_pwm×freezer")
print('='*70)

X2_cols = ['fan_pwm', 'temp_in', 'temp_room', 'humi_room', 'freezer', 'mister',
           'temp_delta', 'hour_sin', 'hour_cos', 'daytime', 'fan_x_freezer']
X2 = sm.add_constant(df[X2_cols])

model2 = sm.OLS(y, X2).fit(cov_type='HC3')
print(model2.summary())

# ===================================================================
# MODEL 3: Dynamic AR(1) model — controls for humidity inertia
# Coefficients represent short-run effects (5-min increment)
# ===================================================================
print(f"\n{'='*70}")
print("MODEL 3: Dynamic AR(1) — short-run effects per 5-min step")
print("+ humidity_lag1")
print('='*70)

X3_cols = ['humidity_lag1', 'fan_pwm', 'temp_in', 'temp_room', 'humi_room',
           'freezer', 'mister', 'hour_sin', 'hour_cos', 'daytime', 'fan_x_freezer']
X3 = sm.add_constant(df[X3_cols])

model3 = sm.OLS(y, X3).fit(cov_type='HC3')
print(model3.summary())

# ===================================================================
# MODEL 4: Change model — Δhumidity ~ predictors
# What drives humidity CHANGES (rather than levels)
# ===================================================================
print(f"\n{'='*70}")
print("MODEL 4: First-difference — what drives Δhumidity?")
print("Δhumidity ~ fan_pwm + temp_in + temp_room + humi_room + freezer + mister + ...")
print('='*70)

X4_cols = ['fan_pwm', 'temp_in', 'temp_room', 'humi_room', 'freezer', 'mister',
           'temp_delta', 'hour_sin', 'hour_cos', 'daytime', 'fan_x_freezer']
X4 = sm.add_constant(df[X4_cols])
y4 = df['humidity_change']

model4 = sm.OLS(y4, X4).fit(cov_type='HC3')
print(model4.summary())

# ===================================================================
# DIAGNOSTICS
# ===================================================================
print(f"\n{'='*70}")
print("MODEL COMPARISON")
print('='*70)

models = [("M1 Static", model1, X1), ("M2 Enriched", model2, X2),
          ("M3 AR(1)", model3, X3), ("M4 Δhumidity", model4, X4)]

print(f"{'Model':<15} {'R²':>7} {'Adj-R²':>7} {'DW':>6} {'AIC':>10} {'BIC':>10} {'N':>6}")
print("-" * 65)
for name, model, X in models:
    dw = durbin_watson(model.resid)
    print(f"{name:<15} {model.rsquared:>7.4f} {model.rsquared_adj:>7.4f} "
          f"{dw:>6.3f} {model.aic:>10.0f} {model.bic:>10.0f} {int(model.nobs):>6}")

# ===================================================================
# LONG-RUN MULTIPLIERS (from Model 3)
# Short-run coef / (1 - ρ) where ρ = lag1 coefficient
# ===================================================================
print(f"\n{'='*70}")
print("LONG-RUN MULTIPLIERS (Model 3)")
print("Short-run effect / (1 - lag_coef) = cumulative steady-state effect")
print('='*70)

rho = model3.params['humidity_lag1']
print(f"  AR(1) coefficient (ρ): {rho:.4f}")
print(f"  Half-life of shock: {np.log(0.5)/np.log(rho):.1f} periods ({np.log(0.5)/np.log(rho)*5:.0f} min)")
print(f"  Long-run multiplier: 1/(1-ρ) = {1/(1-rho):.1f}x")
print()

lr_vars = ['fan_pwm', 'temp_in', 'temp_room', 'humi_room', 'freezer', 'mister']
for var in lr_vars:
    sr = model3.params[var]
    lr = sr / (1 - rho)
    sig = "***" if model3.pvalues[var] < 0.001 else "**" if model3.pvalues[var] < 0.01 else "*" if model3.pvalues[var] < 0.05 else ""
    print(f"  {var:20s}: short-run={sr:+.4f}, long-run={lr:+.3f} {sig}")

print(f"\n  Long-run practical effects:")
lr_fan = model3.params['fan_pwm'] / (1 - rho)
lr_troom = model3.params['temp_room'] / (1 - rho)
lr_hroom = model3.params['humi_room'] / (1 - rho)
lr_freezer = model3.params['freezer'] / (1 - rho)
lr_mister = model3.params['mister'] / (1 - rho)
print(f"  +10 PWM fan speed   → {lr_fan*10:+.2f}% humidity (steady state)")
print(f"  +1°C room temp      → {lr_troom:+.2f}% humidity")
print(f"  +10% room humidity  → {lr_hroom*10:+.2f}% humidity")
print(f"  Freezer ON vs OFF   → {lr_freezer:+.2f}% humidity")
print(f"  Mister ON vs OFF    → {lr_mister:+.2f}% humidity")

# ===================================================================
# MARGINAL EFFECTS — Model 1 (straightforward interpretation)
# ===================================================================
print(f"\n{'='*70}")
print("MARGINAL EFFECTS (Model 1 — simple, interpretable)")
print('='*70)

coefs = model1.params
ci = model1.conf_int()
pvals = model1.pvalues

for var in X1_cols:
    sig = "***" if pvals[var] < 0.001 else "**" if pvals[var] < 0.01 else "*" if pvals[var] < 0.05 else ""
    print(f"  {var:20s}: {coefs[var]:+.4f} [{ci.loc[var,0]:+.4f}, {ci.loc[var,1]:+.4f}] p={pvals[var]:.4f} {sig}")

print(f"\n  Practical interpretation (equilibrium associations):")
print(f"  +10 PWM fan speed   → {coefs['fan_pwm']*10:+.2f}% humidity")
print(f"  +1°C inner temp     → {coefs['temp_in']:+.2f}% humidity")
print(f"  +1°C room temp      → {coefs['temp_room']:+.2f}% humidity")
print(f"  +10% room humidity  → {coefs['humi_room']*10:+.2f}% humidity")
print(f"  Freezer ON vs OFF   → {coefs['freezer']:+.2f}% humidity")
print(f"  Mister ON vs OFF    → {coefs['mister']:+.2f}% humidity")

# ===================================================================
# SCENARIO ANALYSIS (Model 1 for interpretability)
# ===================================================================
print(f"\n{'='*70}")
print("SCENARIO ANALYSIS (Model 1)")
print('='*70)

means = df[X1_cols].mean()

def predict_m1(desc, overrides):
    row = means.copy()
    for k, v in overrides.items():
        row[k] = v
    row_full = pd.DataFrame([np.concatenate([[1], row.values])], columns=X1.columns)
    pred = model1.predict(row_full)[0]
    print(f"  {desc:50s} → {pred:.1f}%")

predict_m1("Baseline (all at means)", {})
predict_m1("Fans OFF (PWM=0), freezer OFF", {'fan_pwm': 0, 'freezer': 0})
predict_m1("Fans MIN (PWM=40), freezer OFF", {'fan_pwm': 40, 'freezer': 0})
predict_m1("Fans MID (PWM=120), freezer ON", {'fan_pwm': 120, 'freezer': 1})
predict_m1("Fans MAX (PWM=204), freezer ON", {'fan_pwm': 204, 'freezer': 1})
predict_m1("Night, fans OFF, freezer OFF", {'fan_pwm': 0, 'freezer': 0, 'mister': 0})
predict_m1("Night, fans=80, freezer OFF", {'fan_pwm': 80, 'freezer': 0, 'mister': 0})
predict_m1("Misting active", {'mister': 1})
predict_m1("Hot room (28°C), avg fans", {'temp_room': 28})
predict_m1("Cool room (18°C), avg fans", {'temp_room': 18})
predict_m1("Dry room (40% RH)", {'humi_room': 40})
predict_m1("Humid room (70% RH)", {'humi_room': 70})

# ===================================================================
# VIF — check multicollinearity
# ===================================================================
print(f"\n{'='*70}")
print("VARIANCE INFLATION FACTORS (Model 1)")
print('='*70)
from statsmodels.stats.outliers_influence import variance_inflation_factor
for i, col in enumerate(X1.columns):
    if col == 'const':
        continue
    vif = variance_inflation_factor(X1.values, i)
    flag = " ⚠ HIGH" if vif > 5 else ""
    print(f"  {col:20s}: VIF = {vif:.1f}{flag}")

print(f"\n{'='*70}")
print("NOTES ON INTERPRETATION")
print('='*70)
print("""
1. Model 1 (R²=0.43) captures equilibrium associations. The low DW (0.07)
   means massive autocorrelation — expected with 5-min time series. Coefficients
   are consistent but standard errors are underestimated.

2. Model 3 AR(1) (R²=0.98) controls for humidity inertia. The lag coefficient
   of ~0.98 means humidity is very sticky — shocks decay with a half-life of
   ~{hl:.0f} minutes. Short-run coefficients are tiny but accumulate over time.
   Long-run multipliers give the steady-state effects.

3. Model 4 (Δhumidity) directly models what changes humidity per 5-min step.
   Low R² is expected — most variance in Δh is noise/unmeasured factors.

4. Key findings:
   - fan_pwm has a POSITIVE association with humidity. This is NOT causal —
     the PID controller increases fans BECAUSE humidity is high. This is
     classic simultaneity bias (reverse causality).
   - Room temperature is the strongest exogenous driver: warmer room → lower
     terrarium humidity (more evaporative capacity, less condensation).
   - Room humidity positively predicts terrarium humidity (shared air exchange).
   - Freezer ON → slightly higher humidity (cold surfaces = condensation sink,
     but also reduces evaporation rate — net effect is small).
   - Mister ON → large negative coefficient in Model 1. Counterintuitive?
     No — misting is brief and the mister turns ON when humidity is already
     dropping (control logic), so it's another simultaneity artifact.

5. CAUTION: Because fan_pwm is endogenous (set by PID reacting to humidity),
   these models estimate ASSOCIATIONS, not causal effects. To estimate the
   true causal effect of fans on humidity, you would need:
   - An instrumental variable (e.g., the Night A/B experiment!)
   - Or a structural/VAR model with proper identification
""".format(hl=np.log(0.5)/np.log(rho)*5))

print("Done.")
