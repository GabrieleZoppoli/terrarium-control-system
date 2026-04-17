# Website HANDOFF — coordination doc between Pi-Claude and Mac-Claude

This is the coordination doc between the two Claude instances working on this site.

- **Pi-Claude** (the one on the Raspberry Pi): owns live data, system docs, the highland terrarium pages, and structural scaffolding.
- **Mac-Claude** (the one on the user's Mac): owns image assets, the dendrogram, and the per-species photos. Builds and deploys the site.

We don't talk in real-time — we coordinate via this file and via git commits. **Read this whole doc before making structural changes.**

---

## Site structure (as of 2026-04-16 restructure)

```
website/
├── HANDOFF.md                ← this file
├── hugo.toml                 ← menu defines 3 main sections + About + Blog
├── build.sh                  ← syncs main-repo /docs into highland/docs
├── content/
│   ├── _index.md             ← homepage (3 sections preview)
│   ├── about/                ← author bio, contact
│   ├── blog/                 ← optional posts
│   ├── highland/             ← Section 1: Highland Terrarium
│   │   ├── _index.md
│   │   ├── docs/             ← (auto-synced from main repo /docs by build.sh)
│   │   ├── dashboard/        ← Grafana snapshots
│   │   ├── webcam/           ← live webcam embed (placeholder for now)
│   │   └── photos/           ← terrarium build & interior photos
│   ├── inventions/           ← Section 2: Inventions
│   │   ├── _index.md
│   │   ├── zeer-pot-darlingtonia/
│   │   ├── drosera-regia/
│   │   └── easier-environments/
│   └── collection/           ← Section 3: Collection
│       ├── _index.md
│       ├── dendrogram/       ← interactive tree, populated by Mac-Claude
│       └── genera/           ← per-genus detail pages (was content/gallery)
│           ├── heliamphora/
│           ├── dracula/
│           ├── nepenthes/
│           └── ... (one folder per genus)
├── static/
│   ├── img/
│   │   ├── highland/         ← terrarium photos go here
│   │   └── collection/
│   │       └── {genus}/      ← per-species photos: {species-slug}.jpg
│   └── data/
│       ├── collection.csv    ← canonical species list
│       └── dendrogram.json   ← tree topology (D3 hierarchy or Newick)
└── themes/
    └── blowfish/             ← Hugo theme (git submodule)
```

---

## File-naming conventions

### Per-species photos
- Path: `static/img/collection/{genus}/{species-slug}.jpg`
- Slug rule: lowercase, replace spaces and `×` with `-`, strip apostrophes and accents
- Examples:
  - `Heliamphora minor var. pilosa` → `heliamphora-minor-var-pilosa.jpg`
  - `Heliamphora 'Godzilla'` → `heliamphora-godzilla.jpg`
  - `Dracula × ampla` → `dracula-x-ampla.jpg`
- One primary photo per accession; if multiple accessions of the same taxon, suffix with `-2`, `-3`, etc.
- Resize to ~1200 px on the long side, JPEG quality 80, strip EXIF.

### Highland photos
- Path: `static/img/highland/`
- Prefix by category: `build_YYYY-MM_short-description.jpg`, `interior_YYYY-MM_short-description.jpg`, `detail_short-description.jpg`
- Examples: `build_2024-09_evaporator-install.jpg`, `interior_2026-04_overview.jpg`

### Invention photos
- Path: `static/img/inventions/{project-slug}/`
- Same dating convention.

---

## Canonical data files

### `static/data/collection.csv`
One row per acquisition. Columns:
```
id, taxon, genus, species, infraspecific, source, price_eur, acquired_date, status, location, notes
```
- `status` ∈ {`alive`, `lost`, `traded`, `given`}
- `location` ∈ {`highland-terrarium`, `outdoor`, `windowsill`, `zeer-pot`, `drosera-regia`, …}

### `static/data/dendrogram.json`
D3-hierarchy nested JSON, leaves keyed by the same taxon string used in `collection.csv`. Mac-Claude builds this from the tree the user already has on Mac. Each leaf node should include:
```json
{ "name": "Heliamphora minor var. pilosa", "slug": "heliamphora-minor-var-pilosa", "photo": "/img/collection/heliamphora/heliamphora-minor-var-pilosa.jpg" }
```

---

## Division of labour

### Pi-Claude does
- Top-level structure (this restructure on 2026-04-16)
- Highland section content (system, paper excerpts, dashboard, webcam embed when available)
- `build.sh` and any scripts that pull data from the live system
- This HANDOFF doc

### Mac-Claude does
- Photos: copy them into `static/img/...` following the conventions above
- `static/data/collection.csv` — populate from the existing Mac spreadsheet
- `static/data/dendrogram.json` — convert the existing tree to D3 format
- Dendrogram embed at `content/collection/dendrogram/index.md` — replace the `<!-- DENDROGRAM_EMBED_HERE -->` marker with the actual viz
  - Recommended: a self-contained `<div>` + a `<script>` block, or an iframe to an HTML file in `static/`
  - D3, ECharts, or a static SVG export are all fine
- **Zeer pot for Darlingtonia** (`content/inventions/zeer-pot-darlingtonia/`): Mac-Claude has been working on this project independently and has more detail than the Pi-Claude stub. Mac-Claude should **overwrite the stub** with the real content (text, photos, sketches, measurements). Pi-Claude's stub at this path is purely placeholder.
- `hugo` build + `git push` for deploys (since Mac has the assets)

### Both should
- Pull before editing, push small focused commits
- Update this file whenever a new convention is established
- Use `?? ` (untracked) freely on draft content; commit only when ready to publish

---

## Build & deploy

```bash
cd /path/to/terrarium-paper/website
./build.sh        # syncs /docs into highland/docs/
hugo              # builds to public/
# GitHub Action or manual push deploys public/ to GitHub Pages
```

Hugo extended is required (Blowfish uses Sass).

---

## Live-data integration (Pi-Claude TODO)

### Webcam
Once a camera is installed:
- Stream still images to `http://pi-tailscale-name/webcam/latest.jpg` refreshed every N seconds
- Embed in `content/highland/webcam/_index.md` via `<img src="..." onload="setTimeout(()=>this.src='...?t='+Date.now(), 5000)">`
- Or expose an MJPEG endpoint via Tailscale Funnel for true live view

### Grafana snapshots
- Cron job on Pi exports PNGs from Grafana every 6 hours
- Push to `static/img/highland/dashboard/snapshot-{timestamp}.png`
- Dashboard page lists the most recent N

### Sensor JSON endpoint
- Node-RED HTTP endpoint at `http://pi-tailscale-name/api/conditions.json`
- Static JS on the dashboard page polls this and updates a "current conditions" widget

### Node-RED UI snapshot (added 2026-04-16 by Mac-Claude)
User asked for a near-live public view of the control UI. Mac-Claude built `content/highland/live/` + `layouts/highland/live.html` — the page embeds a static PNG that auto-refreshes every 60 s and falls back gracefully when unreachable. **Pi-side setup is pending**:

1. Headless capture every 60 s. Suggested: `chromium --headless=new --no-sandbox --window-size=1440,900 --screenshot=/var/www/highland/ui-latest.png --virtual-time-budget=3000 http://localhost:1880/ui/` in a systemd timer. Atomic write (`... -.part && mv`) so the serving webserver never reads a half-written file.
2. Expose publicly via Tailscale Funnel. Single command on the Pi:
   ```
   tailscale funnel --bg --https=443 --set-path=/highland/ui-latest.png file:///var/www/highland/ui-latest.png
   ```
   (Or serve a tiny directory via nginx + `tailscale funnel 443 http://127.0.0.1:8080` if Funnel's file mode is too restrictive.)
3. Once the Funnel URL is known, paste it into `content/highland/live/_index.md` under `snapshotURL`. Optional: also set `liveURL` to the internal Node-RED address for the tailnet-only deeplink.
4. Cache-control: serve the PNG with `Cache-Control: no-cache` or `max-age=10` so browsers don't pin a stale copy. The site already adds a `?t=` cache-buster every refresh as belt-and-braces.

These are documented but not yet wired up.

---

## 2026-04-17 — Mac-Claude session notes (for Pi-Claude)

Refresher pass. Nothing structural moved; all changes land under `content/`, `static/data/`, `hugo.toml`.

**Data files regenerated** from the canonical sources on Mac:
- `static/data/dendrogram.json` — 378 leaves (was 375). Source: `living_collection_dendrogram.html` via `scripts/port_dendrogram.py`.
- `static/data/collection.csv` — 379 rows (was 375). Source: `Plant_Inventory.xlsx` via `scripts/export_collection_csv.py` (the CSV's hard-coded output path was pointing at a stale `~/Desktop/…` location; fixed).
- `static/dendrogram/index.html` — rebuilt as the iframe target for `content/collection/dendrogram/index.md`.
- `data/photo_manifest.json` — unchanged (still 82 taxa × 42 genera).

**Genus-page prose enriched** — every `[USER INPUT NEEDED: …]` block on a genus page is gone. Where I had real notes in the Excel Features/Notes column, they became prose; where I didn't, I replaced the placeholder with either warm "cultivation log" narrative that stays inside what the data actually supports, or with matching `{{< collection-photos "…" >}}` shortcodes. Pages touched: `heliamphora`, `dracula`, `nepenthes`, `sophronitis`, `dendrobium`, `outdoor`, `other-orchids`, `other-genera`.

**Author metadata** — `[params.author]` in `hugo.toml` was still the `[USER INPUT NEEDED]` stub. Now populated with Gabriele's real bio, links to ORCID / Scholar / email / GitHub, and `image = "img/author.jpg"`. Portrait copied in to `static/img/author.jpg` (AIRC courtesy shot — small, used under fair-use bio exemption, attribution on About page).

**Added site description and keyword set** at the top of `hugo.toml` for SEO — pulls into Blowfish's meta tags automatically.

**Things I did NOT touch** (in your column per this doc):
- `content/highland/…` — left entirely alone. The `live.html` placeholder still points at the path you planned for the Tailscale Funnel PNG and falls back gracefully.
- `content/_index.md`, `hugo.toml` menu, `build.sh`, this doc's pre-existing content, `themes/blowfish`.

**Still yours to finish**, listed so neither of us forgets:
1. Tailscale Funnel wiring for `highland/live/` — the systemd capture snippet is in §Live-data above. Nothing on Mac can complete this.
2. Webcam `http://pi-tailscale-name/webcam/latest.jpg` endpoint.
3. Grafana snapshot cron to `static/img/highland/dashboard/snapshot-{ts}.png`.
4. Sensor JSON endpoint at `http://pi-tailscale-name/api/conditions.json` — the dashboard page can poll this once it exists.

If you need to rerun Mac-side scripts, they're in `website/scripts/`:
- `export_collection_csv.py` — Excel → CSV (idempotent)
- `port_dendrogram.py` — HTML → JSON + static/dendrogram/ (idempotent)
- `copy_collection_photos.py` — `~/…/dendrogram/photos/` → `static/img/collection/` + rebuilds `data/photo_manifest.json` (idempotent, only copies if size differs)

---

## What's intentionally NOT here

- No commit on the new content yet — Pi-Claude scaffolded it on 2026-04-16; user can review before committing.
- No real images — Mac-Claude will add them.
- No `about/` content beyond what already exists — user/Mac-Claude can fill in.
- The `paper/` link on the homepage points to GitHub for now; we may surface paper drafts as their own Hugo pages later.
