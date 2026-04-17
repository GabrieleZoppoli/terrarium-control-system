"""Copy watermarked collection photos into website/static/img/collection/.

Source tree: one folder per taxon under dendrogram/photos/, each containing
1.jpg, 2.jpg, ... (already watermarked, ~1600px long edge, q80).

Per website/HANDOFF.md:
  static/img/collection/{genus}/{species-slug}.jpg
  Slug: lowercase, spaces and × → `-`, strip apostrophes/accents.
  Multiple photos of same taxon → suffix `-2`, `-3`, …

We don't re-encode (keeps watermark + CC BY-SA EXIF intact).

Also emits website/data/photo_manifest.json for Hugo to pick up as
site.Data.photo_manifest — used by the collection-photos shortcode to render
per-genus galleries without scanning the filesystem at template time.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

SRC = Path("/Users/gabrielezoppoli/Documents/documenti personali/botanica/dendrogram/photos")
WEB = Path("/Users/gabrielezoppoli/Documents/documenti personali/my website/terrarium-paper/website")
DST = WEB / "static/img/collection"
MANIFEST = WEB / "data/photo_manifest.json"

QUOTE_CHARS = "'\u2018\u2019\u201C\u201D\""


def slugify(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    stripped = stripped.replace("×", "x")
    for q in QUOTE_CHARS:
        stripped = stripped.replace(q, "")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", stripped).strip("-").lower()
    return slug


def main() -> int:
    if not SRC.is_dir():
        print(f"source not found: {SRC}", file=sys.stderr)
        return 1
    DST.mkdir(parents=True, exist_ok=True)
    taxa = [p for p in sorted(SRC.iterdir()) if p.is_dir() and not p.name.startswith("_")]
    copied = 0
    skipped_empty = 0
    manifest: dict[str, list[dict]] = {}

    for folder in taxa:
        taxon = folder.name
        genus = taxon.split()[0]
        genus_slug = slugify(genus)
        taxon_slug = slugify(taxon)
        out_dir = DST / genus_slug
        photos = sorted(list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")),
                        key=lambda p: (len(p.stem), p.stem))
        if not photos:
            skipped_empty += 1
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        entry_files: list[str] = []
        for i, src in enumerate(photos, start=1):
            suffix = "" if i == 1 else f"-{i}"
            name = f"{taxon_slug}{suffix}.jpg"
            dst = out_dir / name
            entry_files.append(name)
            if dst.exists() and dst.stat().st_size == src.stat().st_size:
                continue
            shutil.copy2(src, dst)
            copied += 1
        manifest.setdefault(genus_slug, []).append({
            "taxon": taxon,
            "slug": taxon_slug,
            "primary": entry_files[0],
            "extras": entry_files[1:],
        })

    # Stable order within each genus: alphabetical by taxon
    for entries in manifest.values():
        entries.sort(key=lambda e: e["taxon"].lower())

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    genera_with_photos = len(manifest)
    taxa_with_photos = sum(len(v) for v in manifest.values())
    print(f"copied {copied} files into {DST}")
    print(f"skipped {skipped_empty} empty folders")
    print(f"manifest: {taxa_with_photos} taxa across {genera_with_photos} genera → {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
