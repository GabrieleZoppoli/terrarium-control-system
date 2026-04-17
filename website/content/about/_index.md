---
title: "About"
description: "Gabriele Zoppoli — oncologist by day, highland-plant obsessive for all the hours the rest of life will spare"
showTableOfContents: true
---

I'm **Gabriele Zoppoli** — a clinician-scientist in oncology and hematology at the University of Genoa, and, for as many hours as the rest of life will spare, a keeper of highland carnivorous plants, miniature orchids, and grey *Tillandsia*. The collection documented on this site has grown one accession at a time out of the quiet thrill of watching species that should be impossible to keep alive, still be alive the next morning.

The systematic side of all of this — the spreadsheet, the phylogenetic ordering, the open-source control loop, the fact that the collection is indexed not alphabetically but by evolutionary divergence — is almost certainly a habit from the lab. You put the variables under control, you log everything, you publish the whole stack so other people can reproduce or argue with it. Applied to a living organism that is stubbornly *not* an experiment, the same reflex becomes something gentler: attention, patience, and a commitment to not losing what you've been lucky enough to receive.

## The convergent cloud forest concept

Cloud forests exist on tropical mountains the world over, wherever persistent fog and cool temperatures create similar selective pressures. Despite being separated by thousands of kilometers and by many millions of years of independent evolution, these ecosystems have converged on the same strategies: compact rosette growth, trichome-covered leaves for fog interception, and shallow root systems adapted to waterlogged, nutrient-poor substrates.

This terrarium exploits that convergence. Species from Venezuelan tepuis (*Heliamphora*, *Stegolepis*), the Colombian Andes (*Dracula*, *Masdevallia*), the Brazilian *campos rupestres* (*Sophronitis*), and the highlands of Papua New Guinea (*Dendrobium* section *Oxyglossum*) coexist inside a single 1,000-liter cabinet because they evolved under functionally identical climatic envelopes — never mind that they have no shared evolutionary history.

## Why Colombian weather?

The control system uses real-time weather data from four Colombian highland cities (Chinchiná, Medellín, Bogotá, Sonsón) as environmental setpoints. These span 1,300–2,600 m of elevation and together approximate the temperature and humidity range of a generic tropical highland cloud forest.

Colombian daytime aligns with European nighttime, so the incoming data is time-shifted by 15 hours to match the terrarium's photoperiod in Genova. The result is naturalistic day-night cycles with realistic diurnal swings of 4–8 °C — and, incidentally, the aesthetic of watching a little slice of the Andes inhale and exhale on a clock that is almost, but not quite, the one outside the window.

## The terrarium

- **Dimensions:** 1.5 × 0.6 × 1.1 m (≈1,000 L)
- **Lighting:** 4 × ChilLED Logic Puck V3 (100 W each, 244 Samsung LM301B LEDs per puck)
- **Cooling:** a Vitrifrigo ND50 marine compressor with a custom evaporator — the sort of part normally installed under a yacht bench
- **Humidity:** MistKing diaphragm pump feeding 20 nozzle points under PID fan control
- **Control:** Raspberry Pi running Node-RED, InfluxDB, Grafana, and an Arduino coprocessor for the latency-sensitive loops

Operational since 2023. The firmware, flows, and hardware schematics are all on [GitHub](https://github.com/GabrieleZoppoli/terrarium-control-system); the papers in progress are in the `paper/` folder of that repository.

## How it started

It began, as these things always begin, with a single *Dionaea muscipula* on a windowsill. Then *Nepenthes* — plants that spent the first year convinced they would die, before deciding not to. Then *Heliamphora*, *Dracula*, miniature *Dendrobium*: species I'd only ever seen in books, sent by small growers across Europe who still pack their plants by hand.

A few years in, it was clear that the ad-hoc windowsill-plus-shelf arrangement was the bottleneck, not the plants themselves. Genova is warm and humid by Italian standards but nothing like a Venezuelan tepui at 2,500 m. The terrarium came out of that mismatch: an insulated cabinet in which the climate could be genuinely chosen rather than tolerated, and in which species from five continents could coexist under one regime. Three years later the census is 375 acquisitions across 86 genera, about 270 of them still alive, and the learning curve has started to flatten in the way it only does when you have killed enough plants to tell the difference between a bad week and a bad decision.

## The hands behind the glass

The collection is mine on paper but two-handed in practice. My partner, **Khadija Mohamud**, covers mist cycles and hand-watering when I'm at the hospital, lends her name to orders from vendors who only ship to one country, and is responsible for roughly half of the plants that are still alive three years in. The terrarium lives in our apartment in Via San Fruttuoso in Genova; the outdoor beds of *Sarracenia* and *Dionaea* sit on the same balcony, a few meters away, soaking up the Mediterranean sun.

None of this would be sustainable — or as joyful — without the European carnivorous-plant and orchid community: Andreas Wistuba (Mudau) for *Nepenthes* and *Heliamphora* with real provenance; Vincenzo Castellaneta at Un Angolo di Deserto for *Pinguicula*; Giulio Celandroni in Pisa for orchids; Lieselotte Hromadnik in Kritzendorf, who still mails *Tillandsia* typed up on paper; the folks at Ecuagenera Europe, Großräschener Orchideen, Diflora, Heldros, Claessen, and many other small growers whose names fill the acquisition records. When any of these people retire, a lineage of hand-propagated clones risks retiring with them — which is as much a reason to keep growing, and to document the growing, as any private satisfaction.

## Contact

If something on the site is wrong, or if you have a plant question, or if you want to propose a trade, you can reach me at [gabriele.zoppoli@unige.it](mailto:gabriele.zoppoli@unige.it). The source code for everything here — the terrarium control system, the dendrogram, the site itself — is on [GitHub](https://github.com/GabrieleZoppoli/terrarium-control-system), and pull requests are welcome.
