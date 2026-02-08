# PID Controller for Humidity-Based Fan Management

## Overview

The terrarium uses a discrete PID (Proportional-Integral-Derivative) controller to modulate fan speed based on the difference between target and actual humidity. This provides smooth, responsive control compared to simpler on/off (bang-bang) approaches.

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
u(t) = Kp × e(t)  +  Ki × ∫₀ᵗ e(τ)dτ  +  Kd × de/dt
```

In discrete form (computed every control cycle, typically ~10–15 seconds):

```
P = Kp × error
I = Ki × integral_accumulator
D = Kd × filtered_derivative

fan_speed = BASE_SPEED + P + I + D
```

## Tuning Parameters

| Parameter | Value | Effect |
|-----------|-------|--------|
| **Kp** | 15 | Proportional gain — primary response to humidity deviation |
| **Ki** | 0.08 | Integral gain — corrects steady-state offset over time |
| **Kd** | 8 | Derivative gain — dampens oscillation, reacts to rate of change |
| **BASE_SPEED** | 72 | Resting fan speed at zero error (~28% duty cycle) |
| **MIN_SPEED** | 40 | Minimum fan PWM (~16%) — ensures continuous air circulation |
| **MAX_SPEED** | 204 | Maximum fan PWM (~80%) — noise reduction cap |

These gains were determined empirically through iterative testing. They are adjustable at runtime via the Node-RED Dashboard UI text input (format: `Kp,Ki,Kd`).

## Anti-Windup Protection

Integral windup occurs when sustained large errors cause the integral term to accumulate to extreme values, leading to large overshoot when the error finally reverses. Two mechanisms prevent this:

### 1. Integral Clamping

```
I_MAX = 120 / Ki     (= 1500 with Ki=0.08)

integral = clamp(integral, -I_MAX, +I_MAX)
```

This limits the integral's contribution to ±120 PWM units.

### 2. Near-Target Decay

When the error magnitude is less than 1.0% RH, the integral decays at 2% per second:

```
if |error| < 1.0:
    integral *= (1 - 0.02 × dt)
```

This prevents the integral from slowly creeping the fan speed away from optimal when conditions are stable.

## Derivative Filtering

Raw derivatives amplify sensor noise. A first-order exponential low-pass filter smooths the derivative term:

```
α = 0.25    (smoothing factor: 0=heavy filter, 1=no filter)

filtered_derivative = α × raw_derivative + (1-α) × previous_filtered_derivative

where:
    raw_derivative = (error - previous_error) / dt
```

The α value of 0.25 provides substantial noise reduction while preserving response to genuine rapid humidity changes (e.g., mister activation, door opening).

## Rate Limiting

To prevent abrupt fan speed transitions that could disturb the terrarium environment:

```
max_change = max(10, |error| × 3)

if |fan_speed - previous_speed| > max_change:
    fan_speed = previous_speed + sign(delta) × max_change
```

This allows faster transitions during large disturbances while maintaining smooth behavior near the setpoint.

## Output Mapping

```
raw_output = BASE_SPEED + P + I + D
fan_speed  = clamp(round(raw_output), MIN_SPEED, MAX_SPEED)
           = clamp(round(raw_output), 40, 204)
```

The fan speed is applied to the outlet fan (pin 44) and impeller fan (pin 45) simultaneously. The freezer fan (pin 46) operates independently based on freezer hysteresis control.

## Guard Conditions

The PID controller output is blocked (returns null) when:

1. **Manual mode is active** — operator has set a fixed fan speed via the Dashboard UI
2. **Mister is ON** — safety interlock stops all fans during misting
3. **Night mode** — fans run at fixed speed (0 or 80 PWM depending on A/B test) instead of PID
4. **No data** — humidity difference is undefined (sensor offline)
5. **Time gap** — dt > 120s (NR restart, prevents integral spike from stale timestamps)

## Control Hierarchy

```
Priority 1 (highest): Manual override    → fixed user-set speed
Priority 2:           Mister interlock   → all fans stop (0 PWM)
Priority 3:           Night mode         → fixed 0 or 80 PWM (A/B test)
Priority 4 (lowest):  PID automatic      → computed fan speed
```

## Typical Behavior

| Condition | Error | P | I (typical) | D | Output | Fan Speed |
|-----------|-------|---|-------------|---|--------|-----------|
| At setpoint | 0 | 0 | ~0 | 0 | 72 | 72 (~28%) |
| Slightly humid (+2% RH) | +2 | +30 | ~+5 | ~0 | 107 | 107 (~42%) |
| Very humid (+5% RH) | +5 | +75 | ~+15 | ~+8 | 170 | 170 (~67%) |
| Slightly dry (−2% RH) | −2 | −30 | ~−5 | ~0 | 37 | 40 (MIN) |
| Rapid humidity rise | +3, rising | +45 | ~+8 | +16 | 141 | 141 (~55%) |

## Monitoring

The PID controller publishes status to the Node-RED Dashboard UI and sets visual node status:

```
Direction indicator: ▲ (fan speed increasing), ▼ (decreasing), ● (stable)
Color: green (|diff| < 2%), yellow (|diff| < 5%), red (|diff| ≥ 5%)
Text: "▲ Δ3.2% → 55% [P:48 I:12 D:5]"
```

All PID components (P, I, D, total output, integral accumulator) are visible in the Dashboard for real-time diagnostics.
