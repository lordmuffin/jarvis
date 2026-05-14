#!/usr/bin/env node
// scripts/export-svg.mjs
// Regenerates print/architecture.svg from shared/architecture.tsx
// Run from jarvis-onepager/web/: pnpm tsx ../scripts/export-svg.mjs
// Or from jarvis-onepager/: node --import tsx/esm scripts/export-svg.mjs

import { writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = resolve(__dirname, '..');

// Use tsx to execute the TypeScript serializer
const svgLight = execSync(
  `npx tsx -e "
    const { serializeArchitectureSvg } = require('./shared/architecture.tsx');
    process.stdout.write(serializeArchitectureSvg('light'));
  "`,
  { cwd: rootDir, encoding: 'utf8' }
);

const outPath = resolve(rootDir, 'print/architecture.svg');
writeFileSync(outPath, svgLight, 'utf8');
console.log('Wrote', outPath);

const svgDark = execSync(
  `npx tsx -e "
    const { serializeArchitectureSvg } = require('./shared/architecture.tsx');
    process.stdout.write(serializeArchitectureSvg('dark'));
  "`,
  { cwd: rootDir, encoding: 'utf8' }
);

const darkPath = resolve(rootDir, 'print/architecture-dark.svg');
writeFileSync(darkPath, svgDark, 'utf8');
console.log('Wrote', darkPath);
