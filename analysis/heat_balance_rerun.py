#!/usr/bin/env python3
"""Heat-balance regression with proper inference (statsmodels OLS).

Re-runs the dT/dt = a0 + a1*T_diff + a2*fans + a3*freezer + a4*lights + a5*fans*freezer
model that Pi-Claude originally ran with numpy.linalg.lstsq (R²=0.24, no SE/CI/F),
this time with HC3 robust standard errors and over the full Meross-instrumented
window so we can publish the table HardwareX §7.4 currently states without
inference.

Outputs:
- stdout: full statsmodels summary
- paper/heat_balance_run_YYYY-MM-DD.yaml: structured stats for the SoT
"""

import subprocess
from io import StringIO
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import numpy as np
import statsmodels.api as sm


WINDOW_DAYS = 84  # 2026-02-18 to ~2026-05-12 covers the Meross-daemon window


def query_influx(measurement: str, days: int = WINDOW_DAYS) -> pd.DataFrame:
    cmd = (f'influx -database highland -execute '
           f'"SELECT value FROM {measurement} WHERE time > now() - {days}d" '
           f'-format csv')
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    df = pd.read_csv(StringIO(result.stdout))
    if df.empty:
        return pd.DataFrame()
    df['time'] = pd.to_datetime(df['time'].astype(int), unit='ns', utc=True)
    df['time'] = df['time'].dt.tz_convert('Europe/Rome')
    df = df.set_index('time')
    return df[['value']].rename(columns={'value': measurement})


def wet_bulb(T, RH):
    return (T * np.arctan(0.151977 * (RH + 8.313659) ** 0.5)
            + np.arctan(T + RH) - np.arctan(RH - 1.676331)
            + 0.00391838 * RH ** 1.5 * np.arctan(0.023101 * RH) - 4.686035)


print(f"Querying {WINDOW_DAYS} days of data...")
series = {
    'room_t':    query_influx('room_temperature'),
    'room_h':    query_influx('room_humidity'),
    'local_t':   query_influx('local_temperature'),
    'freezer':   query_influx('freezer_status'),
    'light':     query_influx('light_status'),
    'fan_speed': query_influx('fan_speed'),
}

freq = '5min'
df = pd.concat([s.resample(freq).mean().rename(columns={s.columns[0]: name})
                for name, s in series.items() if not s.empty], axis=1)
df = df.dropna(subset=['room_t', 'local_t'])
print(f"Merged: {len(df)} 5-min rows ({df.index.min()} → {df.index.max()})")

df['room_wb']      = wet_bulb(df['room_t'], df['room_h'])
df['t_diff_room']  = df['room_t']  - df['local_t']
df['t_above_wb']   = df['local_t'] - df['room_wb']
df['freezer_on']   = (df['freezer'].fillna(0) > 0.5).astype(float)
df['light_on']     = (df['light'].fillna(0)   > 0.5).astype(float)
df['fan_pwm']      = df['fan_speed'].fillna(0).clip(lower=0, upper=255)
df['fans_on']      = (df['fan_pwm'] > 0).astype(float)

# dT/dt °C per hour via centered difference (2 steps × 5 min = 10 min)
df['dT_dt'] = df['local_t'].diff(periods=2) / (10 / 60)
df['dT_dt'] = df['dT_dt'].shift(-1)
df = df[df['dT_dt'].abs() < 10]

# Drop any remaining NaNs introduced by diff
df = df.dropna(subset=['dT_dt', 't_diff_room', 'fans_on', 'freezer_on', 'light_on'])
print(f"Valid rows after NaN/outlier filter: {len(df)}")

# Model 1: original specification (binary fans_on for direct comparison)
X = sm.add_constant(df[['t_diff_room', 'fans_on', 'freezer_on', 'light_on']]
                    .assign(fans_freezer=df['fans_on'] * df['freezer_on']))
y = df['dT_dt']
m1 = sm.OLS(y, X).fit(cov_type='HC3')

# Model 2: continuous fan PWM (better-specified, but coefficient is per-PWM-unit)
X2 = sm.add_constant(df[['t_diff_room', 'fan_pwm', 'freezer_on', 'light_on']]
                     .assign(fan_freezer=df['fan_pwm'] * df['freezer_on']))
m2 = sm.OLS(y, X2).fit(cov_type='HC3')

print("\n" + "=" * 70)
print("MODEL 1 — binary fans_on (matches original 2026-02-24 specification)")
print("=" * 70)
print(m1.summary())

print("\n" + "=" * 70)
print("MODEL 2 — continuous fan_pwm (better-specified)")
print("=" * 70)
print(m2.summary())


def coef_block(model, var: str) -> dict:
    return {
        'coef':   float(model.params[var]),
        'se':     float(model.bse[var]),
        't':      float(model.tvalues[var]),
        'p':      float(model.pvalues[var]),
        'ci95':   [float(model.conf_int().loc[var, 0]),
                   float(model.conf_int().loc[var, 1])],
    }


now_iso = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')

result = {
    'generated_utc': now_iso,
    'window': {
        'start': df.index.min().isoformat(),
        'end':   df.index.max().isoformat(),
        'days':  float((df.index.max() - df.index.min()).total_seconds() / 86400),
        'n_rows_5min': int(len(df)),
    },
    'covariance_type': 'HC3 robust',
    'software': 'statsmodels.api.OLS (Python)',
    'model_1_binary_fans': {
        'formula': 'dT_dt ~ const + t_diff_room + fans_on + freezer_on + light_on + fans_on*freezer_on',
        'r_squared':       float(m1.rsquared),
        'adj_r_squared':   float(m1.rsquared_adj),
        'f_statistic':     float(m1.fvalue),
        'f_pvalue':        float(m1.f_pvalue),
        'n':               int(m1.nobs),
        'df_resid':        int(m1.df_resid),
        'coefficients': {v: coef_block(m1, v) for v in m1.params.index},
    },
    'model_2_continuous_pwm': {
        'formula': 'dT_dt ~ const + t_diff_room + fan_pwm + freezer_on + light_on + fan_pwm*freezer_on',
        'r_squared':       float(m2.rsquared),
        'adj_r_squared':   float(m2.rsquared_adj),
        'f_statistic':     float(m2.fvalue),
        'f_pvalue':        float(m2.f_pvalue),
        'n':               int(m2.nobs),
        'df_resid':        int(m2.df_resid),
        'coefficients': {v: coef_block(m2, v) for v in m2.params.index},
    },
}

# Headline summary for the paper
print("\n" + "=" * 70)
print("HEADLINE (Model 1, for direct comparison with the 2026-02-24 numbers)")
print("=" * 70)
for var, label in [('fans_on',     'Fans ON     (°C/hr)'),
                   ('freezer_on',  'Freezer ON  (°C/hr)'),
                   ('t_diff_room', 'Passive     (°C/hr per °C diff)')]:
    c = result['model_1_binary_fans']['coefficients'][var]
    print(f"  {label:35s} = {c['coef']:+7.3f}  SE={c['se']:.3f}  "
          f"95%CI=[{c['ci95'][0]:+7.3f}, {c['ci95'][1]:+7.3f}]  p={c['p']:.4f}")
print(f"  R²={result['model_1_binary_fans']['r_squared']:.4f}  "
      f"F={result['model_1_binary_fans']['f_statistic']:.1f}  "
      f"N={result['model_1_binary_fans']['n']}")

# Dump YAML manually (no external dep)
def yaml_dump(d, indent=0):
    out = []
    pre = '  ' * indent
    for k, v in d.items():
        if isinstance(v, dict):
            out.append(f'{pre}{k}:')
            out.append(yaml_dump(v, indent + 1))
        elif isinstance(v, list):
            out.append(f'{pre}{k}: [{", ".join(repr(x) if isinstance(x, str) else str(x) for x in v)}]')
        elif isinstance(v, str):
            out.append(f'{pre}{k}: "{v}"')
        else:
            out.append(f'{pre}{k}: {v}')
    return '\n'.join(out)

stamp = datetime.now().strftime('%Y-%m-%d')
out_path = Path(__file__).resolve().parents[1] / 'paper' / f'heat_balance_run_{stamp}.yaml'
out_path.write_text(yaml_dump(result) + '\n')
print(f"\nWrote {out_path}")
