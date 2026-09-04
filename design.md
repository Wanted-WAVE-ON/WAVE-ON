# Design — SilentOrchestra 2.0

A locked design system for this app. Every page redesign reads this file before emitting code. Amend this file when the system needs to grow; do not invent per-page themes.

## Genre

Atmospheric, with a technical Workbench voice. The canvas is dark, but function—not ambience—carries the page.

## Macrostructure family

- App pages: **Workbench**. Primary task rail first; context and learned evidence sit beside it on desktop and follow it on mobile.
- Marketing pages: not currently present.
- Content pages: not currently present.

Workbench variation knobs: `primary=agent-flow`, `context=left-rail`, `evidence=right-rail`, `mobile=center-first`, `containment=single-layer`.

## Theme — Night Signal

- `--color-paper` oklch(13% 0.018 255)
- `--color-paper-2` oklch(17% 0.022 255)
- `--color-paper-3` oklch(21% 0.025 255)
- `--color-ink` oklch(95% 0.012 235)
- `--color-ink-2` oklch(78% 0.018 235)
- `--color-rule` oklch(34% 0.026 255)
- `--color-accent` oklch(80% 0.15 210)
- `--color-accent-ink` oklch(16% 0.03 255)
- `--color-focus` oklch(80% 0.18 205)
- `--color-learning` oklch(72% 0.12 292), reserved for suggestion/learning semantics only

Accent footprint stays below 5% of a viewport. Violet is not decoration; it only identifies a learning state.

## Typography

- Display: IBM Plex Sans KR, weight 700, roman
- Body: Pretendard Variable, weight 400–600
- Outlier: IBM Plex Mono, weight 500; wordmark and live metrics only
- Display tracking: -0.035em
- Type scale anchor: `--text-display = clamp(1.9rem, 4vw, 2.75rem)`

Fonts load with `swap`; Korean-capable system fallbacks remain available.

## Spacing

The source is `tokens.css`: a 4-point named scale from `--space-3xs` through `--space-3xl`. Page styles use tokens, never raw spacing values.

## Motion

- Easings: `--ease-out`, `--ease-in`, and `--ease-in-out`
- Primitives: button press and state crossfade only
- No ambient loops or page-load reveal
- Reduced motion: opacity-only, at most 120ms

## Microinteractions stance

- Silent success when the resulting state is already visible
- Error or off-screen async result only may use the fixed toast
- Every control has default, hover, focus, active, disabled, loading, error, and success styling
- Focus rings are immediate; touch targets are at least 44px

## CTA voice

- Primary: solid cyan, dark text, 10px radius, specific Korean verb
- Secondary: dark raised surface, rule border, same height and radius
- Destructive: secondary surface with error-colour text; no red-filled button

## Per-page allowances

- App pages must not use enrichment. Product state is the visual content.
- Marketing pages may use one Tier-A or Tier-B enrichment if a route is added later.
- Content pages remain typography-only.

## What pages must share

- SilentOrchestra wordmark
- Night Signal palette and semantic colour roles
- IBM Plex Sans KR + Pretendard pairing
- Workbench button and field voice
- Mobile-first primary-task ordering

## What pages may differ

- Density and number of evidence panels
- Which Workbench rail is sticky on wide screens
- Presence of the learning-state semantic violet

## Exports

### tokens.css

The canonical implementation is [`tokens.css`](tokens.css). It contains the complete colour, type, spacing, motion, rule, radius, shadow, and z-index tokens.

### Tailwind v4 `@theme`

```css
@theme {
  --color-paper: oklch(13% 0.018 255);
  --color-paper-2: oklch(17% 0.022 255);
  --color-paper-3: oklch(21% 0.025 255);
  --color-ink: oklch(95% 0.012 235);
  --color-ink-2: oklch(78% 0.018 235);
  --color-rule: oklch(34% 0.026 255);
  --color-accent: oklch(80% 0.15 210);
  --color-focus: oklch(80% 0.18 205);
  --font-display: "IBM Plex Sans KR", sans-serif;
  --font-body: "Pretendard Variable", sans-serif;
  --font-outlier: "IBM Plex Mono", monospace;
  --spacing-xs: 0.75rem;
  --spacing-sm: 1rem;
  --spacing-md: 1.5rem;
  --spacing-lg: 2rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-md: 1.25rem;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in: cubic-bezier(0.7, 0, 0.84, 0);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
}
```

### DTCG `tokens.json`

```json
{
  "$schema": "https://design-tokens.github.io/community-group/format/",
  "color": {
    "paper": { "$value": "oklch(13% 0.018 255)", "$type": "color" },
    "paper-2": { "$value": "oklch(17% 0.022 255)", "$type": "color" },
    "paper-3": { "$value": "oklch(21% 0.025 255)", "$type": "color" },
    "ink": { "$value": "oklch(95% 0.012 235)", "$type": "color" },
    "ink-2": { "$value": "oklch(78% 0.018 235)", "$type": "color" },
    "rule": { "$value": "oklch(34% 0.026 255)", "$type": "color" },
    "accent": { "$value": "oklch(80% 0.15 210)", "$type": "color" },
    "accent-ink": { "$value": "oklch(16% 0.03 255)", "$type": "color" },
    "focus": { "$value": "oklch(80% 0.18 205)", "$type": "color" }
  },
  "font": {
    "display": { "$value": "IBM Plex Sans KR", "$type": "fontFamily" },
    "body": { "$value": "Pretendard Variable", "$type": "fontFamily" },
    "outlier": { "$value": "IBM Plex Mono", "$type": "fontFamily" }
  },
  "space": {
    "xs": { "$value": "0.75rem", "$type": "dimension" },
    "sm": { "$value": "1rem", "$type": "dimension" },
    "md": { "$value": "1.5rem", "$type": "dimension" },
    "lg": { "$value": "2rem", "$type": "dimension" }
  }
}
```

### shadcn/ui CSS variables

```css
:root {
  --background: 13% 0.018 255;
  --foreground: 95% 0.012 235;
  --card: 17% 0.022 255;
  --card-foreground: 95% 0.012 235;
  --popover: 21% 0.025 255;
  --popover-foreground: 95% 0.012 235;
  --primary: 80% 0.15 210;
  --primary-foreground: 16% 0.03 255;
  --secondary: 21% 0.025 255;
  --secondary-foreground: 78% 0.018 235;
  --muted: 27% 0.023 255;
  --muted-foreground: 68% 0.018 240;
  --border: 34% 0.026 255;
  --input: 34% 0.026 255;
  --ring: 80% 0.18 205;
  --radius: 0.75rem;
}
```
