// Design tokens — single source for web (CSS vars + Tailwind) and HTML targets.
// Light values used for print; dark values are the web/slide default.

export const colorTokens = {
  light: {
    bg: '#FAFAFA',
    surface: '#FFFFFF',
    surface2: '#F4F4F5',
    fg: '#0A0A0A',
    fgMuted: '#52525B',
    fgSubtle: '#71717A',
    border: '#E4E4E7',
    borderStrong: '#D4D4D8',
    accent: '#2563EB',
    accentFg: '#FFFFFF',
    success: '#15803D',
    warn: '#A16207',
  },
  dark: {
    bg: '#0A0A0A',
    surface: '#111111',
    surface2: '#171717',
    fg: '#FAFAFA',
    fgMuted: '#A1A1AA',
    fgSubtle: '#71717A',
    border: '#27272A',
    borderStrong: '#3F3F46',
    accent: '#3B82F6',
    accentFg: '#FFFFFF',
    success: '#22C55E',
    warn: '#EAB308',
  },
} as const;

export const radius = { base: '6px', card: '12px' } as const;

export const spacing = [4, 8, 12, 16, 24, 32, 48, 64, 96] as const;

// Tailwind theme extension object (used in tailwind.config.ts)
export const tailwindThemeExtension = {
  colors: {
    bg: 'var(--bg)',
    surface: 'var(--surface)',
    'surface-2': 'var(--surface-2)',
    fg: 'var(--fg)',
    'fg-muted': 'var(--fg-muted)',
    'fg-subtle': 'var(--fg-subtle)',
    border: 'var(--border)',
    'border-strong': 'var(--border-strong)',
    accent: 'var(--accent)',
    'accent-fg': 'var(--accent-fg)',
    success: 'var(--success)',
    warn: 'var(--warn)',
  },
  borderRadius: {
    token: 'var(--radius)',
    card: 'var(--radius-card)',
  },
};
