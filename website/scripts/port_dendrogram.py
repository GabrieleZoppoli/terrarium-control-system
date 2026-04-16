"""Port `living_collection_dendrogram.html` into the site.

- Rewrites photo paths in the embedded `const data = {...}` JSON from
  `photos/{Genus species}/N.jpg` → `../img/collection/{genus-slug}/{taxon-slug}{-N?}.jpg`
  so photos resolve to the copies already copied by copy_collection_photos.py.
- Writes the rewritten HTML to `static/dendrogram/index.html`.
- Also exports the transformed tree to `static/data/dendrogram.json` for any
  future bespoke viewer.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

SRC = Path("/Users/gabrielezoppoli/Documents/documenti personali/botanica/dendrogram/living_collection_dendrogram.html")
WEB = Path("/Users/gabrielezoppoli/Documents/documenti personali/my website/terrarium-paper/website")
DST_HTML = WEB / "static/dendrogram/index.html"
DST_JSON = WEB / "static/data/dendrogram.json"

QUOTE_CHARS = "'\u2018\u2019\u201C\u201D\""


def slugify(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    stripped = stripped.replace("×", "x")
    for q in QUOTE_CHARS:
        stripped = stripped.replace(q, "")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", stripped).strip("-").lower()
    return slug


PHOTO_RE = re.compile(r"^photos/(?P<taxon>[^/]+)/(?P<n>\d+)\.(?:jpg|jpeg)$", re.IGNORECASE)


def rewrite_photo(p: str) -> str:
    m = PHOTO_RE.match(p)
    if not m:
        return p
    taxon = m.group("taxon")
    n = int(m.group("n"))
    genus = taxon.split()[0]
    genus_slug = slugify(genus)
    taxon_slug = slugify(taxon)
    suffix = "" if n == 1 else f"-{n}"
    # relative path: dendrogram HTML lives at /dendrogram/ so ../img/... resolves to /img/...
    return f"../img/collection/{genus_slug}/{taxon_slug}{suffix}.jpg"


def walk_rewrite(node: dict) -> None:
    photos = node.get("photos")
    if isinstance(photos, list):
        node["photos"] = [rewrite_photo(p) for p in photos]
    for child in node.get("children", []) or []:
        walk_rewrite(child)
    # Add a slug handy for external consumers
    if "children" not in node and "name" in node:
        pass  # leaf — let callers compute slug from context if they need it


def main() -> int:
    html = SRC.read_text(encoding="utf-8")
    m = re.search(r"const data = (\{.*?\});\s", html, re.DOTALL)
    if not m:
        m = re.search(r"const data = (\{.*\});", html)
    if not m:
        print("couldn't find `const data = ...` in source HTML", file=sys.stderr)
        return 1

    data = json.loads(m.group(1))
    walk_rewrite(data)
    new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    new_html = html[: m.start(1)] + new_json + html[m.end(1) :]

    DST_HTML.parent.mkdir(parents=True, exist_ok=True)
    DST_HTML.write_text(new_html, encoding="utf-8")
    DST_JSON.parent.mkdir(parents=True, exist_ok=True)
    DST_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    leaves = 0
    with_photos = 0

    def count(n: dict) -> None:
        nonlocal leaves, with_photos
        if "children" not in n:
            leaves += 1
            if n.get("photos"):
                with_photos += 1
        for c in n.get("children", []) or []:
            count(c)

    count(data)
    print(f"wrote {DST_HTML} ({len(new_html)/1024:.0f} KB)")
    print(f"wrote {DST_JSON} ({DST_JSON.stat().st_size/1024:.0f} KB)")
    print(f"{with_photos}/{leaves} leaves have photos — paths rewritten to ../img/collection/…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
