// Single source of truth for all content strings.
// Web, print, and slide import from here — never duplicate content in target files.

export const meta = {
  name: 'jarvis',
  buildRef: 'a3f7c2e',
  buildDate: '2026-05-13',
  buildTime: '11:42 PT',
  buildDiff: '+12 −3',
  statusPill: 'phase 0 · queued',
  currentPhase: 'phase 0',
  date: '2026-05-13',
} as const;

export const thesis = {
  eyebrow: '// the thesis',
  oneLiner:
    'A Markdown-native, sovereign knowledge layer that proposes actions on the homelab and waits for approval.',
  sentences: [
    'Jarvis exists because the durable moat against well-funded autonomous-execution agents is open knowledge infrastructure that closed AI vendors structurally cannot replicate.',
    'The bet is that a Markdown-native, vendor-neutral knowledge surface — built by an engineer who can deploy, version, and operate plain-text infrastructure — becomes the layer those agents query rather than rebuild.',
    'The window is now because the autonomous-agent market is racing to ship execution UX while leaving the knowledge substrate unclaimed.',
  ],
} as const;

export type Principle = {
  id: string;
  icon: string;
  name: string;
  gloss: string;
  rulesOut: string;
};

export const principles: Principle[] = [
  {
    id: 'mobile-first',
    icon: 'Smartphone',
    name: 'Mobile-First',
    gloss:
      'The phone is the body — the Pixel is the primary surface and toast notifications are the primary interaction.',
    rulesOut:
      'Laptop-tethered workflows, "mobile companion" framings where the phone is a thin viewer.',
  },
  {
    id: 'sovereign',
    icon: 'Lock',
    name: 'Sovereign',
    gloss:
      'Default local inference on the homelab, burst over Tailscale, no commercial cloud in v1.',
    rulesOut:
      'API-keyed dependencies, hosted vector DBs, anything that breaks the Phase 5 airplane-mode test.',
  },
  {
    id: 'router',
    icon: 'Network',
    name: 'Router',
    gloss:
      'Jarvis proposes, Andrew approves — Approve / Edit / Dismiss is the v1 UX everywhere.',
    rulesOut:
      'Autonomous send/post/commit, fire-and-forget agents, any action that executes without a human confirmation step.',
  },
  {
    id: 'knowledge-layer',
    icon: 'BookOpen',
    name: 'Knowledge Layer',
    gloss:
      'The Obsidian-compatible Markdown vault in EPARAX topology is the substrate; the soul lives as plain text.',
    rulesOut:
      "Proprietary databases, binary persona stores, anything that can't be grep-ed, diffed, or committed to git.",
  },
  {
    id: 'with-a-soul',
    icon: 'Heart',
    name: 'With a Soul',
    gloss:
      'Identity is irreducible — CLAUDE.md + soul.md + user.md plus the decision history — and survives hardware death via the Phase 5 Soul Parity Suite restore test.',
    rulesOut:
      'Vibes-as-soul, undocumented persona drift, "the model just knows me" hand-waving.',
  },
];

export type Phase = {
  id: string;
  label: string;
  goal: string;
  state: 'queued' | 'active' | 'shipped';
  effort: string;
  active: boolean;
};

export const phases: Phase[] = [
  {
    id: 'phase-0',
    label: 'phase 0',
    goal: 'Decision lockdown + dev env (Goose + Ollama + emulator)',
    state: 'queued',
    effort: '1–2 wks · 6–12h',
    active: true,
  },
  {
    id: 'phase-1',
    label: 'phase 1',
    goal: 'Mobile router skeleton — first Gmail draft round-trip on Pixel',
    state: 'queued',
    effort: '4–6 wks · 24–40h',
    active: false,
  },
  {
    id: 'phase-2',
    label: 'phase 2',
    goal: 'Knowledge layer integration — vault MCP + embeddings + Syncthing',
    state: 'queued',
    effort: '4–6 wks · 30–48h',
    active: false,
  },
  {
    id: 'phase-3',
    label: 'phase 3',
    goal: 'Persona library + daily-driver MVP (5:30 AM digest to phone)',
    state: 'queued',
    effort: '4–6 wks · 24–40h',
    active: false,
  },
  {
    id: 'phase-4',
    label: 'phase 4',
    goal: 'Telegram hybrid — TTS playback + interactive triage',
    state: 'queued',
    effort: '3–4 wks · 18–28h',
    active: false,
  },
  {
    id: 'phase-5',
    label: 'phase 5+',
    goal: 'On-device 3B model, Soul Parity Suite, skill scale-out, gated OSS release',
    state: 'queued',
    effort: '70+ h',
    active: false,
  },
];

export const shipsNext = {
  heading: 'Ships next',
  phase: 'Phase 0',
  body:
    'Goose running locally against Ollama, one vault skill (tlddr or inbox-triage) ported as an MCP server with a working end-to-end round-trip, and a Pixel 9 emulator joined to the homelab tailnet. Validation: goose run "summarize the last 5 daily notes" returns a vault-grounded answer in ≤ 15 s with zero egress beyond Tailscale.',
  killCriterion:
    'Kill criterion: if Goose cannot reliably load a local-model provider after 8 hours of effort, pivot the substrate to OpenCode (sst) before Phase 1 ships.',
} as const;

export const whatThisIsNot: string[] = [
  'Not an autonomous agent — Jarvis proposes, Andrew approves; the Router model is the product, not a temporary UX.',
  'Not a competitor to apex.host — Jarvis is the complement layer those execution agents query.',
  'Not a chat UX — the C-Suite Personas are queryable structured advisor data, not a competing conversation surface.',
  'Not cloud-required — no commercial-cloud dependency in v1; the Phase 5 airplane-mode test is the named falsifier.',
  'Not a five-front commitment — Beyond DevOps and Healing Organics are cut for this cycle.',
];

export const northStar = {
  eyebrow: '// north star',
  pills: [
    { label: 'Compounding Infrastructure', variant: 'primary' as const },
    { label: 'Long-form Shipped', variant: 'secondary' as const },
    { label: 'Authority Reps', variant: 'secondary' as const },
  ],
  body:
    'Jarvis directly moves the Compounding Infrastructure input — Jarvis Knowledge API v0.1 + 50 graduated atomic notes by 2027-05-09. It secondarily moves Long-form Shipped (build-in-public artifacts from runbooks and design docs) and Authority Reps (the decision history wired into vault MCP is queryable proof of Chair-scope choices).',
} as const;

export type Decision = {
  id: string;
  name: string;
  resolve: string;
  rationale: string;
  tbd?: boolean;
};

export const openDecisions: Decision[] = [
  {
    id: 'goose-vs-opencode',
    name: 'Goose vs OpenCode (sst) as the substrate',
    resolve: 'End of Phase 0',
    rationale:
      'Locks the agent-runtime path for every subsequent phase. Goose is upstream Block/LF; OpenCode is the fallback if local-model provider loading is unreliable.',
  },
  {
    id: 'pixel-9-hardware',
    name: 'Pixel 9 hardware procurement',
    resolve: 'By Phase 1 week 4',
    rationale:
      'Emulator-only Phase 1 is acceptable for 4 weeks max before cellular/Tailscale validation cannot be done.',
  },
  {
    id: 'spreadsheet-output',
    name: 'Spreadsheet output for the Daily Driver',
    resolve: 'Phase 3',
    rationale:
      'Keep the Markdown digest, build a real spreadsheet, or drop it entirely. Low stakes; defer.',
  },
  {
    id: 'telegram-bot-account',
    name: 'Telegram bot account — separate or personal',
    resolve: 'Before Phase 4 week 1',
    rationale: 'Determines ops cleanliness for the hybrid surface.',
  },
  {
    id: 'restic-endpoint',
    name: 'Restic offsite endpoint',
    resolve: 'Before Phase 5',
    rationale:
      'Backblaze B2 vs friend NAS vs other; determines cost, bandwidth, trust model.',
  },
  {
    id: 'execution-partner',
    name: '10/80/10 execution partner — Cat Louis confirmed or alternative',
    resolve: 'End of Phase 0',
    rationale:
      'Without external execution capacity the plan stretches to 12–18 months.',
    tbd: true,
  },
  {
    id: 'apex-conversation',
    name: 'When the apex.host conversation starts',
    resolve: 'Phase 2 exit gate, or sooner if warm intro materializes',
    rationale:
      'Now with a vision deck, or after the working demo? Depends on relationship temperature.',
  },
];

export type GlossaryEntry = { term: string; definition: string };

export const glossary: GlossaryEntry[] = [
  {
    term: 'MCP',
    definition:
      'Model Context Protocol — the open spec for letting agents call tools/servers; the wire format every Jarvis capability is exposed over.',
  },
  {
    term: 'Goose',
    definition:
      "Block's open-source agent runtime, now under the Linux Foundation's Agentic AI Foundation; used as upstream substrate, extended via skills + MCP servers, never forked.",
  },
  {
    term: 'EPARAX',
    definition:
      "Andrew's vault topology — 00 Inbox / 10 Projects / 20 Areas / 30 Resources / 40 Archives / 50 Galaxy — the queryable knowledge schema.",
  },
  {
    term: 'Router model',
    definition:
      'The propose-not-execute UX pattern — Jarvis surfaces a proposed action as a toast; Andrew taps Approve / Edit / Dismiss.',
  },
  {
    term: '10/80/10',
    definition:
      "Andrew's management model for Jarvis: 10% architecture (Andrew), 80% execution (external talent, Cat Louis lead candidate), 10% review/integration (Andrew).",
  },
];

export const archCaption =
  'gmail → goose → ollama + vault → ntfy → approve → send → audit log';
