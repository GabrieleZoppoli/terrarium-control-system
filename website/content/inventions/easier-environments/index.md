---
title: "Fog Shelves"
description: "Glass shelves in the living room: ultrasonic misters on a Raspberry-Pi-driven hysteresis RH loop (~80 %), switched via Tapo P100 plugs, BME280 + SHT35 sensors"
---

Not every plant needs a 1.5 m climate-controlled cabinet. Several species in the collection live on a set of open glass shelves in the living room. Each shelf has an ultrasonic mister with a reservoir, plugged into a Tapo P100 smart plug; a second Raspberry Pi polls a Bosch BME280 and an SHT35 on the shelf and toggles the plug on a hysteresis loop around ~80 % RH. No chiller, no PID, no logging.

The room handles temperature passively (18–24 °C year-round, Genoese Mediterranean climate); ambient daylight plus a plain full-spectrum LED strip provides the photoperiod.

These are the plants that live happily in a Genoese living room once water vapour is added and temperature is left alone.

## What's on the shelves

The lineup changes. Plants that outgrow their spot or need cooler nights move into the highland cabinet; newcomers that do not need cloud-forest temperatures start here and stay if they do well.

| Shelf resident | Source | Why here and not in the cabinet |
|---|---|---|
| *Vanda coerulescens* | Celandroni Orchidee | Warm-intermediate vandaceous; tolerates room temperatures. |
| *Neostylis* Lou Sneary (*N. falcata* × *Rhynchostylis coelestis* var. *coerulea*) | Celandroni Orchidee | Hybrid inherits the warmer tolerance of *Rhynchostylis*. |
| *Darwinara* Charm 'Blue Moon' (*Neofinetia × Vanda × Rhynchostylis × Ascocentrum*) | Claessen Orchids & Plants | Blue-violet flowers; the blue pigmentation tracks with cooler *nights* specifically, which the mister-fog microclimate provides without actual chilling. |
| Mexican *Pinguicula* (*agnata*, *ehlersiae*, *esseriana*, *gypsicola* × *moctezumae*, *rotundiflora*, *rectifolia*, *Marciano*, *Apasionada*, *Red Starfish* etc.) | Un Angolo di Deserto · Giardino Carnivoro | Mexican pings want bright light + dry roots + high humidity during the rainy season; the fog gives them humidity without soaking. |
| *Cephalotus follicularis* + f. 'Hummer's Giant' | Giardino Carnivoro · David Maccioni | Hates the highland night minimum (13 °C) and the still air; prefers a drier, brighter, more ventilated spot. |
| *Phalaenopsis* species (*finleyi*, *lowii*, *gibbosa*, *wilsonii*, *parishii*) | Celandroni Orchidee | Warm-growing botanical *Phalaenopsis*, miniature in habit. Happier in intermediate conditions than in the cloud forest. |
| *Angraecum didieri* | Growlist | Madagascan miniature; intermediate-warm, intolerant of the highland night drop. |
| *Bulbophyllum makoyanum* | Gift | Southeast-Asian lowland to mid-elevation; the cabinet is too cool overnight for it. |

## The hardware

- **Ultrasonic mister**: generic 24 V piezoelectric disc with a refillable reservoir, switched by a Tapo P100 smart plug. Replace the disc every ~18 months; cartridges are cheap and the unit itself is cheaper.
- **Sensors**: a Bosch BME280 and an SHT35 side by side on the shelf. Two sensors because RH sensors drift, and a setpoint 10 % off is the difference between healthy plants and mould.
- **Controller**: a second Raspberry Pi (not the highland one) runs a small Python loop: it reads the two sensors, averages them, and toggles the Tapo plug via the PyP100 library to hold RH around 80 % with hysteresis. No InfluxDB, no dashboard, no Node-RED; a setpoint, a dead band and a log file.
- **Light**: a plain full-spectrum LED strip along the top of each shelf, on a wall socket with a dumb daily timer (no dawn ramps, no PID, no Node-RED).
- **Everything else**: room air, room temperature, windowsill light where applicable.

The whole setup costs a fraction of the highland cabinet, and most of the plants that would otherwise go into the cabinet do not need it. The shelves hold the ones that don't.
