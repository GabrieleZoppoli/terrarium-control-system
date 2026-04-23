#!/usr/bin/env python3
"""Generate static/data/mosaic_pools.json for the homepage rotating mosaics.

Reads collection.csv (status=alive) and scans static/img/collection/<genus>/
for each plant's photo(s). Emits two pools:

  {
    "terrarium": [ { src, alt, taxon, href, provenance }, ... ],
    "balcony":   [ { src, alt, taxon, href, provenance }, ... ]
  }

Pool entries have the same shape as hugo.toml's featuredMosaic entries,
so the homepage rotation JS can drop any pool entry into any tile.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent
CSV_PATH = WEB / "static" / "data" / "collection.csv"
IMG_ROOT = WEB / "static" / "img" / "collection"
OUT_PATH = WEB / "static" / "data" / "mosaic_pools.json"

LOCATION_TO_POOL = {
    "highland": "terrarium",
    "outdoor":  "balcony",
}

PROVENANCE_BY_POOL = {
    "terrarium": "Highland cabinet",
    "balcony":   "Balcony · outdoor",
}

# Genera that have their own genus page on the site. Anything else routes
# to /collection/genera/ so we never emit a 404 link.
GENUS_PAGES = {
    "heliamphora", "nepenthes", "sarracenia", "dionaea", "dracula",
    "sophronitis", "dendrobium", "tillandsia", "cephalotus", "utricularia",
    "pinguicula",
}


def slug(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s.strip("-")


def find_photo(genus: str, taxon: str) -> str | None:
    """Find the first photo for a taxon in static/img/collection/<genus>/.

    Matches the taxon slug at the start of the filename, then falls back
    to any file beginning with the species slug. Skips responsive variants
    (-480.jpg, -960.jpg) since those are served via srcset alongside the
    1600w master.
    """
    genus_dir = IMG_ROOT / slug(genus)
    if not genus_dir.is_dir():
        return None
    taxon_slug = slug(taxon)
    # Strip genus prefix from the taxon slug — filenames inside a genus
    # folder typically start with the full taxon but sometimes drop the
    # genus prefix. Try both.
    candidates = [taxon_slug]
    genus_prefix = slug(genus) + "-"
    if taxon_slug.startswith(genus_prefix):
        candidates.append(taxon_slug[len(genus_prefix):])
    for cand in candidates:
        for p in sorted(genus_dir.glob("*.jpg")):
            if p.name.endswith(("-480.jpg", "-960.jpg")):
                continue
            stem = p.stem
            if stem == cand or stem.startswith(cand + "-"):
                return f"img/collection/{slug(genus)}/{p.name}"
    return None


def build_pools() -> dict:
    pools: dict[str, list] = {k: [] for k in LOCATION_TO_POOL.values()}
    seen: dict[str, set] = {k: set() for k in LOCATION_TO_POOL.values()}
    with CSV_PATH.open() as f:
        for row in csv.DictReader(f):
            if row.get("status") != "alive":
                continue
            pool_key = LOCATION_TO_POOL.get(row.get("location", ""))
            if not pool_key:
                continue
            taxon = row.get("taxon", "").strip()
            genus = row.get("genus", "").strip()
            if not taxon or not genus:
                continue
            # Dedupe at the taxon level — clonal lines pile up otherwise.
            if taxon in seen[pool_key]:
                continue
            src = find_photo(genus, taxon)
            if not src:
                continue
            genus_slug = slug(genus)
            href = (
                f"/collection/genera/{genus_slug}/"
                if genus_slug in GENUS_PAGES
                else "/collection/genera/"
            )
            pools[pool_key].append({
                "src":         src,
                "alt":         taxon,
                "taxon":       taxon,
                "href":        href,
                "provenance":  PROVENANCE_BY_POOL[pool_key],
            })
            seen[pool_key].add(taxon)
    return pools


def main() -> None:
    pools = build_pools()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(pools, ensure_ascii=False, indent=2) + "\n")
    for k, v in pools.items():
        print(f"{k:10s}: {len(v):3d} entries")
    print(f"wrote {OUT_PATH.relative_to(WEB)}")


if __name__ == "__main__":
    main()
