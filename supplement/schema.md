# InfluxDB Measurement Schema

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

These 13 measurements are written by the centralized Data Logger function node on the Utilities tab, reading from Node-RED global context.

| # | Measurement | Field | Type | Unit | Source |
|---|-------------|-------|------|------|--------|
| 1 | `local_temperature` | `value` | float | °C | SHT35 via ESP/MQTT |
| 2 | `local_humidity` | `value` | float | % RH | SHT35 via ESP/MQTT |
| 3 | `vpd` | `value` | float | kPa | Calculated (Magnus formula) |
| 4 | `target_temperature_computed` | `value` | float | °C | Weather average, clamped 12–24 |
| 5 | `target_humidity_computed` | `value` | float | °C | Weather average, clamped 70–90 |
| 6 | `difference_temperature` | `value` | float | °C | target − actual |
| 7 | `difference_humidity` | `value` | float | % | target − actual |
| 8 | `fan_speed` | `value` | float | PWM (0–255) | PID controller output |
| 9 | `freezer_status` | `value` | float | 0/1 | Tapo plug state |
| 10 | `mister_status` | `value` | float | 0/1 | Tapo plug state |
| 11 | `light_status` | `value` | float | 0/1 | Tapo plug state |
| 12 | `water_level_local` | `value` | string | arbitrary | Water level sensor |
| 13 | `night_test_mode` | `value` | float | 0/1 | 0=Night A (fans off), 1=Night B (fans 80) |

### Fan PWM Measurements (RBE — on value change only)

These measurements are logged via Report-by-Exception (RBE) nodes — only written when the value changes. Null periods in the data indicate no change, not zero output.

| # | Measurement | Field | Type | Unit | Source |
|---|-------------|-------|------|------|--------|
| 14 | `fan_pwm_outlet` | `value` | float | PWM (0–255) | Arduino pin 44 |
| 15 | `fan_pwm_impeller` | `value` | float | PWM (0–255) | Arduino pin 45 |
| 16 | `fan_pwm_freezer` | `value` | float | PWM (0–255) | Arduino pin 46 |

### Room Environment (HTTP pull — ~60s interval)

Room conditions are pulled from a remote sensor via HTTP and stored locally.

| # | Measurement | Field | Type | Unit | Source |
|---|-------------|-------|------|------|--------|
| 17 | `room_temperature` | `value` | float | °C | Remote InfluxDB via HTTP |
| 18 | `room_humidity` | `value` | float | % RH | Remote InfluxDB via HTTP |

### Colombian Weather Reference (API poll interval)

Weather data from 4 Colombian highland cities, fetched via OpenWeatherMap API.

| # | Measurement | Field | Type | Unit | Source |
|---|-------------|-------|------|------|--------|
| 19 | `temperature` | `value` | float | °C | Chinchiná (primary) |
| 20 | `humidity` | `value` | float | % RH | Chinchiná (primary) |
| 21 | `temperature_bogota` | `value` | float | °C | Bogotá |
| 22 | `humidity_bogota` | `value` | float | % RH | Bogotá |
| 23 | `temperature_medellin` | `value` | float | °C | Medellín |
| 24 | `humidity_medellin` | `value` | float | % RH | Medellín |
| 25 | `temperature_sonson` | `value` | float | °C | Sonsón |
| 26 | `humidity_sonson` | `value` | float | % RH | Sonsón |

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

### Night A/B comparison
```sql
SELECT mean("value") FROM "local_temperature" WHERE time > now() - 7d AND "value" > 0 GROUP BY time(1h)
```

## Notes

- All measurements use a single field key (`value`) for simplicity
- Boolean states (freezer, mister, light) are stored as float 0/1
- `water_level_local` is stored as string type (sensor returns integer as string)
- `fan_speed` from the Data Logger may be stale at night (retains last PID value even when fans are off/at night mode speed — the PID only runs during daytime)
- `fan_pwm_*` measurements use RBE logging, so gaps represent unchanged values, not missing data
- Query via CLI: `influx -database highland -execute 'YOUR QUERY'`
