---
title: "Il terrario d'alta quota"
description: "Un terrario open-source che riproduce il clima dei tepui per circa 120 specie di foresta nebulosa"
ogImage: "img/collection/dracula/dracula-pholeodytes.jpg"
---

<div class="highland-hero">
  <a class="highland-hero__interior" href="/collection/genera/dracula/" aria-label="Dracula pholeodytes dentro al terrario">
    <img src="/img/collection/dracula/dracula-pholeodytes.jpg" alt="Dracula pholeodytes dentro al terrario" loading="eager" decoding="async">
    <figcaption><em>Dracula pholeodytes</em> · dentro al terrario</figcaption>
  </a>
  <a class="highland-hero__schematic" href="/highland/docs/architecture/" aria-label="Architettura hardware">
    <img src="/img/highland/build/schematic_panel-01.png" alt="Schema del pannello frontale del terrario" loading="eager" decoding="async">
    <figcaption>Pannello frontale · uno dei 10 schemi nella documentazione</figcaption>
  </a>
</div>

Una camera acrilica isolata da 1,5 × 0,6 × 1,1 m, qui a Genova, che riproduce il clima di una foresta nebulosa d'alta quota usando in tempo reale i dati meteo della Colombia (sfasati di 15 ore). Un compressore marino porta la temperatura notturna a circa 13,5 °C in una stanza a 22 °C. Circa 120 specie convivono sotto lo stesso regime — *Heliamphora*, *Nepenthes* d'alta quota, *Dracula*, *Sophronitis*, *Dendrobium* della Nuova Guinea, *Utricularia* sect. *Orchidioides*, e altre ancora.

{{< highland-live >}}

<dl class="highland-stats" aria-label="Condizioni operative">
  <div><dt>Temperatura</dt><dd>13,5 – 24,3 °C</dd></div>
  <div><dt>Umidità</dt><dd>75 – 98 % UR</dd></div>
  <div><dt>VPD</dt><dd>0,03 – 0,64 kPa</dd></div>
  <div><dt>Log</dt><dd>32 segnali · ogni 60 s</dd></div>
  <div><dt>Specie ospitate</dt><dd>≈ 120</dd></div>
  <div><dt>In funzione</dt><dd>dal 2023</dd></div>
</dl>

## Sezioni

- **[Documentazione](docs/)** — Architettura, controller PID, schema InfluxDB, flussi Node-RED *(in inglese)*
- **[Dashboard](dashboard/)** — Snapshot dei pannelli Grafana e condizioni correnti *(in inglese)*
- **[Webcam](webcam/)** — Vista dal vivo dentro al terrario *(in arrivo)*
- **[Foto](photos/)** — Foto di costruzione e di crescita *(in arrivo)*

## Il paper

È in corso di preparazione una pubblicazione articolata su più riviste: *HardwareX* (il sistema completo), *Carnivorous Plant Newsletter* (la parte colturale sulle piante carnivore), *Orchids* (un pezzo divulgativo sulle orchidee) e una sintesi conclusiva. Le bozze sono in [`paper/`](https://github.com/GabrieleZoppoli/terrarium-control-system/tree/main/paper) sul repository.

## Codice sorgente

Tutti i flussi di controllo, il firmware, le dashboard e gli script di analisi: [repository GitHub](https://github.com/GabrieleZoppoli/terrarium-control-system) — licenza CERN-OHL-P-2.0.
