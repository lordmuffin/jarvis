# jarvis-onepager

Three output formats from one content source:
- `web/` — Next.js 15 static export (dark-default one-pager)
- `print/` — HTML + CSS → PDF (8.5×11, single page)
- `slide/` — HTML 1920×1080 slide (16:9, dark palette)

## ⚠️ Content rule

**Edit `shared/content.ts` only.** Never edit content strings inside `web/`, `print/`, or `slide/` directly.

## Quickstart

```bash
cd web
pnpm install
pnpm dev          # http://localhost:3000
```

## Build commands

| Format | Command | Output |
|--------|---------|--------|
| Web (dev) | `cd web && pnpm dev` | localhost:3000 |
| Web (static) | `cd web && pnpm build` | `web/out/` |
| Print PDF | `cd print && bash build.sh` | `../jarvis-onepager.pdf` |
| Slide (preview) | open `slide/index.html` in browser | — |
| Slide PDF | Chrome → Print → Save as PDF (no margins) | manual |

## Regenerate architecture SVG

After editing `shared/architecture.tsx`, regenerate the static SVG used by print and slide:

```bash
cd web
pnpm tsx ../scripts/export-svg.mjs
```

## Deploy (static host)

The `web/out/` directory after `pnpm build` is a self-contained static site.
Drop it on any static host (Cloudflare Pages, Netlify, GitHub Pages, nginx).

No `personal-website/` integration at this time — deploy `out/` independently.
