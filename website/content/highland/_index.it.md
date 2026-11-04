---
title: "Il terrario d'alta quota"
description: "Un terrario open-source che riproduce il clima dei tepui per circa 70 specie di foresta nebulosa"
ogImage: "img/collection/dracula/dracula-pholeodytes.jpg"
---

> **Più di 70 specie vivono all'interno.** [Vedi la griglia delle piante →](/areas/highland-terrarium/)

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

Un terrario acrilico isolato da 1,5 × 0,6 × 1,1 m, qui a Genova, che riproduce il clima di una foresta nebulosa d'alta quota dai dati meteo della Colombia in tempo reale, con uno scarto di 15 ore. Un compressore marino porta la temperatura notturna a circa 13,5 °C in una stanza a 22 °C. Circa 70 specie (≈85 esemplari contando le linee clonali) vivono sotto lo stesso regime: *Heliamphora*, *Nepenthes* d'alta quota, *Dracula*, *Sophronitis*, *Dendrobium* della Nuova Guinea, Pleurothallidinae miniatura e altre.

{{< highland-live >}}

<p class="highland-envelope">Terrario a compressore marino in funzione dal 2022 (predecessore con chiller dal 2016) · 32 segnali registrati ogni 60 s · intervalli storici 13,5 – 24,3 °C e 75 – 98 % UR.</p>

## Dentro al terrario

<figure class="moment">
  <a href="/highland/photos/"><img src="/img/highland/interior/interior_2023-06-24_20230624_122929.jpg" alt="Heliamphora sotto le luci di crescita, giugno 2023" loading="lazy"></a>
  <figcaption>Giugno 2023, tredici mesi dall'accensione. La <a href="/highland/photos/">cronologia completa</a> mostra la costruzione.</figcaption>
</figure>

## Chi ci vive

Sei dei generi ospitati nel terrario. Ogni tessera porta alla rispettiva pagina con provenienza, fornitori e foto.

<ul class="highland-residents">
  <li><a href="/collection/genera/heliamphora/"><img src="/img/collection/heliamphora/heliamphora-macdonaldae.jpg" alt="Heliamphora macdonaldae" loading="lazy"><span><em>Heliamphora</em><small>pianta-brocca dei tepui</small></span></a></li>
  <li><a href="/collection/genera/dracula/"><img src="/img/collection/dracula/dracula-pholeodytes.jpg" alt="Dracula pholeodytes" loading="lazy"><span><em>Dracula</em><small>orchidee delle Ande</small></span></a></li>
  <li><a href="/collection/genera/nepenthes/"><img src="/img/collection/nepenthes/nepenthes-argentii.jpg" alt="Nepenthes argentii" loading="lazy"><span><em>Nepenthes</em><small>pianta-brocca tropicale d'alta quota</small></span></a></li>
  <li><a href="/collection/genera/sophronitis/"><img src="/img/collection/sophronitis/sophronitis-coccinea-4n.jpg" alt="Sophronitis coccinea 4N" loading="lazy"><span><em>Sophronitis</em><small>miniature rupicole del Brasile</small></span></a></li>
  <li><a href="/collection/genera/dendrobium/"><img src="/img/collection/dendrobium/dendrobium-cuthbertsonii-yellow.jpg" alt="Dendrobium cuthbertsonii" loading="lazy"><span><em>Dendrobium</em><small>orchidee d'altura della Nuova Guinea</small></span></a></li>
  <li><a href="/collection/genera/other-orchids/"><img src="/img/collection/masdevallia/masdevallia-decumana.jpg" alt="Masdevallia decumana" loading="lazy"><span><em>Masdevallia</em><small>miniature andine</small></span></a></li>
</ul>

## Sezioni

- **[Foto →](photos/)**: cronologia dell'interno, dieci scatti dalla fase di costruzione a oggi
- **[Documentazione →](docs/)**: architettura, controllore PID, schema InfluxDB, flussi Node-RED
- **[Dashboard →](dashboard/)**: snapshot Grafana (mobile e desktop) e condizioni correnti
- **[Interfaccia live →](live/)**: il pannello di controllo Node-RED, aggiornato ogni 15 minuti
- **[Webcam](webcam/)**: vista dal vivo dentro al terrario *(in arrivo)*

## Il paper

Sono in preparazione articoli per *HardwareX* (il sistema completo), *Carnivorous Plant Newsletter* (la coltivazione delle carnivore) e *Orchids* (le orchidee), più una sintesi. Le bozze sono in [`paper/`](https://github.com/GabrieleZoppoli/terrarium-control-system/tree/main/paper) sul repository.

## Codice sorgente

Tutti i flussi di controllo, il firmware, le dashboard e gli script di analisi: [repository GitHub](https://github.com/GabrieleZoppoli/terrarium-control-system), licenza CERN-OHL-S v2.
