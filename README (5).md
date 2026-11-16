# Premium Dashboard — Generic SaaS Foundation

A premium, modern SaaS dashboard designed as a **blank, reusable foundation** — not locked to finance, payments, or any domain. Recreated from reference composition: large rounded container centered on light grey, clean white/off-white surfaces, minimal nav, massive heading, header controls, responsive 3-column grid, chart/metric/progress placeholders, gradient announcement, expandable input panel.

## Quick Start

```bash
npm install
npm run dev    # http://localhost:3000
npm run build  # production build
npm run start  # serve production
```

## Theme System — Customize in Seconds

All branding is centralized in `src/app/globals.css` `:root` CSS variables. Edit there — no component changes needed.

```css
:root {
  /* Brand */
  --primary: #635bff;
  --primary-hover: #4f46e5;
  --primary-soft: rgba(99,91,255,0.08);
  --primary-ring: rgba(99,91,255,0.18);
  --secondary: #0ea5e9;
  --accent: #06b6d4;

  /* Surfaces */
  --bg: #eef0f3;                 /* outer page light grey */
  --bg-subtle: #f8fafc;
  --card-bg: #ffffff;            /* card */
  --card-bg-soft: #f8fafc;       /* off-white variant */
  --card-bg-hover: #fbfcfe;
  --text: #0f172a;
  --text-dim: #64748b;
  --text-faint: #94a3b8;
  --border: #e2e8f0;
  --border-soft: #f1f5f9;

  /* Gradients */
  --gradient-from: #635bff;
  --gradient-to: #38bdf8;
  --gradient-card-from: #6366f1;
  --gradient-card-to: #22d3ee;
  --gradient-announcement-from: #1e1b4b;
  --gradient-announcement-to: #4338ca;

  /* Effects */
  --shadow: 0 4px 24px rgba(15,23,42,0.04);
  --shadow-lg: 0 16px 48px rgba(15,23,42,0.08);
  --shadow-card: 0 1px 3px rgba(15,23,42,0.06), 0 4px 16px rgba(15,23,42,0.04);
  --shadow-hover: 0 8px 32px rgba(15,23,42,0.08);
  --radius: 16px;
  --radius-lg: 24px;
  --radius-xl: 32px;
  --radius-sm: 10px;
  --blur: 16px;
  --glass-bg: rgba(255,255,255,0.72);
  --glass-border: rgba(15,23,42,0.06);
}
html[data-theme="dark"] { /* complete dark override — copy :root and adjust */ }
```

**Toggle dark/light:** `html[data-theme="dark"]` — persisted in `localStorage`, button in TopNav.

## Layout

```
Outer:  min-h-screen bg-[var(--bg)] p-8 flex justify-center
  Container: max-w-[1360px] bg-[var(--card-bg)] rounded-[var(--radius-xl)] shadow-[var(--shadow-lg)] border overflow-hidden
    ├─ TopNav: logo + pill nav + search ⌘K + bell + avatar
    ├─ Header: Dashboard Overview (30px extrabold) + All Teams / Last 7 days / Export / New Project
    └─ Canvas: bg-[#f8f9fb] p-7 space-y-5
         ├─ View pills (Overview/Performance/Reports) + Live indicator
         ├─ Row 1: 3 metric cards (Total Views sparkline, Active Sessions progress+miniBars, Conversion)
         ├─ Row 2: Performance Analytics line chart (col-span-2) + Traffic Sources donut (col-span-1)
         ├─ Row 3: Recent Activity + Team Progress + Storage Usage (3 equal)
         ├─ Row 4: Gradient announcement (col-span-2, from-[#1e1b4b] to-[#4338ca]) + Quick Metrics 2x2 (col-span-1)
         └─ Row 5: Assistant expandable input (chat + chips + textarea expand on focus) + Tasks + Integrations
```

All cards: `rounded-[var(--radius)] border-[var(--border)] shadow-[var(--shadow-card)] hover:translateY(-2px) hover:shadow-[var(--shadow-hover)]`.

## Components

```
src/
  app/
    layout.tsx           # font + metadata
    page.tsx             # assembles grid — generic placeholder labels only
    globals.css          # ★ THEME — edit variables here
  components/
    ui/
      card.tsx           # Card, CardHeader, CardTitle, CardContent
      button.tsx         # Button (primary/secondary/ghost/outline), IconButton
      badge.tsx          # Badge tones
    TopNav.tsx           # logo placeholder, nav links, search, notification, profile icons
    HeaderControls.tsx   # heading + dropdowns, date selector, action button
    Charts.tsx           # Sparkline, LineChartPlaceholder, DonutChart, MiniBars, Progress
    ExpandablePanel.tsx  # chat messages + expandable bottom input panel
```

Reusable — import `Card` anywhere, pass `className`, `hover={false}` to disable lift.

## Customization Checklist

- [ ] Change `--primary`, `--secondary`, `--accent` for brand colors
- [ ] Swap `--bg` outer grey, `--card-bg` surfaces
- [ ] Adjust `--radius-*` for sharper/softer corners
- [ ] Tweak `--shadow` intensity
- [ ] Replace placeholder copy (`Total Views`, `Performance Analytics` etc.) with your domain
- [ ] Connect charts: swap `LineChartPlaceholder` SVG with Recharts/Chart.js using same props
- [ ] Wire search + filters to your API (currently dummy)
- [ ] Connect Assistant panel textarea to your backend (see `ExpandablePanel.tsx` `send()`)

## Stack

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS (content: src/app, src/components)
- lucide-react icons
- CSS variables for theming (light/dark)

## Connecting to API Hunter Backend

Classic Python backend runs at `http://127.0.0.1:8787`. To proxy from Next.js:

```ts
// next.config.mjs
const nextConfig = {
  async rewrites() {
    return [{ source: '/api/:path*', destination: 'http://127.0.0.1:8787/api/:path*' }]
  }
}
```

Then `fetch('/api/state')` etc. work from dashboard.

Or keep dashboards separate — premium is generic foundation, classic shows hunts.

## Responsive

- Desktop: 3-col grid
- Tablet: 2-col + stacked
- Mobile: 1-col, collapsible nav, hidden date picker variant, full-width cards

## License

MIT — part of api-hunter repo.

## Disclaimer
This dashboard is a generic foundation — you are responsible for what you connect. Hunt only authorized targets.
