---
title: "Il terrario d'alta quota"
description: "Un terrario open-source che riproduce il clima dei tepui per circa 120 specie di foresta nebulosa"
ogImage: "img/collection/dracula/dracula-pholeodytes.jpg"
---

<div class="highland-hero">
  <a class="highland-hero__interior" href="/it/collection/genera/dracula/" aria-label="Dracula pholeodytes dentro al terrario">
    <img src="/img/collection/dracula/dracula-pholeodytes.jpg" alt="Dracula pholeodytes dentro al terrario" loading="eager" decoding="async">
    <figcaption><em>Dracula pholeodytes</em> · dentro al terrario</figcaption>
  </a>
  <a class="highland-hero__dashboard" href="/it/highland/dashboard/" aria-label="Dashboard Grafana live delle ultime 24 ore">
    <img src="https://rei1.tail7cc014.ts.net/highland/grafana-latest-hero.png" alt="Grafana live — temperatura, umidità, VPD, stato attuatori sulle ultime 24 ore" loading="eager" decoding="async">
    <figcaption>Grafana live · aggiornata ogni 15 min</figcaption>
  </a>
</div>

<nav class="highland-hero-links" aria-label="Costruzione, documentazione e sorgente">
  <a href="/it/highland/photos/">Cronologia della costruzione</a>
  <a href="/it/highland/docs/architecture/">Architettura e schemi</a>
  <a href="/it/highland/docs/flows/">Flussi Node-RED</a>
  <a href="https://github.com/GabrieleZoppoli/terrarium-control-system" rel="external">Sorgente e firmware</a>
</nav>

Una camera acrilica isolata da 1,5 × 0,6 × 1,1 m, qui a Genova, che riproduce il clima di una foresta nebulosa d'alta quota usando in tempo reale i dati meteo della Colombia (con uno scarto di 15 ore). Un compressore marino porta la temperatura notturna a circa 13,5 °C in una stanza a 22 °C. Circa 70 specie (≈85 esemplari contando le linee clonali) convivono sotto lo stesso regime — *Heliamphora*, *Nepenthes* d'alta quota, *Dracula*, *Sophronitis*, *Dendrobium* della Nuova Guinea, Pleurothallidinae miniatura, e altre ancora.

{{< highland-live >}}

<p class="highland-envelope">In funzione dal 2023 · 32 segnali registrati ogni 60 s · intervalli storici 13,5 – 24,3 °C e 75 – 98 % UR.</p>

## Dentro al terrario

<figure class="moment">
  <a href="/highland/photos/"><img src="/img/highland/interior/interior_2023-06-24_20230624_122929.jpg" alt="Heliamphora sotto le luci di crescita, giugno 2023" loading="lazy"></a>
  <figcaption>Giugno 2023 — tredici mesi dall'accensione. La <a href="/highland/photos/">timeline completa</a> racconta tutto il percorso.</figcaption>
</figure>

## Chi ci vive

Una piccola selezione dei generi ospitati nel terrario. Ogni tessera porta alla rispettiva pagina con provenienza, fornitori e galleria fotografica completa.

<ul class="highland-residents">
  <li><a href="/collection/genera/heliamphora/"><img src="/img/collection/heliamphora/heliamphora-macdonaldae.jpg" alt="Heliamphora macdonaldae" loading="lazy"><span><em>Heliamphora</em><small>pianta-brocca dei tepui</small></span></a></li>
  <li><a href="/collection/genera/dracula/"><img src="/img/collection/dracula/dracula-pholeodytes.jpg" alt="Dracula pholeodytes" loading="lazy"><span><em>Dracula</em><small>orchidee delle Ande</small></span></a></li>
  <li><a href="/collection/genera/nepenthes/"><img src="/img/collection/nepenthes/nepenthes-argentii.jpg" alt="Nepenthes argentii" loading="lazy"><span><em>Nepenthes</em><small>pianta-brocca tropicale d'alta quota</small></span></a></li>
  <li><a href="/collection/genera/sophronitis/"><img src="/img/collection/sophronitis/sophronitis-coccinea-4n.jpg" alt="Sophronitis coccinea 4N" loading="lazy"><span><em>Sophronitis</em><small>miniature rupicole del Brasile</small></span></a></li>
  <li><a href="/collection/genera/dendrobium/"><img src="/img/collection/dendrobium/dendrobium-cuthbertsonii-yellow.jpg" alt="Dendrobium cuthbertsonii" loading="lazy"><span><em>Dendrobium</em><small>orchidee d'altura della Nuova Guinea</small></span></a></li>
  <li><a href="/collection/genera/other-orchids/"><img src="/img/collection/masdevallia/masdevallia-decumana.jpg" alt="Masdevallia decumana" loading="lazy"><span><em>Masdevallia</em><small>miniature andine</small></span></a></li>
</ul>

## Sezioni

- **[Foto →](photos/)** — Timeline cronologica dell'interno, otto scatti dallo stadio di costruzione al terrario maturo
- **[Documentazione →](docs/)** — Architettura, controller PID, schema InfluxDB, flussi Node-RED *(in inglese)*
- **[Dashboard →](dashboard/)** — Pannelli Grafana (mobile + desktop) e condizioni correnti *(in inglese)*
- **[Interfaccia live →](live/)** — Vista ravvicinata del pannello di controllo Node-RED, aggiornato ogni 15 minuti *(in inglese)*
- **[Webcam](webcam/)** — Vista dal vivo dentro al terrario *(in arrivo)*

## Il paper

È in corso di preparazione una pubblicazione articolata su più riviste: *HardwareX* (il sistema completo), *Carnivorous Plant Newsletter* (la parte colturale sulle piante carnivore), *Orchids* (un pezzo divulgativo sulle orchidee) e una sintesi conclusiva. Le bozze sono in [`paper/`](https://github.com/GabrieleZoppoli/terrarium-control-system/tree/main/paper) sul repository.

## Codice sorgente

Tutti i flussi di controllo, il firmware, le dashboard e gli script di analisi: [repository GitHub](https://github.com/GabrieleZoppoli/terrarium-control-system) — licenza CERN-OHL-P-2.0.
