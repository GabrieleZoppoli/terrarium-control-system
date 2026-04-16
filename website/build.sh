#!/bin/bash
# Pre-build script: copies docs/ into website content with Hugo front matter
set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCS_SRC="$REPO_ROOT/docs"
DOCS_DST="$REPO_ROOT/website/content/highland/docs"

declare -A TITLES=(
  ["architecture.md"]="System Architecture"
  ["schema.md"]="InfluxDB Measurement Schema"
  ["pid-controller.md"]="PID Controller"
)

declare -A DESCS=(
  ["architecture.md"]="Hardware layers, communication protocols, and software stack"
  ["schema.md"]="All 32 measurements logged by the system"
  ["pid-controller.md"]="Gain-scheduled PID algorithm with three-regime fan control"
)

for f in architecture.md schema.md pid-controller.md; do
  slug="${f%.md}"
  mkdir -p "$DOCS_DST/$slug"
  {
    echo "---"
    echo "title: \"${TITLES[$f]}\""
    echo "description: \"${DESCS[$f]}\""
    echo "---"
    echo ""
    # Strip the first H1 line (Hugo uses front matter title)
    tail -n +2 "$DOCS_SRC/$f"
  } > "$DOCS_DST/$slug/index.md"
done

# Copy flows-README as a docs page
mkdir -p "$DOCS_DST/flows"
{
  echo "---"
  echo "title: \"Node-RED Flows Guide\""
  echo "description: \"Flow import guide and tab-by-tab description\""
  echo "---"
  echo ""
  tail -n +2 "$REPO_ROOT/nodered/flows-README.md"
} > "$DOCS_DST/flows/index.md"

echo "Docs synced to Hugo content."
