---
title: "Light curve C: a raised cosine for the cloud-forest cabinet"
date: 2026-05-04T23:30:00+02:00
description: "An afternoon humidity creep on a clear May day pushed me to replace the cabinet's three-step LED schedule (40-60-40) with a smooth raised-cosine curve peaking at 70 % at solar noon. About 23 % more daily light, redistributed to keep the cabinet warmer through the late-afternoon RH danger window. Three-week experiment; this post will be updated 2026-05-25 with the result."
tags: ["build-log", "highland-terrarium", "lighting", "control-loops", "experiment"]
showReadingTime: true
---

I noticed a slow afternoon humidity creep on the cabinet today. Target was at the 75 % floor (Colombian curve, clamped) and the cabinet was tracking it neatly through morning and noon — then around 15:00 the cabinet RH started rising again despite the PID having the outlet fans pinned at PWM 255. The "wait, what's capping the fan?" hunt was a red herring: nothing was. The fans were at max. The PID was doing all it could.

The fix turned out to be **upstream of the fans, in the LED schedule.**

## What was actually happening

Pulling the data for that window (13:00–17:00 CEST):

```
CEST    cabHumi%   cabT°C    Genoa room
14:30   79.82      21.95     22.96 / 56.7%
15:00   80.32      21.70     23.08 / 56.8%
15:30   81.49      21.44  ←  23.11 / 57.2%   cabinet COOLING
16:00   81.77      21.43     23.17 / 57.4%
16:30   81.88      21.47     23.26 / 57.4%
```

The cabinet *cooled* by 0.5 °C between 14:30 and 16:00, while the room kept warming. Plotting actual vapour pressure (Magnus formula) shows the absolute moisture was essentially flat — slowly *decreasing*, in fact. The fans were doing their job. **The relative humidity rise was a thermodynamic artefact of falling temperature** at near-constant water content.

So the next question is: why did the cabinet cool while the lights were still on?

The answer is in the LED schedule. The current schedule is a step function:

- 0 → 40 % over the dawn ramp (06:39 → 07:09)
- 40 % plateau through morning
- 40 → 60 % at "midday-up" (today: 11:44)
- 60 % plateau across solar noon (11:44 → 14:47)
- 60 → 40 % at "midday-down" (today: 14:47)
- 40 % plateau through afternoon
- 40 → 0 % at the dusk ramp (19:21 → 19:51)

Each step is a 30 min linear ramp; the plateaus are flat. The 60 % plateau lasts about 3 hours centred on solar noon. **The moment it drops back to 40 %, LED heat input falls — and the cabinet starts cooling.** That's exactly what I saw at 14:47 today, with the RH following 30–60 minutes later as the temperature drop translated through Magnus.

## Cloud-forest light is not a step function

The natural sun curve at the equator is essentially a half-cosine: zero at sunrise, peak at solar noon, zero at sunset, with the steep zenith angles of low latitudes giving a sharp peak rather than a flat plateau. The cabinet's plants are highland cloud forest specialists — *Heliamphora* from the tepuis, *Dracula* and *Masdevallia* from the Andes, *Dendrobium cuthbertsonii* from New Guinea highlands — habitats roughly between 1500–2500 m at low latitudes. None of these plants experience a flat midday plateau in their natural light environment. They get a sun curve that rises smoothly through morning, peaks above zenith, and decays smoothly through afternoon.

So both *physiologically* (smooth = natural, plateaus = artificial) and *engineering-wise* (plateau-then-drop creates the RH cliff I just observed), the step schedule is suboptimal.

## Three candidate curves

I evaluated three shapes:

{{< figure src="curve-comparison.png" caption="Three candidate slider schedules over today's photoperiod (sunrise 07:09 — sunset 19:21, day length 12.2 h). A is the current step schedule. B is a pure half-cosine peaking at 70 % at solar noon, dropping to 0 at the boundaries. C is a 'raised cosine' with a 35 % floor and a 70 % noon peak — the smooth shape but without the dim morning/evening of B." >}}

| Curve | Shape | Peak | Min | Daily light dose (slider·h) | Δ vs current |
|---|---|---|---|---|---|
| **A** | step | 60 | 40 | 569 | baseline |
| **B** | pure cosine | 70 | 0 | 544 | **−4.5 %** |
| **C₆₀** | raised cosine | 60 | 35 | 621 | +9 % |
| **C₆₅** | raised cosine | 65 | 35 | 660 | +16 % |
| **C₇₀** *(adopted)* | raised cosine | 70 | 35 | 699 | **+23 %** |

{{< figure src="delta-auc.png" caption="Daily light dose (area under the slider curve) for each variant. The chosen variant — raised cosine with floor 35 %, peak 70 % — delivers about 23 % more total daily light than the current step schedule, redistributed so that the late-afternoon shoulder stays significantly higher than the current 40 % plateau." >}}

The +23 % figure looks alarming on paper, but the actual photon flux still sits well below tropical-noon irradiance — the cabinet's Mean Well drivers have a hardware screw cap at roughly 60 % of rated current, so a slider value of 70 means roughly 70 % × 60 % = 42 % of the LED's rated output. The plants receive a generous but not extreme dose, and the species in the cabinet (Heliamphora at the top under the brightest puck, Dracula and Masdevallia in the lower shade tier) tolerate considerably more than that in the wild.

I considered B (pure cosine) seriously because it is the most physically faithful shape, but the dim morning was a problem: at 09:00 it sits at slider 32, *below* the current plateau of 40, and the cabinet plants are clearly happier with at least a 40-baseline. So C — keeping the morning baseline at 35 (slightly *below* current, which I lowered intentionally to keep the AUC change reasonable) and rising smoothly to a 70 peak at noon — is the compromise that best fits both the engineering goal and the cloud-forest analogy.

## Where the cabinet currently sits

For context, here's the recent baseline from 21 days of telemetry:

{{< figure src="temperature-3w.png" caption="Cabinet temperature vs target (Colombian curve, lat 4.98°N) by hour-of-day, mean ± 95 % CI over the last 3 weeks. The cabinet tracks the target reasonably well overnight, undershoots in the early morning (warming faster than target), and the daytime plateau sits around 21 °C — well below the 24 °C daytime target." >}}

{{< figure src="humidity-3w.png" caption="Cabinet humidity vs target by hour-of-day, mean ± 95 % CI over the last 3 weeks. The clamps (75 % floor, 95 % cap, both set this week) are visible as the dotted lines. The cabinet runs 5–8 % above target through most of the day — the band the new light curve is trying to compress." >}}

{{< figure src="pwm-outlet-3w.png" caption="Outlet fan PWM (P45) by hour-of-day, mean ± 95 % CI over the last 3 weeks. The morning blast (04:00–07:00 = MAX 255) is visible, then PID-driven activity through the day with a clear daytime average around 80–120 PWM. After 20:00 the lights-off fan gate forces outlets to 0." >}}

The interesting band on the humidity chart is **15:00–18:00** — the peak rises slightly above the 90 % line right when the LED step schedule has just dropped from 60 to 40. That is precisely the artefact the new curve is meant to fix.

## What I implemented

A single function node on the Lights tab, fired by a 60-second interval inject (and once at NR start). It reads `payload.photo_sunrise` and `payload.photo_sunset` from the Photoperiod Calculator, then for the current minute computes:

```
slider(t) = max(35, 35 + 35 × cos(π × (t − solar_noon) / day_length))
```

…and emits the inverted PWM value (255 → 0 mapping) to the existing `pin8_writer_001`, which handles serial output and door-safety override. The two old `dynamic-dimmer` nodes are disabled (not deleted — easy to revert). The Tapo on/off events at the photoperiod boundaries are unchanged: the smartplug still cycles power to the LED drivers on a daily schedule, the curve only handles the dim PWM signal *within* that on-window.

The whole change is one new function, one new inject, two disabled nodes, and a backup of `flows.json` for rollback. No new dependencies, no schema changes, no Grafana dashboard work.

## What I expect to see

If the diagnosis is right, three things should change in the next 21 days of telemetry:

1. **The 15:00–18:00 humidity bump compresses.** The cabinet should hold closer to target through the afternoon shoulder.
2. **Cabinet temperature stays slightly higher in the late afternoon** (the LED is still feeding heat past the old midday-down moment).
3. **Outlet fan PWM increases slightly during 14:00–17:00** because the PID has more thermal load to dump — but that's a price worth paying to keep the RH from drifting up.

Things to watch out for that would mean the change was a mistake:

- **Cabinet daytime temperature exceeds the 24 °C target** more often. With +23 % daily light dose, the freezer might have to work harder, and on the warmest days the cabinet could exceed the daytime target. If `target_temperature_computed` is regularly held below local temperature for >30 % of the daytime window, the peak is too high.
- **Lower-tier plants show light stress** — bleaching on Dracula leaves, leaf curl on Masdevallia. The lower shade tier should be unaffected by the slider change (they live below the polycarbonate shelf), but a watch is in order.
- **Driver running temperatures rise**. The four Logic Puck V3 each have 140 mm pin heatsinks with 12 V fans; they've been comfortable at 60 % screw cap. A slider of 70 keeps them within the screw-cap headroom but they will run somewhat warmer.

## Three weeks from today: what this post will look like

This is an experiment, not a finished change. **On 2026-05-25 I will re-run the chart-generation script with three weeks of post-curve telemetry** and update this post with:

- The same hour-of-day mean-and-CI plots, *post*-curve, side-by-side with the pre-curve baseline above.
- Whether the 15:00–18:00 RH bump compressed.
- Whether daytime cabinet temperature stayed within target.
- Whether anything ugly showed up in the plants.

If the answer is broadly "yes, it works", the curve stays. If not, I'll either drop the peak (try C₆₅), tweak the floor, or fall back to the step schedule with a wider 60 % plateau.

The data needed to make that call already exists in InfluxDB; the script lives at `~/terrarium-analysis/light_curve_charts.py` on the Pi. The point of the post-by-post structure is to make the experiment legible — *here is the hypothesis, here is the data, here is what I expect, here is what actually happened* — rather than buried in commit messages.

See you in three weeks.
