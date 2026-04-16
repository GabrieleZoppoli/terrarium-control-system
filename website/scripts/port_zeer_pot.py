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
    "https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400"
    "&family=Inter:wght@300;400;500;600;700"
    "&family=JetBrains+Mono:wght@400;500;600&display=swap"
)

ROOT_RE = re.compile(r":root\s*\{[^}]*\}", re.DOTALL)

# The original SVG pitchers are three naive J-curves that don't really read as
# Darlingtonia. Replace the whole <!-- Darlingtonia pitchers --> group with a
# recognizable silhouette: tubular body + inflated cobra hood + forked fishtail
# appendage + translucent areolae (light windows).
DARLINGTONIA_RE = re.compile(
    r"<!--\s*Darlingtonia pitchers\s*-->\s*<g[^>]*>.*?</g>",
    re.DOTALL,
)
DARLINGTONIA_SVG = """<!-- Darlingtonia pitchers (cobra-head silhouette) -->
        <g opacity="0.55">
          <!-- left pitcher, medium -->
          <g transform="translate(318,195)">
            <path d="M-2,0 C -5,-25 -4,-55 1,-80 C 4,-94 12,-100 18,-92"
                  fill="none" stroke="#7da050" stroke-width="5.2" stroke-linecap="round"/>
            <ellipse cx="22" cy="-91" rx="10" ry="6.5" fill="#7da050"/>
            <path d="M15,-94 Q22,-99 31,-92" fill="none" stroke="#5a7838" stroke-width="1" opacity="0.55"/>
            <circle cx="20" cy="-93" r="1.3" fill="#e4efba" opacity="0.85"/>
            <circle cx="25" cy="-90" r="1" fill="#e4efba" opacity="0.7"/>
            <path d="M18,-83 Q15,-77 13,-72 M23,-83 Q26,-77 28,-72"
                  fill="none" stroke="#a85a34" stroke-width="1.3" stroke-linecap="round"/>
          </g>
          <!-- center pitcher, tallest, with twist -->
          <g transform="translate(382,195)">
            <path d="M-2,0 C -6,-40 -2,-78 2,-104 C 5,-118 14,-124 21,-115"
                  fill="none" stroke="#7da050" stroke-width="5.5" stroke-linecap="round"/>
            <ellipse cx="25" cy="-114" rx="11" ry="7" fill="#7da050"/>
            <path d="M17,-117 Q25,-123 34,-115" fill="none" stroke="#5a7838" stroke-width="1" opacity="0.55"/>
            <circle cx="23" cy="-116" r="1.5" fill="#e4efba" opacity="0.9"/>
            <circle cx="28" cy="-112" r="1.1" fill="#e4efba" opacity="0.75"/>
            <path d="M20,-106 Q18,-99 15,-95 M26,-106 Q29,-99 32,-95"
                  fill="none" stroke="#a85a34" stroke-width="1.3" stroke-linecap="round"/>
          </g>
          <!-- right pitcher, short, facing right -->
          <g transform="translate(445,195)">
            <path d="M-2,0 C -5,-28 -3,-58 1,-80 C 4,-92 11,-96 17,-88"
                  fill="none" stroke="#7da050" stroke-width="5" stroke-linecap="round"/>
            <ellipse cx="21" cy="-87" rx="8.5" ry="6" fill="#7da050"/>
            <path d="M14,-90 Q21,-95 29,-88" fill="none" stroke="#5a7838" stroke-width="0.9" opacity="0.55"/>
            <circle cx="19" cy="-89" r="1.2" fill="#e4efba" opacity="0.85"/>
            <path d="M17,-80 Q15,-75 13,-71 M22,-80 Q24,-75 26,-71"
                  fill="none" stroke="#a85a34" stroke-width="1.2" stroke-linecap="round"/>
          </g>
        </g>"""


def main() -> int:
    if not SRC.is_file():
        print(f"source not found: {SRC}", file=sys.stderr)
        return 1
    html = SRC.read_text(encoding="utf-8")

    # 1. Swap the :root block
    new_html, n = ROOT_RE.subn(NEW_ROOT.strip(), html, count=1)
    if n != 1:
        print("warning: could not find a :root block to replace", file=sys.stderr)

    # 1b. Swap the simple J-curve pitchers for a recognizable Darlingtonia silhouette
    new_html, n_pitchers = DARLINGTONIA_RE.subn(DARLINGTONIA_SVG, new_html, count=1)
    if n_pitchers != 1:
        print("warning: Darlingtonia pitchers block not replaced", file=sys.stderr)

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
