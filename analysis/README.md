# Terrarium PID Statistical Analysis

Statistical models of the PID-controlled highland cloud forest terrarium.
Generated 2026-02-18.

## Data

- Source: InfluxDB `highland` database, 5-minute aggregates
- Default window: last 14 days
- Run `./export_data.sh [days]` to refresh CSVs before re-running scripts

## Scripts

### 01_pid_humidity_model.py
Four OLS models of terrarium humidity:
- **Model 1**: Static OLS — humidity ~ fan_pwm + temp_in + temp_room + humi_room + freezer + mister
- **Model 2**: Enriched — adds temp_delta, hour, daytime, fan×freezer interaction
- **Model 3**: AR(1) dynamic — adds lagged humidity, computes long-run multipliers
- **Model 4**: First-difference (Δhumidity) — what drives humidity changes

Key finding: fan_pwm shows *positive* association with humidity due to PID simultaneity
(fans increase because humidity is high, not the other way around).

### 02_iv_causal_model.py
IV/2SLS model using Night A/B experiment as instrument:
- Instrument: day-of-year parity (even=fans off, odd=fans at 80 PWM)
- First-stage F=20.6 (strong instrument)
- **Causal estimate: +10 PWM → -0.37% humidity** (sign correctly flips vs OLS)
- Includes reduced-form, Wald estimator, and nightly aggregate comparison

### 03_ab_temperature.py
Night A/B effect on temperature (unadjusted):
- Raw comparison, nightly aggregates, regressions
- Hourly profiles, cooling rate analysis
- Key finding: fans accelerate evening cooling but raise late-night floor

### 04_ab_temperature_adjusted.py
Same as 03 but adjusted for room temperature and humidity:
- Hour-by-hour regressions with controls
- Residualized profiles
- Balance check on room conditions
- **Adjusted: evening cooling -0.75 to -1.4°C, late-night warming +0.3 to +0.55°C**

## Dependencies

```bash
pip3 install --break-system-packages pandas statsmodels linearmodels scipy
```

## Usage

```bash
cd ~/terrarium-analysis
./export_data.sh          # refresh data (optional days arg, default 14)
python3 01_pid_humidity_model.py
python3 02_iv_causal_model.py
python3 03_ab_temperature.py
python3 04_ab_temperature_adjusted.py
```

Results are saved in `results/` as text files.
