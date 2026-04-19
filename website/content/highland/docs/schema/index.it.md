---
title: "Schema delle misure InfluxDB"
description: "Tutte le 32 misure registrate dal sistema"
---


**Database**: `highland`
**Retention policy di default**: `standard_highland_retention` (365 giorni)
**Intervallo di scrittura**: 60 secondi (Data Logger), variabile per le altre fonti

## Retention policy

| Policy | Durata | Default |
|--------|--------|---------|
| `autogen` | illimitata | No |
| `one_year_policy` | 365 giorni | No |
| `standard_highland_retention` | 365 giorni | Sì |

## Misure

### Misure principali del terrario (Data Logger — intervallo 60 s)

Queste 16 misure sono scritte dal function node Data Logger centralizzato nel tab Utilities, che legge dal global context di Node-RED.

| # | Misura | Campo | Tipo | Unità | Fonte |
|---|--------|-------|------|-------|-------|
| 1 | `local_temperature` | `value` | float | °C | SHT35 via ESP8266/MQTT |
| 2 | `local_humidity` | `value` | float | % UR | SHT35 via ESP8266/MQTT |
| 3 | `vpd` | `value` | float | kPa | Calcolato (formula di Magnus) |
| 4 | `target_temperature_computed` | `value` | float | °C | Media meteo (limitata a 12–24 °C) |
| 5 | `target_humidity_computed` | `value` | float | % UR | Media meteo (limitata a 70–90 %) |
| 6 | `difference_temperature` | `value` | float | °C | target − misurata |
| 7 | `difference_humidity` | `value` | float | % | target − misurata |
| 8 | `fan_speed` | `value` | float | PWM (0–255) | Output del controllore PID |
| 9 | `freezer_status` | `value` | float | 0/1 | Stato presa Tapo (compressore) |
| 10 | `mister_status` | `value` | float | 0/1 | Stato presa Tapo |
| 11 | `light_status` | `value` | float | 0/1 | Stato presa Tapo |
| 12 | `water_level_local` | `value` | string | arbitraria | Sensore ultrasonico del livello d'acqua |
| 13 | `night_test_mode` | `value` | float | 0/1/−1 | 0=Notte A (ventole off), 1=Notte B (ventole 80), −1=sospeso |
| 14 | `power_consumption` | `value` | float | Watt | Meross MSS310 (via daemon MQTT, ogni 2 s) |
| 15 | `wbt_shutdown_active` | `value` | float | 0/1 | Stato del gate di shutdown ventola per wet-bulb |
| 16 | `pid_control_mode` | `value` | float | 0/1 | 0=PID umidità, 1=PID temperatura |

### Misure PWM ventole (RBE — solo al cambio di valore)

Queste misure sono registrate con nodi Report-by-Exception (RBE) — scritte solo quando il valore cambia. I periodi vuoti indicano nessun cambiamento, non output zero.

| # | Misura | Campo | Tipo | Unità | Fonte |
|---|--------|-------|------|-------|-------|
| 15 | `fan_pwm_outlet` | `value` | float | PWM (0–255) | Arduino pin 45 |
| 16 | `fan_pwm_impeller` | `value` | float | PWM (0–255) | Arduino pin 46 |
| 17 | `fan_pwm_freezer` | `value` | float | PWM (0–255) | Arduino pin 44 |
| 18 | `fan_pwm_circulation` | `value` | float | PWM (0–255) | Arduino pin 12 |

### Ambiente stanza (pull HTTP — ~60 s)

Le condizioni della stanza sono recuperate da un sensore remoto (DietPi RPi su 192.168.1.94) via HTTP e salvate localmente.

| # | Misura | Campo | Tipo | Unità | Fonte |
|---|--------|-------|------|-------|-------|
| 19 | `room_temperature` | `value` | float | °C | InfluxDB remoto via HTTP |
| 20 | `room_humidity` | `value` | float | % UR | InfluxDB remoto via HTTP |

### Eventi di nebulizzazione (event-driven — per ciclo)

Registrati all'istante in cui parte un ciclo di nebulizzazione, a differenza del `mister_status` campionato che può mancare cicli brevi.

| # | Misura | Campo | Tipo | Unità | Fonte |
|---|--------|-------|------|-------|-------|
| 21 | `mist_event` | `value` | float | 1 | Tab Humidity, event-driven al trigger |

### Salute Arduino (parser seriale — ~2 s)

| # | Misura | Campo | Tipo | Unità | Fonte |
|---|--------|-------|------|-------|-------|
| 22 | `arduino_status` | `value` | float | 0/1 | Heartbeat "alive" |

### Riferimento meteo colombiano (poll API)

Dati meteo di 4 città d'alta quota colombiane, via OpenWeatherMap.

| # | Misura | Campo | Tipo | Unità | Fonte |
|---|--------|-------|------|-------|-------|
| 23 | `temperature` | `value` | float | °C | Chinchiná (primaria) |
| 24 | `humidity` | `value` | float | % UR | Chinchiná (primaria) |
| 25 | `temperature_bogota` | `value` | float | °C | Bogotá |
| 26 | `humidity_bogota` | `value` | float | % UR | Bogotá |
| 27 | `temperature_medellin` | `value` | float | °C | Medellín |
| 28 | `humidity_medellin` | `value` | float | % UR | Medellín |
| 29 | `temperature_sonson` | `value` | float | °C | Sonsón |
| 30 | `humidity_sonson` | `value` | float | % UR | Sonsón |

**Totale**: 32 misure su tutte le fonti.

## Query comuni

### Condizioni attuali
```sql
SELECT last("value") FROM "local_temperature"
SELECT last("value") FROM "local_humidity"
SELECT last("value") FROM "vpd"
```

### Ultime 24 ore di temperatura
```sql
SELECT mean("value") FROM "local_temperature" WHERE time > now() - 24h GROUP BY time(5m)
```

### Escursione giornaliera
```sql
SELECT min("value"), max("value"), mean("value") FROM "local_temperature" WHERE time > now() - 24h
```

### Consumo elettrico
```sql
SELECT mean("value") FROM "power_consumption" WHERE time > now() - 7d GROUP BY time(1h)
```

### Conteggio giornaliero nebulizzazioni (event-driven)
```sql
SELECT count("value") FROM "mist_event" WHERE time > now() - 24h
```

### Confronto Notte A/B (storico)
```sql
SELECT mean("value") FROM "local_temperature" WHERE time > '2026-02-05' AND time < '2026-02-19' GROUP BY time(1h)
```

## Note

- Tutte le misure usano un unico nome di campo (`value`) per semplicità
- Gli stati booleani (freezer, mister, light) sono salvati come float 0/1
- `water_level_local` è stringa (il sensore restituisce un intero come stringa)
- `fan_speed` dal Data Logger può risultare stantio di notte (mantiene l'ultimo valore PID anche a ventole spente — il PID gira solo fra le 06:30 e le 00:00)
- Le misure `fan_pwm_*` usano logging RBE: i buchi nei grafici rappresentano valori invariati, non dati mancanti
- `night_test_mode` = −1 indica che l'esperimento A/B è sospeso (stato attuale)
- `power_consumption` viene registrato ogni 2 secondi tramite un daemon Meross persistente che pubblica su MQTT
- Query da CLI: `influx -database highland -execute 'LA TUA QUERY'`
- `mist_event` è event-driven (una scrittura per ciclo), a differenza di `mister_status` che campiona ogni 60 s e può mancare la finestra di 35 s della nebulizzazione. Usa `mist_event` per conteggi accurati; `mister_status` prima del 2026-02-24 sotto-conta di circa il 18 %
- Nota: `curl -sG` (GET) restituisce risultati vuoti — usa POST o la CLI
