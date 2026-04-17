"""Write website/data/stats.json from live source data.

Called at the end of every /add-plant sync (and any manual run of
``copy_collection_photos.py``). Reads:

- ``static/data/collection.csv``  -> accessions, alive, genera, alive_genera
- ``data/photo_manifest.json``    -> species_photographed, genera_photographed
- ``static/dendrogram/index.html`` -> dendrogram_accessions / _genera
  (the "N accessions · M genera · K families" subtitle line)

Writes ``data/stats.json``. Hugo templates read it via ``site.Data.stats``.
Idempotent; rerun any time.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1]
CSV_PATH = WEB / "static/data/collection.csv"
MANIFEST = WEB / "data/photo_manifest.json"
DENDRO_HTML = WEB / "static/dendrogram/index.html"
OUT = WEB / "data/stats.json"


def compute() -> dict:
    rows = list(csv.DictReader(CSV_PATH.open()))
    alive = [r for r in rows if (r.get("status") or "").strip() == "alive"]
    genera = {r["genus"] for r in rows if r.get("genus")}
    alive_genera = {r["genus"] for r in alive if r.get("genus")}

    pm = json.loads(MANIFEST.read_text())
    species_photographed = sum(len(v) for v in pm.values())
    genera_photographed = len(pm)

    dendro_accessions = len(rows)
    dendro_genera = len(genera)
    dendro_families = 0
    if DENDRO_HTML.exists():
        m = re.search(r"(\d+)\s*accessions\s*·\s*(\d+)\s*genera\s*·\s*(\d+)\s*families",
                      DENDRO_HTML.read_text())
        if m:
            dendro_accessions = int(m.group(1))
            dendro_genera = int(m.group(2))
            dendro_families = int(m.group(3))

    return {
        "accessions": len(rows),
        "alive": len(alive),
        "genera": len(genera),
        "alive_genera": len(alive_genera),
        "species_photographed": species_photographed,
        "genera_photographed": genera_photographed,
        "dendrogram_accessions": dendro_accessions,
        "dendrogram_genera": dendro_genera,
        "dendrogram_families": dendro_families,
    }


def main() -> int:
    stats = compute()
    OUT.write_text(json.dumps(stats, indent=2) + "\n")
    for k, v in stats.items():
        print(f"  {k:>24}: {v}")
    print(f"wrote -> {OUT.relative_to(WEB.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
