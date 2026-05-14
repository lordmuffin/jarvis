#!/usr/bin/env bash
# print/build.sh — exports jarvis-onepager.pdf to repo root
# Usage: bash build.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT="$REPO_ROOT/jarvis-onepager.pdf"

# Require architecture.svg
SVG_FILE="$SCRIPT_DIR/architecture.svg"
if [ ! -f "$SVG_FILE" ]; then
  echo "ERROR: $SVG_FILE not found."
  echo "Run: cd jarvis-onepager && pnpm install && pnpm --filter web tsx ../scripts/export-svg.mjs"
  exit 1
fi

SVG_CONTENT=$(cat "$SVG_FILE")

# Build a temp HTML with SVG inlined
TMP_HTML=$(mktemp /tmp/jarvis-print-XXXXXX.html)
python3 - "$SCRIPT_DIR/index.html" "$SVG_CONTENT" "$TMP_HTML" << 'PYEOF'
import sys
src = open(sys.argv[1]).read()
svg = sys.argv[2]
out = src.replace('<!-- ARCH_SVG_PLACEHOLDER -->', svg)
open(sys.argv[3], 'w').write(out)
PYEOF

echo "Exporting PDF via Playwright headless Chrome..."

# Try Playwright's built-in PDF via Node
node - "$TMP_HTML" "$OUT" << 'JSEOF' 2>/dev/null || {
  echo "Node/Playwright not available; trying npx playwright..."
  npx --yes playwright@latest chromium pdf "file://$TMP_HTML" "$OUT"
}
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(`file://${process.argv[2]}`);
  await page.emulateMedia({ media: 'print' });
  await page.pdf({
    path: process.argv[3],
    format: 'Letter',
    printBackground: true,
    margin: { top: 0, bottom: 0, left: 0, right: 0 },
  });
  await browser.close();
})();
JSEOF

rm -f "$TMP_HTML"

if [ ! -f "$OUT" ]; then
  echo "BUILD FAILED: PDF not created. Install Playwright: pnpm add -D playwright && npx playwright install chromium"
  exit 1
fi

# Page-count check (requires pdfinfo from poppler-utils, optional)
if command -v pdfinfo &>/dev/null; then
  PAGES=$(pdfinfo "$OUT" | grep "^Pages:" | awk '{print $2}')
  if [ "$PAGES" != "1" ]; then
    echo "BUILD FAILED: PDF has $PAGES pages (expected 1). Adjust print.css to fit single page." >&2
    exit 1
  fi
  echo "PDF exported: $OUT (${PAGES} page)"
else
  echo "PDF exported: $OUT (install pdfinfo/poppler-utils to verify page count)"
fi
