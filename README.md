<p align="center">
  <img src="https://img.shields.io/github/stars/Dev-PlutoPglu/api-hunter?style=for-the-badge&logo=github&color=635bff" alt="stars"/>
  <img src="https://img.shields.io/badge/Made%20for%20Hackers-black?style=for-the-badge" alt="hackers"/>
  <img src="https://img.shields.io/badge/Reverse%20Engineering-JS%20%7C%20APK-0ea5e9?style=for-the-badge" alt="reverse"/>
</p>

# 🔍 API Hunter — The Most Complete API Discovery & Reverse Engineering Toolkit

<p align="center">
  <a href="https://github.com/Dev-PlutoPglu/api-hunter/stargazers"><img src="https://img.shields.io/github/stars/Dev-PlutoPglu/api-hunter?style=social" alt="stars"/></a>
  <a href="https://github.com/Dev-PlutoPglu/api-hunter/network/members"><img src="https://img.shields.io/github/forks/Dev-PlutoPglu/api-hunter?style=social" alt="forks"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="license"/></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-blue.svg" alt="python"/>
  <img src="https://img.shields.io/badge/dashboard-premium%20SaaS-635bff" alt="dashboard"/>
  <img src="https://img.shields.io/badge/reverse-website%20%7C%20APK-0ea5e9" alt="reverse"/>
  <img src="https://img.shields.io/badge/coverage-2500%2B%20APIs-brightgreen" alt="coverage"/>
</p>

<p align="center"><b>Hunt free APIs from GitHub & the internet • Reverse-engineer hidden APIs from any website or APK • Test every endpoint live • Hunt OpenAPI/Swagger metadata • Gorgeous dashboards</b></p>

<p align="center">
  <a href="#-quick-start"><b>Quick Start</b></a> •
  <a href="#-premium-dashboard">Premium Dashboard</a> •
  <a href="#-reverse-engineering">Reverse Engineering</a> •
  <a href="#-why-api-hunter">Why Best?</a> •
  <a href="docs/ARCHITECTURE.md">Architecture</a>
</p>

<p align="center">⭐ <b>If this tool saves you time, please star the repo — it helps a lot!</b> ⭐</p>

```
 _    ____ ___ ____   _   _    _   _ _____ ___ ____  _   _ __  __
/ \  |  _ \_ _|  _ \ / \ | |  | | | |_   _|_ _|  _ \| | | |  \/  |
/ _ \ | |_) | || |_) / _ \| |  | |_| | | |  | || |_) | |_| | |\/| |
/ ___ \|  __/| ||  __/ ___ \ |___|  _  | | |  | ||  _ < |  _  | |  | |
/_/   \_\_|  |___|_| /_/   \_____|_| |_| |_| |___|_| \_\|_| |_|_|  |_|
```

---

## 🎬 Demo

<p align="center">
  <img src="docs/screenshots/01-premium-dashboard.png" width="100%" alt="API Hunter Premium Dashboard — Hunt Reverse Test — Light Theme" />
  <br><em>Premium Dashboard — Light Theme • Hunt. Reverse. Test. • 48% Progress • Results Table</em>
</p>

<p align="center">
  <img src="docs/screenshots/02-dark-mode.png" width="100%" alt="API Hunter Dashboard — Dark Mode" />
  <br><em>Dark Mode • Same components, production-ready theming</em>
</p>

<p align="center">
  <img src="docs/screenshots/03-terminal.png" width="100%" alt="API Hunter Terminal — Live Hunt" />
  <br><em>Terminal — <code>python3 apihunter.py run -k weather -n 20</code> → 1462 APIs → Rich table → WORKING / KEY NEEDED / RATE LIMITED</em>
</p>

> **Terminal:** Rich tables + live progress • **Classic Dashboard:** `http.server` SSE @ `:8787` • **Premium Dashboard:** Next.js light premium @ `:3000`

```bash
$ python3 apihunter.py run -k crypto -a none --endpoints deep -n 30

[*] stage 1/4: hunting catalogs (github + internet)
[*] 1462 unique APIs discovered → 12 after filters
[*] stage 2/4: testing endpoints (12 workers)
[*] stage 3/4: analysing metadata + hunting metadata APIs
[*] stage 4/4: reporting

                        API HUNT RESULTS
┌──────────────┬──────────────┬─────────┬──────────────┬──────┬──────┬──────────────────────────┐
│ API          │ Source       │ Auth    │ Status       │ HTTP │  ms  │ URL                      │
├──────────────┼──────────────┼─────────┼──────────────┼──────┼──────┼──────────────────────────┤
│ Cat Facts    │ builtin      │ none    │ WORKING      │ 200  │  312 │ https://catfact.ninja    │
│ CoinGecko    │ apisguru     │ none    │ WORKING      │ 200  │  420 │ https://api.coingecko.com│
│ WeatherAPI   │ github       │ apiKey  │ KEY NEEDED   │ 401  │  180 │ https://api.weatherapi.com│
└──────────────┴──────────────┴─────────┴──────────────┴──────┴──────┴──────────────────────────┘
```

**Dashboards:** Hunt live in browser — start a hunt, watch logs stream, donut updates, results table filters, click any row for headers/rate-limits/secrets.

| Classic (Dark) | Premium (Light) |
|---|---|
| `python3 apihunter.py ui` → `:8787` • gradient orbs • glass panels • SSE | `cd dashboard-premium && npm run dev` → `:3000` • light-grey outer + white rounded container • CSS-variable theming |



---

## ✨ Features — Why 1,000+ Devs Will Star This

| Area | What You Get |
|---|---|
| **Hunt** | `public-apis/public-apis` + GitHub awesome-list search + **APIs.guru 2500+ OpenAPI specs** + builtin catalog — deduplicated by `url_key` |
| **Reverse Website** | Download HTML + up to 60 JS assets, mine `fetch`/`axios`/`XHR`/`baseURL`/`/api/v1…`/`GraphQL` + hardcoded secrets (AKIA, AIza, ghp, sk-, Firebase…) — static, safe |
| **Reverse APK** | Unzip APK → DEX strings + `AndroidManifest.xml` + `resources.arsc` + `assets/` → same miners + package/permissions context. `--apk-deep` runs `apktool`/`jadx` if installed |
| **Test** | Concurrent workers (default 12), per-request timeout, 6-state classification: `WORKING` `KEY NEEDED` `RATE LIMITED` `NEEDS PARAMS` `DEAD` `ERROR` |
| **Metadata** | Probe `/openapi.json`/`/swagger.json`/`/api-docs`/`/v3/api-docs`/`/.well-known/openid-configuration`/`/health` — parse for endpoints + auth, capture rate-limit headers + JSON shape |
| **Secrets** | Regex for API keys/tokens — reported **masked** (`sk-****abcd`) |
| **Reports** | `catalog.json` `results.json` `api-hunt-report.json/csv/md` + summary + history |
| **Dashboards** | Classic (stdlib, offline) + Premium (Next.js, Tailwind, Lucide, theme variables, responsive) — live logs, donut, sortable table, metadata cards, automations, webhooks |
| **Automations** | Scheduled hunts every N mins, Discord/Slack webhooks, presets (localStorage), retry failed APIs, hunt history (20 runs) |
| **Custom** | Headers (`-H "X-Api-Key: …"`), insecure TLS skip, deep endpoint testing, GitHub token, workers/timeout tuning |

---

## 📊 Why API Hunter vs Others?

| Tool | Sources | Reverse | Test | Metadata | Dashboard | Secrets | Offline |
|---|---|---|---|---|---|---|---|
| **API Hunter** | 4 (GitHub+APIs.guru+public-apis+builtin) | ✅ Web + APK (DEX/JS) | ✅ Concurrent + deep | ✅ OpenAPI/Swagger/OpenID | ✅ 2 dashboards (SSE + Next.js) | ✅ Masked | ✅ |
| public-apis list | 1 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| APIs.guru explorer | 1 | ❌ | ❌ | ✅ | ✅ basic | ❌ | ❌ |
| Generic scrapers | 1 | ⚠️ partial | ❌ | ❌ | ❌ | ❌ | ❌ |

**Bottom line:** Only API Hunter does *hunt + reverse + test + metadata + report + live UI* in one MIT-licensed tool.

---

## 📥 Install — Git Clone

```bash
# 1. Clone the repo
git clone https://github.com/Dev-PlutoPglu/api-hunter.git
cd api-hunter

# 2. Install Python deps (Python 3.9+)
pip install -r requirements.txt
# Optional pretty tables + YAML
pip install rich PyYAML

# 3. Or install as command
pip install .
apihunter --help

# 4. Run premium dashboard (needs Node 18+)
cd dashboard-premium
npm install
npm run dev        # http://localhost:3000
# Classic dashboard
python3 apihunter.py ui  # http://127.0.0.1:8787
```

**One-liner (Linux/macOS):**
```bash
git clone https://github.com/Dev-PlutoPglu/api-hunter.git && cd api-hunter && pip install -r requirements.txt && python3 apihunter.py run -k weather -n 20
```

**Docker:**
```bash
git clone https://github.com/Dev-PlutoPglu/api-hunter.git && cd api-hunter
docker build -t api-hunter .
docker run -p 8787:8787 api-hunter
```

**Vercel — One-click deploy premium dashboard:**
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Dev-PlutoPglu/api-hunter&project-name=api-hunter&root-directory=dashboard-premium)

---

## 🚀 Quick Start

```bash
# Clone & install (Python 3.9+)
git clone https://github.com/Dev-PlutoPglu/api-hunter.git
cd api-hunter
pip install -r requirements.txt          # requests (+ rich, PyYAML optional)
# pip install .                         # optional: adds `apihunter` command

# Full pipeline — hunt crypto APIs, test, metadata, report
python3 apihunter.py run -k crypto -a none --endpoints deep -n 30

# Just catalog (fast, no testing)
python3 apihunter.py discover -k animals -n 100 -s public-apis,apisguru

# Reverse-engineer a website
python3 apihunter.py reverse-web https://example.com --max-js 20

# Reverse-engineer an APK (deep if apktool/jadx installed)
python3 apihunter.py reverse-apk ./app.apk --apk-deep

# Re-test / re-report
python3 apihunter.py test apihunter_out/catalog.json
python3 apihunter.py metadata apihunter_out/results.json
python3 apihunter.py report apihunter_out/results.json

# Dashboards
python3 apihunter.py ui --port 8787                 # classic @ 127.0.0.1:8787
cd dashboard-premium && npm install && npm run dev  # premium @ localhost:3000
```

**Docker:**
```bash
docker build -t api-hunter .
docker run -p 8787:8787 -v $(pwd)/apihunter_out:/app/apihunter_out api-hunter
# docker-compose up — runs both dashboards
```

Reports: `apihunter_out/{catalog.json,results.json,api-hunt-report.{json,csv,md}}`

---

## 🖥️ Premium Dashboard — Light SaaS, Fully Customizable

**Visual:** Large white `rounded-[32px]` container centered on light-grey `#eef0f3` page, soft shadows, 16px card radius, glass accents — premium minimalist.

**TopNav:** API HUNTER logo + pill nav + search `⌘K` + status pill + theme toggle + GitHub

**Header:** `Hunt. Reverse. Test.` 32px gradient + `LIVE` pill + mode/sources + Start Hunt

**Canvas (`#f8f9fb`):**
- Stats 6 cards (Discovered/Tested/Working/Dead/Meta/Secrets) — 3-col grid
- Progress + Donut (2+1 col) — live logs, 86% donut
- Hunt Controls — keyword/category/auth/limit/workers/timeout + headers + Start/Stop/Retry
- Reverse — Website JS Mining + APK DEX Mining (gradient CTAs)
- Results — sortable, chips (All/WORKING/KEY NEEDED…), search, copy working, detail modal
- Metadata/Secrets + History + Reports + Pro Tip gradient
- Bottom: Gradient announcement `from-[#1e1b4b] to-[#4338ca]` + Assistant expandable input (chat + textarea expands on focus)

**Theme:** Edit `dashboard-premium/src/app/globals.css` `:root` — `--primary`, `--bg`, `--card-bg`, `--border`, `--shadow`, `--radius`, `--blur` → entire app re-themes. Dark/light toggle included.

```css
:root { --primary:#635bff; --bg:#eef0f3; --card-bg:#ffffff; --radius:16px; }
html[data-theme="dark"] { --bg:#060918; --card-bg:#111827; }
```

See [`dashboard-premium/README.md`](dashboard-premium/README.md) + [`docs/DASHBOARD_THEME.md`](docs/DASHBOARD_THEME.md).

---

## 🤖 AI Next Level — NEW!

**1. Natural Language Hunt:**
```bash
python3 apihunter.py run --nl "mujhe free weather apis chahiye jo fast ho"
# Dashboard: natural language input → AI (Groq/OpenAI if OPENAI_API_KEY set) parses to keyword/category/auth
```
Set `OPENAI_API_KEY` or `GROQ_API_KEY` for LLM, else heuristic fallback works offline.

**2. AI Docs Generator:** Every working API gets `ai_docs` — `curl`, Python `requests`, JS `fetch` snippets. `report.json` me `ai_docs` field. Set `OPENAI_API_KEY` for richer docs.

**3. Self-Healing Tests:** `NEEDS_PARAMS` (400/422) pe LLM valid JSON body generate karke `POST` retry → many `needs_params` → `working` ban jate hain.

## 🛡️ Security Pro — NEW!

**4. Nuclei + OWASP Top 10:** If `nuclei` installed, `nuclei -t http/misconfiguration/` auto runs on top 5 targets; else heuristic checks (BOLA `/{id}/\d+`, Broken Auth no-HTTPS). Results `report.json` → `owasp` field.

**5. CVE Auto-Scan:** `Server: nginx/1.18.0` → `https://cve.circl.lu/api/cvefor/nginx/1.18.0` → CVE list in report (`cves` field). Known old versions fallback.

**6. Secret Validation:** `AKIA...` → `LEAKED` (critical), `ghp_...` → live `api.github.com/user` check `VALID/INVALID`, `AIza...` → Google probe. See `apihunter/security.py` → `validate_secret()`.

---

## 🧬 Reverse Engineering — How It Works

**Website:** Fetch HTML → collect `<script src>` (capped `max_js`) → mine HTML+JS for absolute API URLs, `fetch("…")`, `axios`, `XHR.open`, `baseURL`, `"/api/…"` paths, GraphQL, secrets → normalize + dedup → test pipeline.

**APK:** Open as ZIP → extract strings from `classes*.dex`, `AndroidManifest.xml`, `resources.arsc`, `assets/**` → same miners + package/permissions → optional `apktool d` / `jadx -d` deep scan → test pipeline.

> Use only on sites/APKs you own/have permission. Secrets are masked.

Try safely: `python3 tools/make_test_apk.py` → `tools/synthetic-app.apk` (fake) & `synthetic-app-real.apk` (real APIs).

---

## 📁 Project Layout

```
api-hunter/
├── apihunter.py, apihunter/{cli,config,sources,reverse,tester,metadata,report,ui,util}.py
├── dashboard.html (classic standalone)
├── dashboard-premium/ (Next.js 14 + TS + Tailwind + Lucide)
│   ├── src/app/{globals.css ★,layout.tsx,page.tsx}
│   └── src/components/{TopNav,Charts,HuntStats,ProgressDonut,ResultsTable,ReversePremium,ExpandablePanel}
├── tools/{make_test_apk.py,synthetic-app.apk}
├── docs/{ARCHITECTURE.md,REVERSE_ENGINEERING.md,DASHBOARD_THEME.md}
├── pyproject.toml, requirements.txt, Dockerfile, docker-compose.yml
```

---

## 🗺️ Roadmap — Help Us Star!

- [x] Hunt 4 sources + reverse web/apk
- [x] Concurrent testing + 6-state classification
- [x] Metadata hunting + secrets masked
- [x] Classic + Premium dashboards + SSE
- [ ] VS Code extension
- [ ] Cloud hosted hunter
- [ ] AI-powered endpoint parameter inference
- [ ] One-click deploy to Vercel

⭐ **Star this repo** to vote for next feature! Open an issue to request.

---

## 🤝 Contributing

PRs welcome! Quick checks:

```bash
python3 build_dashboard.py && node test_dashboard_runtime.js
cd dashboard-premium && npm run build
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md). MIT — use it, fork it, ship it.

---

## 🙏 Acknowledgments

- [public-apis/public-apis](https://github.com/public-apis/public-apis) • [APIs.guru](https://apis.guru)
- Built with `requests`, `rich`, `PyYAML`, Next.js, Tailwind, Lucide

<p align="center"><b>Hunt responsibly</b> — test only APIs you’re allowed. This tool helps you find <i>your own</i> exposed endpoints & keys.</p>

<p align="center">Made with ❤️ for hackers, by hackers — <a href="https://github.com/Dev-PlutoPglu/api-hunter/stargazers">give us a ⭐</a></p>

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Dev-PlutoPglu/api-hunter&type=Date)](https://star-history.com/#Dev-PlutoPglu/api-hunter&Date)
---

## ⚠️ Disclaimer

**This tool is provided AS-IS, for educational and authorized testing only (MIT License). The author (`Dev-PlutoPglu`) assumes NO responsibility for how you use it.**

**Your Responsibilities:**
- ✅ Only run `reverse-web` / `reverse-apk` on sites and APKs you own or have explicit permission to test
- ✅ Respect all free-tier limits, rate limits, and Terms of Service — do not abuse, scrape excessively, or DDoS any API
- ✅ Immediately rotate any exposed secrets found (`AKIA...`, `ghp_...`, `sk-...`, `AIza...`) and never share them publicly
- ✅ Run `nuclei`, CVE scans, and vulnerability checks only on authorized targets

**Prohibited Use:**
- ❌ Mining or reverse-engineering any APK, website, or API without permission
- ❌ Using leaked keys or tokens to access, exfiltrate, or manipulate data
- ❌ Bypassing rate limits, paywalls, or authentication to disrupt services

**By using this tool, you agree:** You accept full legal responsibility for your actions. The author shall not be held liable for any damages, bans, account suspensions, or legal consequences resulting from your use. **Hunt responsibly.**

**Responsible Disclosure:** If this tool helps you discover a real leaked secret, exposed endpoint, or CVE, please follow responsible disclosure — notify the owner directly and privately, do not publish or exploit it.

*Built for defenders, by defenders — use it to secure, not to harm.*

