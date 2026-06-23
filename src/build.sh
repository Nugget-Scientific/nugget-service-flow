#!/usr/bin/env bash
#
# Rebuild the diagram assets from source.
#
#   1. Render the mermaid flowchart to a crisp vector SVG (used by the site)
#      and a 3x-scale PNG (the title-less base for the composited download).
#   2. Paint the branded header (title + logo) onto the PNG via compose.py.
#
# Requires: npx (Node) for mermaid-cli, and Python with Pillow for the compose.
# Run from anywhere: `bash src/build.sh`.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/src"
ASSETS="$ROOT/assets"

echo "==> Rendering SVG (vector, for the web viewer)"
npx -y @mermaid-js/mermaid-cli@latest \
  -i "$SRC/service_lifecycle.mmd" -o "$ASSETS/diagram.svg" \
  -C "$SRC/style.css" -b white

echo "==> Rendering PNG base (3x scale, title-less)"
npx -y @mermaid-js/mermaid-cli@latest \
  -i "$SRC/service_lifecycle.mmd" -o "$SRC/diagram_only.png" \
  -C "$SRC/style.css" -b white -s 3

echo "==> Composing branded header -> assets/diagram.png"
python3 "$SRC/compose.py"

echo "==> Done."
