# Architecture — API Hunter

```
                        ┌─────────────────┐
                        │  CLI (cli.py)   │
                        │  run/discover/  │
                        │  reverse/test/  │
                        └────────┬────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌───────────────┐        ┌───────────────┐        ┌──────────────┐
│ sources.py    │        │ reverse.py    │        │ tester.py    │
│ • public-apis │        │ • website JS  │        │ • concurrent │
│ • apis.guru   │        │ • APK ZIP/DEX │        │ • classify   │
│ • github      │        │ • apktool/jadx│        │ • latency    │
│ • builtin     │        └───────┬───────┘        └──────┬───────┘
└───────┬───────┘                │                       │
        └────────────┬───────────┘                       │
                     ▼                                   ▼
              ┌─────────────┐                     ┌──────────────┐
              │  config.py  │                     │ metadata.py  │
              │  tunables   │◄────────────────────│ • openapi    │
              │  catalog    │                     │ • swagger    │
              └─────────────┘                     │ • health     │
                     │                            └──────┬───────┘
                     ▼                                   ▼
              ┌─────────────┐                     ┌──────────────┐
              │  report.py  │                     │   util.py    │
              │  JSON/CSV/MD│                     │  HTTP helpers│
              │  summary    │                     └──────────────┘
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │   ui.py     │  http.server + SSE
              │  (classic)  │  live logs, donut, table, history
              └──────┬──────┘
                     │  API: /api/start, /api/state, /api/results, /events
                     │
              ┌──────▼──────────────┐
              │ dashboard-premium/  │  Next.js 14 + Tailwind + Lucide
              │  generic SaaS UI   │  theme via CSS variables
              │  3-col grid, charts│  proxies to :8787 or standalone
              └────────────────────┘
```

## Data Flow

1. **Discover**: `sources.discover()` → list[APIEntry] (url, name, auth, category, source)
2. **Filter**: `cli.filter_entries()` by keyword/category/auth/limit
3. **Test**: `tester.run()` concurrent workers → enrich each entry with `test: {status, http_status, latency_ms, sample}`
4. **Metadata**: `metadata.run()` probe metadata endpoints → `metadata_apis[]`, `metadata{server, ratelimit, json}`, `secrets[]`, `endpoints[]`
5. **Report**: `report.save_report()` → `apihunter_out/` + summary
6. **UI**: `ui.STATE` holds live state, SSE pushes to browser, history archived

## Key Concepts

- **APIEntry**: dict with `name, url, base_url, category, auth, source, description, test, metadata, metadata_apis, secrets, endpoints`
- **Classification**: pure function of HTTP code + body inspection
- **Secret Mining**: regex for AKIA, AIza, ghp, sk-, xoxb, Firebase etc. — masked after detection
- **Reverse**: string mining, not execution — safe static analysis
```

cat > /home/user/api-hunter/docs/REVERSE_ENGINEERING.md <<'MD'
# Reverse Engineering — Website & APK Deep Dive

## Website Mining (`reverse.py: hunt_from_target("web", url, args)`)

### 1. Fetch HTML
`util.http_get(url)` with timeout + UA. Parse with regex (no heavy deps) for:

### 2. Collect JS Assets
- `<script src="...">` absolute + relative resolution
- `link[rel=modulepreload]` as JS
- Deduplicate, cap `max_js` (default 15, up to 60)
- Fetch each with `http_get`, keep text if `content-type` js/json/html

### 3. Mine Strings
Single pass over `html + "\n".join(js_texts)`:

| Pattern | Example | Regex |
|---|---|---|
| Absolute API URL | `https://api.example.com/v1/users` | `https?://[^\s"'<>]+(?:api\|v1\|graphql\|oauth)` |
| Fetch/Axios | `fetch("/api/v1/users")` | `fetch\s*\(\s*["']([^"']+)["']` |
| XHR | `.open("GET", url)` | `\.open\s*\(\s*["']GET["']\s*,\s*["']([^"']+)["']` |
| baseURL | `baseURL: "https://api.foo.com"` | `(?:baseURL\|apiUrl\|API_BASE)\s*[:=]\s*["']([^"']+)["']` |
| Path strings | `"/api/v1/users"` | `"(\/api\/[^"']+)"` |
| GraphQL | `https://api.example.com/graphql` | `graphql` + URL ctx |
| Secrets | `AKIA...`, `ghp_...` | see `config.SECRET_PATTERNS` |

### 4. Normalize
- Resolve relative paths against page origin
- Deduplicate by `url_key` (lowercase host+path)
- Filter obvious non-APIs (cdn, analytics)
- Save as `catalog` entries with `source: "reverse-web"`

### 5. Test Pipeline
Same as normal hunt: `tester.run()` → `metadata.run()` → `report`.

---

## APK Mining (`hunt_from_target("apk", path, args)`)

### 1. Open as ZIP
`zipfile.ZipFile(apk)` — no extraction to disk

### 2. Strings Extraction
- `classes*.dex`: read bytes, extract printable ASCII 4+ (`re.findall(b"[ -~]{4,}")`)
- `AndroidManifest.xml`: try `ET.fromstring` (if plaintext) else regex search
- `resources.arsc`: byte string scan
- `assets/**`: read as utf-8
- `res/values/strings.xml`: parse XML

### 3. Same Miners
Run website miners over `"\n".join(all_strings)` → candidates

### 4. Context
- Parse `package` from manifest (`package="com.example.app"`)
- Parse `uses-permission` list
- Attach to report header

### 5. Deep Scan (`--apk-deep`)
If `apktool` on PATH: `apktool d app.apk -o /tmp/decode` → mine `smali/**/*.smali`
If `jadx` on PATH: `jadx -d /tmp/jadx app.apk` → mine `*.java`
Merge + deduplicate

### Example
```bash
python3 apihunter.py reverse-apk tools/synthetic-app.apk -v
# => logs: [reverse-apk] found 12 candidates (8 urls, 4 paths, 2 secrets)
# => tester: 12 tested, 2 working, 1 key-needed
```

### Security Note
- Never run on APKs you don't own/have permission for
- Secrets are masked (`sk-****abcd`) in reports
- No dynamic execution, only static string mining
```

cat > /home/user/api-hunter/docs/DASHBOARD_THEME.md <<'MD'
# Dashboard Theme System — Customization Guide

All theming is **CSS variables** in `dashboard-premium/src/app/globals.css`. No JS changes needed.

## Variables

| Category | Variable | Default | Effect |
|---|---|---|---|
| Brand | `--primary` | `#635bff` | Buttons, links, active nav, progress |
|  | `--primary-hover` | `#4f46e5` | Hover state |
|  | `--primary-soft` | `rgba(99,91,255,0.08)` | Soft backgrounds, chips |
|  | `--secondary` | `#0ea5e9` | Secondary chart line, accents |
|  | `--accent` | `#06b6d4` | Tertiary accents |
| Surfaces | `--bg` | `#eef0f3` | Outer page light grey |
|  | `--card-bg` | `#ffffff` | Card background |
|  | `--card-bg-soft` | `#f8fafc` | Off-white variant, input BG |
| Text | `--text` | `#0f172a` | Primary |
|  | `--text-dim` | `#64748b` | Secondary muted |
|  | `--text-faint` | `#94a3b8` | Tertiary faint, labels |
| Borders | `--border` | `#e2e8f0` | Card borders |
|  | `--border-soft` | `#f1f5f9` | Subtle dividers |
| Gradients | `--gradient-from` | `#635bff` | Button/announcement |
|  | `--gradient-to` | `#38bdf8` | Button/announcement |
|  | `--gradient-announcement-from` | `#1e1b4b` | Large feature card |
| Effects | `--shadow` | `0 4px 24px…` | Card shadow |
|  | `--shadow-lg` | `0 16px 48px…` | Container shadow |
|  | `--radius` | `16px` | Card radius |
|  | `--radius-xl` | `32px` | Container radius |
|  | `--blur` | `16px` | Glass backdrop |

## How to Rebrand

1. Open `src/app/globals.css`
2. Edit `:root` values — e.g.:
   ```css
   :root {
     --primary: #ec4899; /* pink brand */
     --bg: #fdf2f8;
     --radius: 12px; /* sharper */
   }
   ```
3. Save — hot reload updates preview
4. Dark mode: edit `html[data-theme="dark"]` block similarly

## Examples

**Corporate Blue:**
```css
--primary: #0f62fe; --bg: #f4f6f8; --radius: 10px;
```

**Neon Dark:**
```css
:root { --bg: #050508; --card-bg: #111115; --text: #f5f5f7; --primary: #00e5ff; }
html[data-theme="dark"] { --bg: #000; }
```

**Warm Minimal:**
```css
--primary: #ff6b35; --bg: #fef9f3; --card-bg: #ffffff; --border: #fde8d8;
```

## Component Usage

Cards use variables automatically:
```tsx
<Card className="p-5"> {/* bg-[var(--card-bg)] border-[var(--border)] ... */}
<Button variant="primary"> {/* bg-[var(--primary)] */}
```

No hardcoded colors — everything flows from CSS variables.
```

cat > /home/user/api-hunter/CONTRIBUTING.md <<'MD'
# Contributing to API Hunter

## Setup

```bash
git clone https://github.com/Dev-PlutoPglu/api-hunter.git
cd api-hunter
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r dashboard-premium/package.json # npm
```

## Pre-commit Checks

```bash
# Python
python3 -m py_compile apihunter/*.py
python3 build_dashboard.py
node test_dashboard_runtime.js

# Premium dashboard
cd dashboard-premium
npm run build
```

## PR Guidelines

- Keep terminal tool stdlib-light (requests + optional rich/PyYAML only)
- Premium dashboard: edit `src/app/globals.css` for theme, `page.tsx` for layout
- Reusable components belong in `src/components/ui/`
- No hardcoded colors — use CSS variables
- Add tests for new miners in `reverse.py`

## Release

```bash
# bump version in pyproject.toml + dashboard-premium/package.json
git tag v1.1.0 && git push --tags
```
