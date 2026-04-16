---
title: "PID Controller"
description: "Gain-scheduled PID algorithm with three-regime fan control"
---


## Overview

The terrarium uses a discrete PID (Proportional-Integral-Derivative) controller with gain scheduling to modulate fan speed based on the difference between target and actual humidity. This provides smooth, responsive control compared to simpler on/off (bang-bang) approaches, while gain scheduling prevents oscillation near the setpoint.

## Error Convention

```
humidity_diff = target_humidity − current_humidity    (from Humidity tab)
error = −humidity_diff = current_humidity − target_humidity
```

- **Positive error** (current > target = too humid) → increase fan speed
- **Negative error** (current < target = too dry) → decrease fan speed (let mister handle it)

## PID Equation

The controller output at each time step is:

```
u(t) = g × Kp × e(t)  +  Ki × ∫₀ᵗ e(τ)dτ  +  g × Kd × de/dt
```

where *g* is the gain factor from the gain scheduling function (see below).

In discrete form (computed every control cycle, typically ~10–15 seconds):

```
P = g × Kp × error
I = Ki × integral_accumulator
D = g × Kd × filtered_derivative

fan_speed = BASE_SPEED + P + I + D
```

## Tuning Parameters

| Parameter | Value | Effect |
|-----------|-------|--------|
| **Kp** | 50 | Proportional gain — primary response to humidity deviation |
| **Ki** | 0.5 | Integral gain — corrects steady-state offset over time |
| **Kd** | 10 | Derivative gain — dampens oscillation, reacts to rate of change |
| **BASE_SPEED** | 50 | Resting fan speed at zero error (~20% duty cycle) |
| **MIN_SPEED** | 40 | Minimum fan PWM (~16%) — ensures continuous air circulation |
| **MAX_SPEED** | 230/255 | Time-of-day cap: 255 (04:00–07:00 morning blast), then weekday/weekend caps (see below) |

These gains are stored in flow context (persists across Node-RED restarts) and are adjustable at runtime via the Node-RED Dashboard UI text input (format: `Kp,Ki,Kd`).

## Gain Scheduling

With fixed Kp=50, the controller exhibited rapid ±25 PWM oscillations when humidity hovered within ±0.5% of the setpoint. The proportional term alone produced swings large enough to overshoot in alternating directions.

The gain scheduling function scales the effective Kp and Kd based on error magnitude:

```
|error| ≤ 1.5%:  gainFactor = 0.15    (effective Kp = 7.5)
|error| ≥ 4.0%:  gainFactor = 1.0     (effective Kp = 50)
Between:          gainFactor = 0.15 + (|error| - 1.5) × (0.85 / 2.5)
                             = linear interpolation
```

This provides:
- **Gentle control near target** (g=0.15): Small, smooth adjustments when humidity is within 1.5% of setpoint
- **Aggressive response to large deviations** (g=1.0): Full PID authority when humidity is 4%+ from target
- **Smooth transition**: Linear interpolation prevents discontinuous jumps in control effort

The integral term (Ki) is NOT scaled by the gain factor — this ensures the integral continues to accumulate normally and corrects steady-state offset regardless of the current error magnitude.

The node status displays the current gain factor as `g:0.15` through `g:1.00` for real-time monitoring.

## Anti-Windup Protection

Integral windup occurs when sustained large errors cause the integral term to accumulate to extreme values, leading to large overshoot when the error finally reverses. Two mechanisms prevent this:

### 1. Integral Clamping

```
I_MAX = 120 / Ki     (= 240 with Ki=0.5)

integral = clamp(integral, -I_MAX, +I_MAX)
```

This limits the integral's contribution to ±120 PWM units.

### 2. Near-Target Decay

When the error magnitude is less than 2.0% RH, the integral decays at 5% per second:

```
if |error| < 2.0:
    integral *= (1 - 0.05 × dt)
```

This prevents the integral from slowly creeping the fan speed away from optimal when conditions are stable. The 5%/s decay rate (increased from earlier 2%/s) provides faster wind-down after humidity spikes.

## Derivative Filtering

Raw derivatives amplify sensor noise. A first-order exponential low-pass filter smooths the derivative term:

```
α = 0.12    (smoothing factor: 0=heavy filter, 1=no filter)

filtered_derivative = α × raw_derivative + (1-α) × previous_filtered_derivative

where:
    raw_derivative = (error - previous_error) / dt
```

The α value of 0.12 provides heavy noise reduction (more aggressive than the previous 0.25) while preserving response to genuine rapid humidity changes (e.g., mister activation, door opening).

## Rate Limiting

To prevent abrupt fan speed transitions that could disturb the terrarium environment:

```
max_change = min(20, max(10, |error| × 3))

if |fan_speed - previous_speed| > max_change:
    fan_speed = previous_speed + sign(delta) × max_change
```

The maximum change is capped at 20 PWM per cycle to protect the serial communication link from command flooding. This allows faster transitions during large disturbances while maintaining smooth behavior near the setpoint.

## Output Mapping

```
raw_output = BASE_SPEED + P + I + D
fan_speed  = clamp(round(raw_output), MIN_SPEED, MAX_SPEED)
           = clamp(round(raw_output), 40, MAX_SPEED)

MAX_SPEED schedule:
  04:00–07:00 (all days):  255  (morning humidity blast)
  Weekday after 07:00:     06:30–08:00 → 180, 08:00–17:00 → 255, else → 230
  Weekend after 07:00:     07:00–10:00 → 180, 10:00–17:00 → 255, else → 230
```

The fan speed is applied to the outlet fan (pin 45) and impeller fan (pin 46) simultaneously via serial commands (`P45,<value>` and `P46,<value>`). The evaporator fan (pin 44) and circulation fan (pin 12) operate independently based on compressor hysteresis control.

## Guard Conditions

The PID controller output is blocked (returns null) when:

1. **Door safety active** — all fans are forced to 0 by the door safety controller
2. **Manual mode is active** — operator has set a fixed fan speed via the Dashboard UI
3. **Mister is ON** — safety interlock stops all fans during misting
4. **Night mode** — fans off from midnight to 04:00 (PID active 04:00–00:00)
5. **No data** — humidity difference is undefined (sensor offline)
6. **Time gap** — dt > 120s (NR restart, prevents integral spike from stale timestamps)

## Control Hierarchy

```
Priority 0 (highest): Door safety        → all fans stop (0 PWM)
Priority 1:           Manual override     → fixed user-set speed
Priority 2:           Mister interlock    → all fans stop (0 PWM)
Priority 3:           Night mode          → fans off (midnight to 04:00)
Priority 4 (lowest):  PID automatic       → computed fan speed
```

Note: The A/B night experiment is suspended — Night Mode always outputs 0 during midnight–04:00. The A/B code is preserved in the function node as a comment block with reactivation instructions.

## Typical Behavior

| Condition | Error | g | P | I (typical) | D | Output | Fan Speed |
|-----------|-------|---|---|-------------|---|--------|-----------|
| At setpoint | 0 | 0.15 | 0 | ~0 | 0 | 50 | 50 (~20%) |
| Slightly humid (+1% RH) | +1 | 0.15 | +7.5 | ~+3 | ~0 | 60 | 60 (~24%) |
| Moderately humid (+3% RH) | +3 | 0.76 | +114 | ~+10 | ~+5 | 179 | 179 (~70%) |
| Very humid (+5% RH) | +5 | 1.0 | +250 | ~+15 | ~+8 | 230 | 230 (MAX) |
| Slightly dry (−1% RH) | −1 | 0.15 | −7.5 | ~−3 | ~0 | 40 | 40 (MIN) |
| Rapid humidity rise | +3, rising | 0.76 | +114 | ~+8 | +16 | 188 | 188 (~74%) |

## Monitoring

The PID controller publishes status to the Node-RED Dashboard UI and sets visual node status:

```
Direction indicator: ▲ (fan speed increasing), ▼ (decreasing), ● (stable)
Color: green (|diff| < 2%), yellow (|diff| < 5%), red (|diff| ≥ 5%)
Text: "▲ Δ3.2% → 55% [P:48 I:12 D:5] g:0.76"
```

All PID components (P, I, D, total output, integral accumulator, gain factor) are visible in the Dashboard for real-time diagnostics.
