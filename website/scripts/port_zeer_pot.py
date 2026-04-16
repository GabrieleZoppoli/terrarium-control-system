"""Port `darlingtonia-zeer-pot.html` into the site with the dendrogram palette.

- Copies the self-contained HTML to `static/zeer-pot/index.html`.
- Swaps the CSS custom-property block at the top so colors track the dendrogram
  (near-black + violet accent) rather than the original olive/plant palette.
- Switches typefaces to Inter / Crimson Pro / JetBrains Mono so it typographically
  matches the rest of the site.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SRC = Path("/Users/gabrielezoppoli/Documents/documenti personali/botanica/darlingtonia-zeer-pot/darlingtonia-zeer-pot.html")
WEB = Path("/Users/gabrielezoppoli/Documents/documenti personali/my website/terrarium-paper/website")
DST = WEB / "static/zeer-pot/index.html"

# Replace the :root { … } block near the top of the stylesheet with palette tokens
# aligned to the site. Structural tokens (spacing, radii) stay inherited from
# whatever the original sets; we only reset colors and typography sources.
NEW_ROOT = """  :root {
    --bg: #0a0b0e;
    --bg-card: rgba(14, 16, 20, 0.72);
    --bg-card-alt: rgba(20, 22, 28, 0.55);
    --accent: #b06dd1;
    --accent-dim: #8e4bb3;
    --accent-glow: rgba(176, 109, 209, 0.45);
    --water: #6fa7c4;
    --water-dim: #3d6f8a;
    --warm: #cf9a68;
    --warm-dim: #8a6540;
    --text: #e0e0e0;
    --text-dim: #8a8a8a;
    --text-bright: #ededed;
    --border: rgba(255, 255, 255, 0.12);
    --sand: #c4a86a;
  }"""

# Font-family replacements — map the zeer pot's choices onto the site's family.
FONT_REPLACEMENTS = [
    ("'Source Sans 3'", "'Inter'"),
    ('"Source Sans 3"', '"Inter"'),
    ("'DM Serif Display'", "'Crimson Pro'"),
    ('"DM Serif Display"', '"Crimson Pro"'),
    ("'IBM Plex Mono'", "'JetBrains Mono'"),
    ('"IBM Plex Mono"', '"JetBrains Mono"'),
]

# The original pulls from Google Fonts — re-point to the site's families in one sweep.
GOOGLE_FONTS_HREF = (
    "https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,500;1,300;1,400"
    "&family=Inter:wght@300;400;500;600"
    "&family=JetBrains+Mono:wght@400;500&display=swap"
)

ROOT_RE = re.compile(r":root\s*\{[^}]*\}", re.DOTALL)


def main() -> int:
    if not SRC.is_file():
        print(f"source not found: {SRC}", file=sys.stderr)
        return 1
    html = SRC.read_text(encoding="utf-8")

    # 1. Swap the :root block
    new_html, n = ROOT_RE.subn(NEW_ROOT.strip(), html, count=1)
    if n != 1:
        print("warning: could not find a :root block to replace", file=sys.stderr)

    # 2. Replace font family tokens everywhere (CSS and anywhere else)
    for old, new in FONT_REPLACEMENTS:
        new_html = new_html.replace(old, new)

    # 3. Rewrite the Google Fonts <link href=…>. The original preconnects to
    #    fonts.googleapis.com/fonts.gstatic.com once and then has one or more
    #    <link rel="stylesheet" href="…fonts.googleapis.com/css2?…"> — the css2
    #    request is the one to retarget.
    new_html = re.sub(
        r'href="https://fonts\.googleapis\.com/css2\?[^"]+"',
        f'href="{GOOGLE_FONTS_HREF}"',
        new_html,
    )

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(new_html, encoding="utf-8")
    print(f"wrote {DST} ({len(new_html)/1024:.0f} KB)  — :root replaced: {n}× | fonts retargeted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
