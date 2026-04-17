---
title: "About the Project"
description: "Convergent cloud forest cultivation in a single terrarium"
showTableOfContents: true
---

## The Convergent Cloud Forest Concept

Cloud forests exist on tropical mountains worldwide, wherever persistent fog and cool temperatures create similar selective pressures. Despite being separated by thousands of kilometers and millions of years of independent evolution, these ecosystems have converged on remarkably similar strategies: compact rosette growth, trichome-covered leaves for fog interception, and shallow root systems adapted to waterlogged, nutrient-poor substrates.

This terrarium exploits that convergence. Species from Venezuelan tepuis (*Heliamphora*, *Stegolepis*), the Colombian Andes (*Dracula*, *Masdevallia*), the Brazilian *campos rupestres* (*Sophronitis*), and the highlands of Papua New Guinea (*Dendrobium* section *Oxyglossum*) coexist because they evolved under functionally identical climatic envelopes — despite having no shared evolutionary history.

## Why Colombian Weather?

The system uses real-time weather data from four Colombian highland cities (Chinchiná, Medellín, Bogotá, Sonsón) as environmental setpoints. These span 1,300–2,600 m elevation and collectively approximate the temperature and humidity range of a generic tropical highland cloud forest.

The weather data is time-shifted by 15 hours to align Colombian daytime (which corresponds to European nighttime) with the terrarium's photoperiod in Genova, Italy. The result: naturalistic day-night cycles with realistic diurnal temperature swings of 4–8 °C.

## The Terrarium

- **Dimensions:** 1.5 × 0.6 × 1.1 m (≈1,000 L)
- **Lighting:** 4 × ChilLED Logic Puck V3 (100 W each, 244 Samsung LM301B LEDs per puck)
- **Cooling:** Vitrifrigo ND50 marine compressor with a custom evaporator
- **Humidity:** MistKing diaphragm pump feeding 20 nozzle points under PID fan control
- **Control:** Raspberry Pi running Node-RED, InfluxDB, Grafana, and an Arduino coprocessor

Operational since 2023; multi-paper publication in progress ([GitHub](https://github.com/GabrieleZoppoli/terrarium-control-system)).

<!--
TO FILL IN when you're ready:

1. A 2–3 paragraph "why I built this" section: the originating frustration, the
   build timeline, what surprised you along the way, what you'd do differently.
   Probably slots right after "The Terrarium" section above.

2. A short author bio: name, affiliation (if any), how cloud-forest cultivation
   became a thing in your life, what drew you to highland carnivores specifically.
   Slots at the bottom of the page under an "## Author" heading.

Everything else on this page tracks published facts and auto-updates, so once
those two paragraphs are in, nothing else here needs maintenance.
-->
