---
title: "Collection Dendrogram"
description: "Phylogenetic tree of all 356 plants with photos at each tip"
---

A phylogenetic dendrogram of the entire collection, with a representative photo at each tip. Built by an offline tool (run on the Mac side) that consumes the species list and per-species photos.

## How to view

The interactive dendrogram is embedded below. Hover (or tap) a tip to see the species name, source, status, and a larger photo.

<!-- DENDROGRAM_EMBED_HERE -->

*Embed not yet present. See [HANDOFF.md](https://github.com/GabrieleZoppoli/terrarium-control-system/blob/main/website/HANDOFF.md) for the asset placement convention.*

## Underlying data

- Species list: `data/collection.csv` (one row per acquisition: taxon, genus, source, price, status, date)
- Photos: `static/img/collection/{genus}/{species-slug}.jpg`
- Tree topology: `static/data/dendrogram.json` (Newick or D3-hierarchy JSON)
