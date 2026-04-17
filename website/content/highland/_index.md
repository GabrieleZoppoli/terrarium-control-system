---
title: "Highland Cloud Forest Terrarium"
description: "An open-source weather-mimicking terrarium simulating tepui climates for ~120 cloud forest species"
ogImage: "img/collection/dracula/dracula-pholeodytes.jpg"
---

<div class="highland-hero">
  <a class="highland-hero__interior" href="/collection/genera/dracula/" aria-label="Dracula pholeodytes inside the terrarium">
    <img src="/img/collection/dracula/dracula-pholeodytes.jpg" alt="Dracula pholeodytes pitcher orchid inside the highland terrarium" loading="eager" decoding="async">
    <figcaption><em>Dracula pholeodytes</em> · inside the cabinet</figcaption>
  </a>
  <a class="highland-hero__schematic" href="/highland/docs/architecture/" aria-label="Hardware architecture">
    <img src="/img/highland/build/schematic_panel-01.png" alt="Front-panel schematic of the Highland cabinet" loading="eager" decoding="async">
    <figcaption>Cabinet front panel · one of 10 schematics in the docs</figcaption>
  </a>
</div>

A 1.5 × 0.6 × 1.1 m insulated acrylic enclosure in Genoa, Italy, that simulates highland cloud forest weather using real-time Colombian meteorological data (time-shifted 15 hours). Marine refrigeration drives nighttime temperatures to ~13.5 °C in a room at 22 °C. About 120 species coexist under the same regime — *Heliamphora*, highland *Nepenthes*, *Dracula*, *Sophronitis*, New Guinea *Dendrobium*, *Utricularia* sect. *Orchidioides*, and more.

{{< highland-live >}}

<dl class="highland-stats" aria-label="Operating envelope">
  <div><dt>Temperature</dt><dd>13.5 – 24.3 °C</dd></div>
  <div><dt>Humidity</dt><dd>75 – 98 % RH</dd></div>
  <div><dt>VPD</dt><dd>0.03 – 0.64 kPa</dd></div>
  <div><dt>Logging</dt><dd>32 signals · 60 s</dd></div>
  <div><dt>Species hosted</dt><dd>≈ 120</dd></div>
  <div><dt>Operational</dt><dd>since 2023</dd></div>
</dl>

## Inside the cabinet

<figure class="moment">
  <a href="/highland/photos/"><img src="/img/highland/interior/interior_2023-06-24_20230624_122929.jpg" alt="Heliamphora pitchers under the grow lights, June 2023" loading="lazy"></a>
  <figcaption>June 2023 — thirteen months in. See the <a href="/highland/photos/">full timeline</a> for how it got here.</figcaption>
</figure>

## The residents

A small selection of the genera hosted in the cabinet. Each links to its page with provenance, sources, and full photo grid.

<ul class="highland-residents">
  <li><a href="/collection/genera/heliamphora/"><img src="/img/collection/heliamphora/heliamphora-macdonaldae.jpg" alt="Heliamphora macdonaldae" loading="lazy"><span><em>Heliamphora</em><small>tepui sun pitchers</small></span></a></li>
  <li><a href="/collection/genera/dracula/"><img src="/img/collection/dracula/dracula-pholeodytes.jpg" alt="Dracula pholeodytes" loading="lazy"><span><em>Dracula</em><small>Andean cloud-forest orchids</small></span></a></li>
  <li><a href="/collection/genera/nepenthes/"><img src="/img/collection/nepenthes/nepenthes-argentii.jpg" alt="Nepenthes argentii" loading="lazy"><span><em>Nepenthes</em><small>highland tropical pitchers</small></span></a></li>
  <li><a href="/collection/genera/sophronitis/"><img src="/img/collection/sophronitis/sophronitis-coccinea-4n.jpg" alt="Sophronitis coccinea 4N" loading="lazy"><span><em>Sophronitis</em><small>Brazilian rock-dwelling miniatures</small></span></a></li>
  <li><a href="/collection/genera/dendrobium/"><img src="/img/collection/dendrobium/dendrobium-cuthbertsonii-yellow.jpg" alt="Dendrobium cuthbertsonii" loading="lazy"><span><em>Dendrobium</em><small>New Guinea highland orchids</small></span></a></li>
  <li><a href="/collection/genera/other-orchids/"><img src="/img/collection/masdevallia/masdevallia-decumana.jpg" alt="Masdevallia decumana" loading="lazy"><span><em>Masdevallia</em><small>Andean miniatures</small></span></a></li>
</ul>

## Sections

- **[Photos →](photos/)** — Chronological interior timeline, eight shots from foil-lined build stage to mature ecosystem
- **[Documentation →](docs/)** — Architecture, PID controller, InfluxDB schema, Node-RED flows
- **[Dashboard →](dashboard/)** — Grafana snapshot panels (mobile + desktop) and current conditions
- **[Live UI →](live/)** — Near-live view of the Node-RED control panel, refreshed every 15 minutes
- **[Webcam](webcam/)** — Live view inside the terrarium *(coming soon)*

## The paper

A multi-paper publication is in progress targeting *HardwareX* (full system), *Carnivorous Plant Newsletter* (CP horticulture), *Orchids* (popular orchid piece), and a comprehensive synthesis. Drafts in [`paper/`](https://github.com/GabrieleZoppoli/terrarium-control-system/tree/main/paper) on the repo.

## Source code

All control flows, firmware, dashboards, and analysis scripts: [GitHub repo](https://github.com/GabrieleZoppoli/terrarium-control-system) — CERN-OHL-P-2.0 license.
