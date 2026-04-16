---
title: "Highland Cloud Forest Terrarium"
description: "An open-source weather-mimicking terrarium simulating tepui climates for ~120 cloud forest species"
---

A 1.5 × 0.6 × 1.1 m insulated acrylic enclosure in Genoa, Italy, that simulates highland cloud forest weather using real-time Colombian meteorological data (time-shifted 15 hours). Marine refrigeration drives nighttime temperatures to ~13.5 °C in a room at 22 °C. ~120 species coexist under the same regime — *Heliamphora*, highland *Nepenthes*, *Dracula*, *Sophronitis*, New Guinea *Dendrobium*, *Utricularia* sect. *Orchidioides*, and more.

## Sections

- **[Documentation](docs/)** — Architecture, PID controller, InfluxDB schema, Node-RED flows
- **[Dashboard](dashboard/)** — Live (snapshot) Grafana panels and current conditions
- **[Webcam](webcam/)** — Live view inside the terrarium *(coming soon)*
- **[Photos](photos/)** — Build photos and growth progression *(coming soon)*

## The paper

A multi-paper publication is in progress targeting *HardwareX* (full system), *Carnivorous Plant Newsletter* (CP horticulture), *Orchids* (popular orchid piece), and a comprehensive synthesis. Drafts in [`paper/`](https://github.com/GabrieleZoppoli/terrarium-control-system/tree/main/paper) on the repo.

## Source code

All control flows, firmware, dashboards, and analysis scripts: [GitHub repo](https://github.com/GabrieleZoppoli/terrarium-control-system) — CERN-OHL-P-2.0 license.
