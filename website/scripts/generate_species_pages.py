#!/usr/bin/env python3
"""Generate per-species content stubs under content/collection/species/.

One folder per unique taxon (alive rows only); each carries photos,
provenance, acquisition data. If a hand-authored `body.md` sits next
to the auto-generated `index.md`, the layout appends its contents as
a rich deep-dive section. Users never edit `index.md` directly — rerun
this script to refresh it.

Reads:
  static/data/collection.csv        — inventory rows
  data/mosaic_provenance.yaml       — origin captions per taxon/genus
  data/photo_manifest.json          — primary + extra photos per taxon

Writes:
  content/collection/species/<slug>/index.md   — auto-generated per taxon
  data/species_index.yaml                      — slug → taxon lookup
                                                 (used by the homepage
                                                 hero + featured mechanic)
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent
CSV_PATH     = WEB / "static" / "data" / "collection.csv"
MANIFEST     = WEB / "data" / "photo_manifest.json"
PROVENANCE   = WEB / "data" / "mosaic_provenance.yaml"
SPECIES_ROOT = WEB / "content" / "collection" / "species"
INDEX_OUT    = WEB / "data" / "species_index.yaml"

LOCATION_LABEL = {
    "highland":   "Highland cabinet",
    "outdoor":    "Balcony · outdoor",
    "shelves":    "Fog shelves",
    "windowsill": "Windowsill",
    "seasonal":   "Seasonal",
}

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


def load_provenance() -> dict[str, str]:
    if not PROVENANCE.is_file():
        return {}
    out: dict[str, str] = {}
    for raw in PROVENANCE.read_text(encoding="utf-8").splitlines():
        m = re.match(r'^\s*"((?:[^"\\]|\\.)*)"\s*:\s*"((?:[^"\\]|\\.)*)"\s*$', raw)
        if m:
            out[m.group(1).replace('\\"', '"')] = m.group(2).replace('\\"', '"')
            continue
        m = re.match(r'^\s*([A-Za-z][\w\s\.\-×\']+?)\s*:\s*"((?:[^"\\]|\\.)*)"\s*$', raw)
        if m:
            out[m.group(1).strip()] = m.group(2).replace('\\"', '"')
    return out


def provenance_for(taxon: str, genus: str, lookup: dict[str, str]) -> str:
    if taxon in lookup:
        return lookup[taxon]
    parts = taxon.split(maxsplit=2)
    if len(parts) >= 2:
        gs = f"{parts[0]} {parts[1]}"
        if gs in lookup:
            return lookup[gs]
    return lookup.get(genus, "")


def y(text: str) -> str:
    """Render a string as a YAML-safe scalar — prefers bare when possible."""
    if not text:
        return '""'
    if re.search(r"[:#'\"\\{}\[\],&*?!|>%@`]|^\s|\s$|^-\s", text):
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return text


def write_index(slug_: str, entry: dict) -> None:
    folder = SPECIES_ROOT / slug_
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "index.md"
    # We always regenerate index.md from the data; the body.md (if any)
    # is appended by the template, not embedded here.
    lines = [
        "---",
        "# AUTO-GENERATED — do not edit by hand.",
        "# Rerun scripts/generate_species_pages.py after inventory changes.",
        "# For rich prose, drop a body.md in this folder; the template appends it.",
        f"title: {y(entry['taxon'])}",
        f"taxon: {y(entry['taxon'])}",
        f"genus: {y(entry['genus'])}",
        f"species: {y(entry['species'])}",
        f"provenance: {y(entry['provenance'])}",
        f"slug: {entry['slug']}",
        "sources:",
    ]
    for src in entry["sources"]:
        lines.append(f"  - id: {src['id']}")
        lines.append(f"    vendor: {y(src['vendor'])}")
        lines.append(f"    acquired: {y(src['acquired'])}")
        lines.append(f"    price_eur: {y(src['price_eur'])}")
        lines.append(f"    location: {y(src['location_label'])}")
        if src.get("notes"):
            lines.append(f"    notes: {y(src['notes'])}")
    lines.append("photos:")
    for p in entry["photos"]:
        lines.append(f"  - {y(p)}")
    if entry.get("primary_photo"):
        lines.append(f"primary_photo: {y(entry['primary_photo'])}")
    if entry.get("genus_page"):
        lines.append(f"genus_page: {entry['genus_page']}")
    lines.append("---")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.is_file() else {}
    # manifest structure: genus_slug → [ { taxon, slug, primary, additional[] } … ]
    # Flatten to taxon → { primary, extras, genus_slug }
    photos_by_taxon: dict[str, dict] = {}
    for genus_slug, entries in manifest.items():
        for e in entries:
            t = e.get("taxon")
            if not t:
                continue
            primary = f"img/collection/{genus_slug}/{e['primary']}" if e.get("primary") else ""
            extras = [f"img/collection/{genus_slug}/{x}" for x in e.get("additional", [])]
            photos_by_taxon[t] = {
                "primary": primary,
                "extras": extras,
                "genus_slug": genus_slug,
            }

    provenance_lookup = load_provenance()

    # Group CSV rows by taxon (alive only)
    by_taxon: dict[str, dict] = {}
    with CSV_PATH.open() as f:
        for row in csv.DictReader(f):
            if row.get("status") != "alive":
                continue
            taxon = (row.get("taxon") or "").strip()
            if not taxon:
                continue
            genus = (row.get("genus") or "").strip()
            species = (row.get("species") or "").strip()
            entry = by_taxon.setdefault(taxon, {
                "taxon":   taxon,
                "genus":   genus,
                "species": species,
                "slug":    slug(taxon),
                "sources": [],
            })
            entry["sources"].append({
                "id":             row.get("id", ""),
                "vendor":         (row.get("source") or "").strip(),
                "acquired":       (row.get("acquired_date") or "").strip(),
                "price_eur":      (row.get("price_eur") or "").strip(),
                "location_label": LOCATION_LABEL.get(row.get("location", ""), row.get("location", "")),
                "notes":          (row.get("notes") or "").strip(),
            })

    SPECIES_ROOT.mkdir(parents=True, exist_ok=True)

    index_rows: list[tuple[str, str, str, str, str]] = []  # (slug, taxon, genus, primary_photo, provenance)
    missing_photos: list[str] = []

    for taxon, entry in sorted(by_taxon.items()):
        photos_info = photos_by_taxon.get(taxon)
        if not photos_info or not photos_info["primary"]:
            missing_photos.append(taxon)
            continue  # skip taxa without any photo — nothing to show

        entry["photos"] = [photos_info["primary"], *photos_info["extras"]]
        entry["primary_photo"] = photos_info["primary"]
        entry["provenance"] = provenance_for(taxon, entry["genus"], provenance_lookup)

        genus_slug = slug(entry["genus"])
        entry["genus_page"] = (
            f"/collection/genera/{genus_slug}/"
            if genus_slug in GENUS_PAGES
            else ""
        )

        write_index(entry["slug"], entry)
        index_rows.append((entry["slug"], taxon, entry["genus"], entry["primary_photo"], entry["provenance"]))

    # Write species_index.yaml — used by the homepage hero/featured mechanism.
    lines = ["# Auto-generated by scripts/generate_species_pages.py.",
             "# Flat index: slug → taxon / genus / primary_photo.",
             ""]
    for s, t, g, p, prov in sorted(index_rows, key=lambda r: r[1].lower()):
        lines.append(f'"{s}":')
        lines.append(f'  taxon: {y(t)}')
        lines.append(f'  genus: {y(g)}')
        lines.append(f'  primary_photo: {y(p)}')
        if prov:
            lines.append(f'  provenance: {y(prov)}')
    INDEX_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {len(index_rows)} species pages → content/collection/species/")
    print(f"wrote index → data/species_index.yaml")
    if missing_photos:
        print(f"[note] {len(missing_photos)} alive taxa skipped (no photo yet):")
        for t in missing_photos[:15]:
            print(f"       - {t}")
        if len(missing_photos) > 15:
            print(f"       … and {len(missing_photos) - 15} more")


if __name__ == "__main__":
    main()
