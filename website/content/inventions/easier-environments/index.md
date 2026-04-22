---
title: "Fog Shelves"
description: "Glass shelves in the living room — ultrasonic misters on a Raspberry-Pi-driven hysteresis RH loop (~80 %), switched via Tapo P100 plugs, BME280 + SHT35 sensors"
---

Not every plant needs a 1.5 m climate-controlled cabinet. Several species in the collection live on a set of open glass shelves in the living room. Each shelf has an ultrasonic mister with a reservoir, plugged into a Tapo P100 smart plug; a second Raspberry Pi polls a Bosch BME280 and an SHT35 on the shelf and toggles the plug on a hysteresis loop around ~80 % RH. No chiller, no PID, no Grafana — but not a dumb timer either.

The room handles temperature passively (18–24 °C year-round, Genoese Mediterranean climate); ambient daylight plus a plain full-spectrum LED strip provides the photoperiod.

The contrast with the highland cabinet is the point: these are the plants whose preference envelope sits inside a Genoese living room if you add *water vapour* and leave temperature alone. Less engineering than the cabinet, more than a wet tray on the windowsill.

## What's on the shelves

A rotating lineup. Plants that outgrow their spot or start wanting cooler nights migrate upstairs into the highland cabinet; newcomers that don't need cloud-forest temperatures land here first and stay if they thrive.

| Shelf resident | Source | Why it's here rather than in the cabinet |
|---|---|---|
| *Vanda coerulescens* | Celandroni Orchidee | Warm-intermediate vandaceous — tolerates room temperatures. |
| *Neostylis* Lou Sneary (*N. falcata* × *Rhynchostylis coelestis* var. *coerulea*) | Celandroni Orchidee | Hybrid inherits the warmer tolerance of *Rhynchostylis*. |
| *Darwinara* Charm 'Blue Moon' (*Neofinetia × Vanda × Rhynchostylis × Ascocentrum*) | Claessen Orchids & Plants | Blue-violet flowers; the blue pigmentation tracks with cooler *nights* specifically, which the mister-fog microclimate provides without actual chilling. |
| Mexican *Pinguicula* (*agnata*, *ehlersiae*, *esseriana*, *gypsicola* × *moctezumae*, *rotundiflora*, *rectifolia*, *Marciano*, *Apasionada*, *Red Starfish* etc.) | Un Angolo di Deserto · Giardino Carnivoro | Mexican pings want bright light + dry roots + high humidity during the rainy season; the fog gives them humidity without soaking. |
| *Cephalotus follicularis* + f. 'Hummer's Giant' | Giardino Carnivoro · David Maccioni | Hates the highland night minimum (13 °C) and the still air; prefers a drier, brighter, more ventilated spot. |
| *Phalaenopsis* species — *finleyi*, *lowii*, *gibbosa*, *wilsonii*, *parishii* | Celandroni Orchidee | Warm-growing botanical *Phalaenopsis*, miniature in habit. Happier in intermediate conditions than in the cloud forest. |
| *Angraecum didieri* | Growlist | Madagascan miniature; intermediate-warm, intolerant of the highland night drop. |
| *Bulbophyllum makoyanum* | Gift | Southeast-Asian lowland to mid-elevation; the cabinet is too cool overnight for it. |

## The hardware

- **Ultrasonic mister**: generic 24 V piezoelectric disc with a refillable reservoir, switched by a Tapo P100 smart plug. Replace the disc every ~18 months; cartridges are cheap and the unit itself is cheaper.
- **Sensors**: a Bosch BME280 and an SHT35 colocated on the shelf. Two sensors for redundancy and a sanity cross-check — RH sensors drift, and getting the setpoint wrong by 10 % is the difference between "happy plants" and "mould".
- **Controller**: a second Raspberry Pi (not the highland one) runs a small Python loop — reads the two sensors, averages, and toggles the Tapo plug via the PyP100 library to hold RH around 80 % on hysteresis. No InfluxDB, no dashboard, no Node-RED; a setpoint, a dead-band, and a log file.
- **Light**: a plain full-spectrum LED strip along the top of each shelf, on a wall socket with a dumb daily timer (no dawn ramps, no PID, no Node-RED).
- **Everything else**: room air, room temperature, windowsill light where applicable.

The whole setup costs a fraction of the highland cabinet. That's also the mental model: *the cabinet is where you invest full-stack engineering when the species demands it; the fog shelves are where you invest just enough when the species lets you.*

## Why this counts as an "invention"

Strictly, it doesn't. It's a reminder: the impressive-looking solution is the wrong default. Most of the plants that end up in the highland cabinet don't actually need the highland cabinet. The shelves document the ones that don't.
