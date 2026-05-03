---
title: "InfluxDB Measurement Schema"
description: "All 32 measurements logged by the system"
---


**Database**: `highland`
**Default Retention Policy**: `standard_highland_retention` (365 days)
**Write Interval**: 60 seconds (Data Logger), varies for other sources

## Retention Policies

| Policy | Duration | Default |
|--------|----------|---------|
| `autogen` | infinite | No |
| `one_year_policy` | 365 days | No |
| `standard_highland_retention` | 365 days | Yes |

## Measurements

### Core Terrarium Measurements (Data Logger — 60s interval)

These 16 measurements are written by the centralized Data Logger function node on the Utilities tab, reading from Node-RED global context.

| # | Measurement | Field | Type | Unit | Source |
|---|-------------|-------|------|------|--------|
| 1 | `local_temperature` | `value` | float | °C | SHT35 via ESP8266/MQTT |
| 2 | `local_humidity` | `value` | float | % RH | SHT35 via ESP8266/MQTT |
| 3 | `vpd` | `value` | float | kPa | Calculated (Magnus formula) |
| 4 | `target_temperature_computed` | `value` | float | °C | Weather average (clamped 12--24°C) |
| 5 | `target_humidity_computed` | `value` | float | % RH | Weather average (clamped 75--95% as of 2026-05-02) |
| 6 | `difference_temperature` | `value` | float | °C | target − actual |
| 7 | `difference_humidity` | `value` | float | % | target − actual |
| 8 | `fan_speed` | `value` | float | PWM (0–255) | PID controller output |
| 9 | `freezer_status` | `value` | float | 0/1 | Tapo plug state (compressor) |
| 10 | `mister_status` | `value` | float | 0/1 | Tapo plug state |
| 11 | `light_status` | `value` | float | 0/1 | Tapo plug state |
| 12 | `water_level_local` | `value` | string | arbitrary | Ultrasonic water level sensor |
| 13 | `night_test_mode` | `value` | float | 0/1/−1 | 0=Night A (fans off), 1=Night B (fans 80), −1=suspended |
| 14 | `power_consumption` | `value` | float | Watts | Meross MSS310 energy monitor (via MQTT daemon, every 2s) |
| 15 | `wbt_shutdown_active` | `value` | float | 0/1 | WBT fan shutdown gate status |
| 16 | `pid_control_mode` | `value` | float | 0/1 | 0=humidity PID, 1=temperature PID |

### Fan PWM Measurements (RBE — on value change only)

These measurements are logged via Report-by-Exception (RBE) nodes — only written when the value changes. Null periods in the data indicate no change, not zero output.

| # | Measurement | Field | Type | Unit | Source |
|---|-------------|-------|------|------|--------|
| 15 | `fan_pwm_outlet` | `value` | float | PWM (0–255) | Arduino pin 45 |
| 16 | `fan_pwm_impeller` | `value` | float | PWM (0–255) | Arduino pin 46 |
| 17 | `fan_pwm_freezer` | `value` | float | PWM (0–255) | Arduino pin 44 |
| 18 | `fan_pwm_circulation` | `value` | float | PWM (0–255) | Arduino pin 12 |

### Room Environment (HTTP pull — ~60s interval)

Room conditions are pulled from a remote sensor (DietPi RPi at 192.168.1.94) via HTTP and stored locally.

| # | Measurement | Field | Type | Unit | Source |
|---|-------------|-------|------|------|--------|
| 19 | `room_temperature` | `value` | float | °C | Remote InfluxDB via HTTP |
| 20 | `room_humidity` | `value` | float | % RH | Remote InfluxDB via HTTP |

### Mist Events (event-driven — per mist cycle)

Logged instantly when a mist cycle is triggered, unlike the polled `mister_status` which can miss short cycles.

| # | Measurement | Field | Type | Unit | Source |
|---|-------------|-------|------|------|--------|
| 21 | `mist_event` | `value` | float | 1 | Humidity tab, event-driven on mist trigger |

### Arduino Health (serial parser — ~2s interval)

| # | Measurement | Field | Type | Unit | Source |
|---|-------------|-------|------|------|--------|
| 22 | `arduino_status` | `value` | float | 0/1 | Heartbeat alive indicator |

### Colombian Weather Reference (API poll interval)

Weather data from 4 Colombian highland cities, fetched via OpenWeatherMap API.

| # | Measurement | Field | Type | Unit | Source |
|---|-------------|-------|------|------|--------|
| 23 | `temperature` | `value` | float | °C | Chinchiná (primary) |
| 24 | `humidity` | `value` | float | % RH | Chinchiná (primary) |
| 25 | `temperature_bogota` | `value` | float | °C | Bogotá |
| 26 | `humidity_bogota` | `value` | float | % RH | Bogotá |
| 27 | `temperature_medellin` | `value` | float | °C | Medellín |
| 28 | `humidity_medellin` | `value` | float | % RH | Medellín |
| 29 | `temperature_sonson` | `value` | float | °C | Sonsón |
| 30 | `humidity_sonson` | `value` | float | % RH | Sonsón |

**Total**: 32 measurements across all sources.

## Common Queries

### Current conditions
```sql
SELECT last("value") FROM "local_temperature"
SELECT last("value") FROM "local_humidity"
SELECT last("value") FROM "vpd"
```

### Last 24 hours of temperature
```sql
SELECT mean("value") FROM "local_temperature" WHERE time > now() - 24h GROUP BY time(5m)
```

### Diurnal range
```sql
SELECT min("value"), max("value"), mean("value") FROM "local_temperature" WHERE time > now() - 24h
```

### Power consumption history
```sql
SELECT mean("value") FROM "power_consumption" WHERE time > now() - 7d GROUP BY time(1h)
```

### Accurate daily mist count (event-driven)
```sql
SELECT count("value") FROM "mist_event" WHERE time > now() - 24h
```

### Night A/B comparison (historical)
```sql
SELECT mean("value") FROM "local_temperature" WHERE time > '2026-02-05' AND time < '2026-02-19' GROUP BY time(1h)
```

## Notes

- All measurements use a single field key (`value`) for simplicity
- Boolean states (freezer, mister, light) are stored as float 0/1
- `water_level_local` is stored as string type (sensor returns integer as string)
- `fan_speed` from the Data Logger may be stale at night (retains last PID value even when fans are off — the PID only runs during 06:30–00:00)
- `fan_pwm_*` measurements use RBE logging, so gaps represent unchanged values, not missing data
- `night_test_mode` = −1 indicates the A/B experiment is suspended (current state)
- `power_consumption` is logged every 2 seconds via a persistent Meross daemon publishing to MQTT
- Query via CLI: `influx -database highland -execute 'YOUR QUERY'`
- `mist_event` is event-driven (one write per mist cycle), unlike polled `mister_status` which samples every 60s and can miss the 35s mist window. Use `mist_event` for accurate counts; `mister_status` data before 2026-02-24 undercounts by ~18%
- Note: `curl -sG` (GET) returns empty results — use POST or the CLI
