"""Copy watermarked area photos into website/static/img/areas/.

Source tree: one folder per area under dendrogram/photos/_areas/, each containing
1.jpg, 2.jpg, ... (already watermarked).

Emits website/data/areas_manifest.json for Hugo:

{
  "balcony":            ["1.jpg", "2.jpg", "3.jpg"],
  "windowsill":         [],
  "fog-shelves":        [],
  "highland-terrarium": ["1.jpg"],
  "mini-ponds":         []
}

Always emits ALL 5 canonical slugs, even if empty — so Hugo templates can
iterate a known set.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

SRC = Path("/Users/gabrielezoppoli/Documents/documenti personali/botanica/dendrogram/photos/_areas")
WEB = Path("/Users/gabrielezoppoli/Documents/documenti personali/my website/terrarium-paper/website")
DST = WEB / "static/img/areas"
MANIFEST = WEB / "data/areas_manifest.json"

CANONICAL_SLUGS = (
    "balcony", "windowsill", "fog-shelves", "highland-terrarium", "mini-ponds",
)


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, list[str]] = {slug: [] for slug in CANONICAL_SLUGS}
    copied = 0

    if SRC.is_dir():
        for slug in CANONICAL_SLUGS:
            src_dir = SRC / slug
            if not src_dir.is_dir():
                continue
            photos = sorted(
                list(src_dir.glob("*.jpg")) + list(src_dir.glob("*.jpeg")),
                key=lambda p: (len(p.stem), p.stem),
            )
            if not photos:
                continue
            out_dir = DST / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            for src in photos:
                dst = out_dir / src.name
                if dst.exists() and dst.stat().st_size == src.stat().st_size:
                    pass  # skip copy, still list it in manifest
                else:
                    shutil.copy2(src, dst)
                    copied += 1
                manifest[slug].append(src.name)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    total = sum(len(v) for v in manifest.values())
    populated = sum(1 for v in manifest.values() if v)
    print(f"copied {copied} files into {DST}")
    print(f"areas manifest: {total} photos across {populated}/5 populated areas → {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
