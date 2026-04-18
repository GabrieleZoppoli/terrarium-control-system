# Darlingtonia Zeer Pot — Wiring Guide

## ESP32-C3 SuperMini Pinout (as used in this project)

```
                    USB-C
                 ┌─────────┐
                 │  ESP32   │
                 │   C3     │
                 │ SuperMini│
         5V  ◄──┤5V     D8 ├──  (unused)
        GND  ◄──┤GND    D10├──  (unused)
        3V3  ──►┤3V3     D7├──  (unused)
   (unused)  ───┤D6      D4├──► GPIO4  → OneWire bus (DS18B20×2)
   (unused)  ───┤D1      D3├──► GPIO3  → MOSFET gate (pump)
   (unused)  ───┤D0      D2├──► GPIO2  → Moisture sensor ADC
                 │        D5├──► GPIO5  → Float switch
                 └─────────┘
```

**Pin assignments in firmware (`darlingtonia-zeer-pot.ino`):**

| GPIO | Function           | Direction | Notes                          |
|------|--------------------|-----------|--------------------------------|
| 4    | DS18B20 OneWire    | I/O       | Shared bus, 4.7kΩ pull-up to 3V3 |
| 3    | Pump MOSFET gate   | OUTPUT    | HIGH = pump ON, 10kΩ pull-down |
| 5    | NC float switch    | INPUT     | HIGH = water OK, 10kΩ pull-up  |
| 2    | Moisture sensor    | ADC INPUT | 12-bit, capacitive probe       |


## Power Chain

```
┌──────────────┐      ┌──────────────────┐      ┌──────────┐
│  5W Solar    │ USB  │     TP4056       │ B+/B-│  18650   │
│  Panel       ├─────►│  USB-C Charger   ├─────►│  3.7V    │
│  (5V USB-C)  │      │  (w/ protection) │      │  ~3Ah    │
└──────────────┘      └───┬──────────┬───┘      └──────────┘
                     OUT+ │          │ OUT-
                          ▼          ▼
                    ┌─ VBAT rail ──────── GND rail ─┐
                    │  (3.0–4.2 V)                  │
                    │                               │
                    │  C1: 10µF (bulk decoupling)    │
                    │                               │
                    ├──► ESP32 5V pin                │
                    │    (onboard regulator → 3V3)   │
                    │                               │
                    │    C2: 100nF across 3V3/GND   │
                    │                               │
                    └──► MT3608 VIN+ (boosts to 12V) │
                         MT3608 VOUT+ ──► Pump (+)  │
                         (via MOSFET low-side)       │
                                                    │
```

**Key point:** The ESP32-C3 SuperMini has an onboard voltage regulator. Feed raw
VBAT (3.0–4.2V) into the **5V pin** — the board regulates down to 3.3V internally.
The 3V3 pin is an **output** that powers the sensors.


## Wiring — Step by Step

### 1. Power rails on breadboard

Use a half-size breadboard (30 columns). Dedicate:
- **Top power rail (+):** VBAT (red wire from TP4056 OUT+)
- **Top power rail (−):** GND (black wire from TP4056 OUT−)
- **Bottom power rail (+):** 3V3 (orange wire from ESP32 3V3 pin)
- **Bottom power rail (−):** GND (bridge to top GND rail)

### 2. ESP32-C3 SuperMini placement

Straddle the ESP32-C3 across the center channel of the breadboard.
Orient it with USB-C pointing outward for easy programming access.

Connect:
- **5V pin → VBAT rail** (red jumper)
- **GND pin → GND rail** (black jumper)
- **3V3 pin → 3V3 rail** (orange jumper)

### 3. DS18B20 temperature probes (×2, shared OneWire bus)

Both probes connect to the same GPIO4 bus. Each probe cable has 3 wires:

| Wire color (typical) | Function | Connect to       |
|----------------------|----------|------------------|
| Red                  | VDD      | 3V3 rail         |
| Black                | GND      | GND rail         |
| Yellow (or white)    | DQ (data)| GPIO4 bus wire   |

**Critical:** Add a **4.7 kΩ pull-up resistor (R2)** between the DQ bus wire
and the 3V3 rail. Without this, OneWire communication will fail.

```
3V3 ──┬── DS18B20 #1 VDD ── DS18B20 #2 VDD
      │
     [R2 4.7kΩ]
      │
GPIO4 ┼── DS18B20 #1 DQ ─── DS18B20 #2 DQ
      │
GND ──┴── DS18B20 #1 GND ── DS18B20 #2 GND
```

### 4. MOSFET pump driver (IRLZ44N, low-side switch)

The R385 12V pump is switched by an N-channel MOSFET on the **low side** (between
pump negative terminal and GND). The MT3608 boosts VBAT to 12V for the pump.

```
VBAT ──► MT3608 VIN+
         MT3608 VOUT+ (12V) ──► Pump (+)
                                Pump (−) ──► MOSFET Drain
                                              MOSFET Source ──► GND
GPIO3 ──┬──────────► MOSFET Gate
        │
       [R4 10kΩ]     (pull-down: keeps pump OFF when ESP sleeps/resets)
        │
       GND
```

**IRLZ44N pinout (face toward you, legs down):**
```
    ┌───┐
    │   │
 G  D  S
(1) (2) (3)
```
- Pin 1 (Gate): GPIO3 + R4 pull-down
- Pin 2 (Drain): Pump (−) terminal
- Pin 3 (Source): GND rail

**Flyback diode (SS14 / 1N5819):** Place across the pump terminals to protect
the MOSFET from inductive voltage spikes when the pump turns off.
- **Cathode** (band side) → Pump (+) / 12V side
- **Anode** → Pump (−) / MOSFET drain side

### 5. Float switch (NC, side-mount)

The float switch is a normally-closed (NC) contact mounted in the reservoir.
When the float is up (water present), the switch opens → GPIO5 = HIGH → pump OK.
When the float drops (low water), the switch closes → GPIO5 = LOW → pump blocked.

```
3V3
 │
[R3 10kΩ]   (pull-up)
 │
GPIO5 ──────┤ NC Float Switch ├──── GND
```

- Float up (water OK): switch open, GPIO5 = HIGH (pulled to 3V3 through R3)
- Float down (low water): switch closed, GPIO5 = LOW (pulled to GND through switch)

### 6. Capacitive moisture sensor

3-wire analog sensor. **Must be 3.3V-compatible** (not 5V-only).

| Sensor wire | Connect to |
|-------------|------------|
| VCC         | 3V3 rail   |
| GND         | GND rail   |
| A (analog)  | GPIO2      |

No pull-up/pull-down needed — the sensor outputs a DC voltage proportional to
moisture level. The ESP32 reads it with 12-bit ADC.


## Complete Bill of Materials (discrete components on breadboard)

| Ref | Value   | Purpose                              |
|-----|---------|--------------------------------------|
| R2  | 4.7 kΩ  | OneWire pull-up (DS18B20 bus)        |
| R3  | 10 kΩ   | Float switch pull-up to 3V3          |
| R4  | 10 kΩ   | MOSFET gate pull-down to GND         |
| C1  | 10 µF   | Bulk decoupling across VBAT/GND      |
| C2  | 100 nF  | High-freq decoupling across 3V3/GND  |
| D1  | SS14    | Flyback protection across pump       |
| Q1  | IRLZ44N | N-MOSFET, low-side pump switch       |


## Quick-Start Checklist

1. [ ] Solder header pins on ESP32-C3 SuperMini (if not pre-soldered)
2. [ ] Place ESP32 on breadboard, connect 5V/GND/3V3 to rails
3. [ ] Flash firmware via USB-C (`platformio run --target upload`)
4. [ ] Wire R2 (4.7k) + one DS18B20 probe to GPIO4 — verify temp reading via serial
5. [ ] Add second DS18B20 to same bus — verify both sensors auto-identify
6. [ ] Wire MOSFET + R4 (10k pull-down) + pump + flyback diode
7. [ ] Test pump: `digitalWrite(3, HIGH)` in serial monitor
8. [ ] Wire float switch + R3 (10k pull-up) to GPIO5
9. [ ] Wire moisture sensor to GPIO2, verify ADC readings
10. [ ] Connect TP4056 + 18650 battery, disconnect USB
11. [ ] Verify system wakes from deep sleep, reads sensors, reports MQTT
12. [ ] Connect solar panel to TP4056 USB input, deploy outdoors


## Schematic

See `schematic-sections.pdf` (6-page CircuiTikZ/LaTeX schematic).
