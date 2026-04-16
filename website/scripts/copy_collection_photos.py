"""Copy watermarked collection photos into website/static/img/collection/.

Source tree: one folder per taxon under dendrogram/photos/, each containing
1.jpg, 2.jpg, ... (already watermarked, ~1600px long edge, q80).

Per website/HANDOFF.md:
  static/img/collection/{genus}/{species-slug}.jpg
  Slug: lowercase, spaces and × → `-`, strip apostrophes/accents.
  Multiple photos of same taxon → suffix `-2`, `-3`, …

We don't re-encode (keeps watermark + CC BY-SA EXIF intact).
"""
from __future__ import annotations

import re
import shutil
import sys
import unicodedata
from pathlib import Path

SRC = Path("/Users/gabrielezoppoli/Documents/documenti personali/botanica/dendrogram/photos")
DST = Path("/Users/gabrielezoppoli/Documents/documenti personali/my website/terrarium-paper/website/static/img/collection")

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
        for i, src in enumerate(photos, start=1):
            suffix = "" if i == 1 else f"-{i}"
            dst = out_dir / f"{taxon_slug}{suffix}.jpg"
            if dst.exists() and dst.stat().st_size == src.stat().st_size:
                continue
            shutil.copy2(src, dst)
            copied += 1
    print(f"copied {copied} files into {DST}")
    print(f"skipped {skipped_empty} empty folders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
