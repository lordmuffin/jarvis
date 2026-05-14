// React SVG component + serialize helper for the Jarvis architecture diagram.
// viewBox: 0 0 880 520 — scales to all three targets.

import React from 'react';

export type DiagramMode = 'light' | 'dark';

const COLORS = {
  dark: {
    surface: '#111111',
    border: '#3F3F46',
    fg: '#FAFAFA',
    fgMuted: '#A1A1AA',
    fgSubtle: '#71717A',
    accent: '#3B82F6',
    containerBg: '#0A0A0A',
  },
  light: {
    surface: '#FFFFFF',
    border: '#D4D4D8',
    fg: '#0A0A0A',
    fgMuted: '#52525B',
    fgSubtle: '#71717A',
    accent: '#2563EB',
    containerBg: '#FAFAFA',
  },
};

type NodeDef = {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  label: string;
  sublabel?: string;
};

// Coordinates designed for 880×520 viewBox
// Layout: Pixel entry (top-left) → Tailscale → homelab container (center) → Pixel toast (bottom-left)
const NODES: NodeDef[] = [
  { id: 'pixel-entry',  x: 40,  y: 28,  w: 160, h: 44, label: 'Pixel 9',       sublabel: 'entry surface' },
  { id: 'tailscale',    x: 40,  y: 112, w: 160, h: 44, label: 'Tailscale tailnet' },
  { id: 'goose',        x: 200, y: 216, w: 160, h: 56, label: 'Goose runtime',  sublabel: 'lxc' },
  { id: 'ollama',       x: 424, y: 192, w: 160, h: 44, label: 'Ollama',         sublabel: 'local LLM' },
  { id: 'vault-mcp',   x: 424, y: 256, w: 160, h: 44, label: 'Vault MCP' },
  { id: 'embeddings',  x: 424, y: 320, w: 160, h: 44, label: 'Embeddings index' },
  { id: 'ntfy',         x: 200, y: 316, w: 160, h: 44, label: 'ntfy push' },
  { id: 'audit-log',   x: 200, y: 416, w: 160, h: 56, label: 'Audit log',       sublabel: '→ vault' },
  { id: 'approve-mcp', x: 424, y: 416, w: 160, h: 56, label: 'Approve fires',   sublabel: 'MCP send' },
  { id: 'pixel-toast', x: 40,  y: 416, w: 136, h: 56, label: 'Pixel 9',         sublabel: 'Approve / Edit / Dismiss' },
];

// Homelab dashed container encloses goose, ollama, vault-mcp, embeddings, ntfy, audit-log, approve-mcp
const HOMELAB = { x: 178, y: 182, w: 428, h: 318 };

// Arrow paths — orthogonal routing, 90° bends only
// Each path is a minimal SVG d-string
const ARROWS = [
  // Pixel entry → Tailscale (straight down)
  { id: 'pixel-to-ts',    d: 'M 120 72 L 120 112' },
  // Tailscale → Goose (down then right into homelab)
  { id: 'ts-to-goose',    d: 'M 120 156 L 120 244 L 200 244' },
  // Goose → Ollama
  { id: 'goose-to-ollama', d: 'M 360 236 L 392 236 L 392 214 L 424 214' },
  // Goose → Vault MCP
  { id: 'goose-to-vault',  d: 'M 360 244 L 424 278' },
  // Goose → Embeddings
  { id: 'goose-to-emb',    d: 'M 360 252 L 392 252 L 392 342 L 424 342' },
  // Goose → ntfy (straight down)
  { id: 'goose-to-ntfy',   d: 'M 280 272 L 280 316' },
  // ntfy → Pixel toast (left out of homelab, then down)
  { id: 'ntfy-to-toast',   d: 'M 200 338 L 156 338 L 156 444 L 176 444' },
  // Pixel toast → Approve MCP (right across)
  { id: 'toast-to-approve', d: 'M 176 444 L 424 444' },
  // Approve MCP → Audit log (left)
  { id: 'approve-to-audit', d: 'M 424 444 L 360 444' },
];

// Junction dot where goose output fans: approximate center of fanout
const JUNCTION = { x: 360, y: 244 };

function ArchDiagram({ mode = 'dark' }: { mode?: DiagramMode }) {
  const c = COLORS[mode];
  const markerId = `arrowhead-${mode}`;

  return (
    <svg
      viewBox="0 0 880 520"
      role="img"
      aria-labelledby="archTitle archDesc"
      style={{ width: '100%', height: 'auto', display: 'block' }}
      xmlns="http://www.w3.org/2000/svg"
    >
      <title id="archTitle">Jarvis architecture: phone proposes, homelab composes, phone approves.</title>
      <desc id="archDesc">
        Pixel 9 connects via Tailscale tailnet to the homelab LXC. Goose runtime consults
        Ollama local LLM, Vault MCP, and Embeddings index to compose a response, then pushes
        via ntfy back through Tailscale to the Pixel 9 toast notification. Tapping Approve
        fires the MCP send tool and writes an audit log entry to the vault.
      </desc>

      <defs>
        <marker
          id={markerId}
          markerWidth="6"
          markerHeight="6"
          refX="5"
          refY="3"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <path d="M0,0.5 L0,5.5 L5.5,3 Z" fill={c.accent} />
        </marker>
      </defs>

      {/* Homelab dashed container */}
      <rect
        x={HOMELAB.x} y={HOMELAB.y}
        width={HOMELAB.w} height={HOMELAB.h}
        rx="12" ry="12"
        fill="none"
        stroke={c.border}
        strokeWidth="1"
        strokeDasharray="6 4"
      />
      {/* Label tab — covers the dashed border */}
      <rect
        x={HOMELAB.x + 10} y={HOMELAB.y - 10}
        width={76} height={20}
        rx="4"
        fill={c.containerBg}
      />
      <text
        x={HOMELAB.x + 14} y={HOMELAB.y + 5}
        fontFamily="'Geist Mono', 'JetBrains Mono', ui-monospace, monospace"
        fontSize="11"
        fill={c.fgSubtle}
        letterSpacing="0.05em"
      >
        HOMELAB
      </text>

      {/* Arrows */}
      {ARROWS.map((a) => (
        <path
          key={a.id}
          d={a.d}
          stroke={c.accent}
          strokeWidth="1"
          fill="none"
          markerEnd={`url(#${markerId})`}
        />
      ))}

      {/* Junction dot at Goose fanout */}
      <circle cx={JUNCTION.x} cy={JUNCTION.y} r="3" fill={c.accent} />

      {/* Nodes */}
      {NODES.map((n) => {
        const hasSub = Boolean(n.sublabel);
        const labelY = hasSub ? n.y + n.h / 2 - 7 : n.y + n.h / 2 + 5;
        const subY = n.y + n.h / 2 + 11;
        return (
          <g key={n.id} role="img" aria-label={n.sublabel ? `${n.label} — ${n.sublabel}` : n.label}>
            <title>{n.sublabel ? `${n.label} (${n.sublabel})` : n.label}</title>
            <rect
              x={n.x} y={n.y}
              width={n.w} height={n.h}
              rx="6" ry="6"
              fill={c.surface}
              stroke={c.border}
              strokeWidth="1"
            />
            <text
              x={n.x + n.w / 2}
              y={labelY}
              textAnchor="middle"
              fontFamily="'Geist Mono', 'JetBrains Mono', ui-monospace, monospace"
              fontSize="13"
              fontWeight="500"
              fill={c.fg}
            >
              {n.label}
            </text>
            {hasSub && (
              <text
                x={n.x + n.w / 2}
                y={subY}
                textAnchor="middle"
                fontFamily="'Geist Mono', 'JetBrains Mono', ui-monospace, monospace"
                fontSize="11"
                fill={c.fgMuted}
              >
                {n.sublabel}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

export default ArchDiagram;

// Serialize to SVG string for print/slide inlining.
// Only called at build time via scripts/export-svg.mjs
export function serializeArchitectureSvg(mode: DiagramMode = 'dark'): string {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { renderToStaticMarkup } = require('react-dom/server');
  return '<?xml version="1.0" encoding="UTF-8"?>\n' + renderToStaticMarkup(<ArchDiagram mode={mode} />);
}
