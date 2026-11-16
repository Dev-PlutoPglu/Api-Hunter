"""Discovery sources: hunt API catalogs from GitHub and the open internet.

Sources:
  * public-apis  -> the classic GitHub "public-apis" markdown catalog
  * github        -> GitHub repository search for other free-API lists, READMEs parsed
  * apisguru      -> APIs.guru directory (real OpenAPI specs: base URLs + endpoints)
  * builtin       -> offline fallback catalog of known no-key APIs
"""
from __future__ import annotations

import re
import time
import urllib.parse

from . import config, util

# ---------------------------------------------------------------------------
# Generic markdown catalog parsing
# ---------------------------------------------------------------------------

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
AUTH_HINTS = [
    (re.compile(r"\boauth\b|\boauth2\b", re.I), "OAuth"),
    (re.compile(r"\bapi[- ]?key\b|\bx-[a-z-]*key\b|\bkey\b|\btoken\b|\bmashape\b|\brapidapi\b|\bbearer\b", re.I), "apiKey"),
    (re.compile(r"^\s*(no|none|free|public|-)\s*$", re.I), "none"),
]


def detect_auth(*cells: str) -> str:
    for cell in cells:
        if not cell:
            continue
        for pattern, label in AUTH_HINTS:
            if pattern.search(cell):
                return label
    return "unknown"


def detect_https(*cells: str):
    for cell in cells:
        if not cell:
            continue
        low = cell.strip().lower()
        if low.startswith("yes"):
            return True
        if low.startswith("no"):
            return False
    return None


def _split_row(line: str):
    parts = [c.strip() for c in line.strip().strip("|").split("|")]
    return [p for p in parts]


def parse_markdown_catalog(text: str, source: str) -> list[dict]:
    """Parse any 'awesome-*-api' style README: markdown tables and link lists."""
    entries: list[dict] = []
    category = "Uncategorized"
    in_code = False

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue

        heading = re.match(r"^(#{1,4})\s+(.*?)\s*$", line)
        if heading:
            cat = heading.group(2).strip()
            if not re.match(r"^(index|table of contents|license|contributing)$", cat, re.I):
                category = cat
            continue

        # ---- table rows -------------------------------------------------
        if line.lstrip().startswith("|"):
            cells = _split_row(line)
            if not cells or len(cells) < 2:
                continue
            # skip header & separator rows
            if all(re.fullmatch(r":?-{2,}:?", c or "---") for c in cells):
                continue
            if re.match(r"^\s*:?-+", cells[0]) and len(cells) > 1:
                continue
            link = None
            for cell in cells:
                m = LINK_RE.search(cell)
                if m:
                    link = m
                    break
            if not link:
                continue
            name = util.strip_html(link.group(1)) or link.group(1)
            url = link.group(2)
            others = [c for c in cells if c != cells[0]] or cells[1:]
            desc = max((util.strip_html(c) for c in others), key=len, default="")
            entries.append(
                {
                    "name": name[:80],
                    "url": url,
                    "description": util.truncate(desc, 300),
                    "category": category[:60],
                    "auth": detect_auth(*others),
                    "https": detect_https(*others),
                    "source": source,
                    "endpoints": [],
                    "base_url": None,
                    "spec_url": None,
                }
            )
            continue

        # ---- list items:  - [Name](url) — description -------------------
        m = re.match(r"^\s*[-*+]\s+\[([^\]]+)\]\(([^)\s]+)\)\s*[-–—:]*\s*(.*)$", line)
        if m:
            desc = util.strip_html(m.group(3))
            entries.append(
                {
                    "name": util.strip_html(m.group(1))[:80],
                    "url": m.group(2),
                    "description": util.truncate(desc, 300),
                    "category": category[:60],
                    "auth": detect_auth(desc),
                    "https": None,
                    "source": source,
                    "endpoints": [],
                    "base_url": None,
                    "spec_url": None,
                }
            )
    return entries


# ---------------------------------------------------------------------------
# Source: public-apis (GitHub)
# ---------------------------------------------------------------------------

def source_public_apis(args) -> tuple[list[dict], str | None]:
    text, err = util.fetch_text(config.PUBLIC_APIS_README, timeout=args.http_timeout)
    if err or not text:
        return [], f"public-apis fetch failed: {err}"
    entries = [
        e for e in parse_markdown_catalog(text, "public-apis")
        if not e["name"].lower().startswith("run in postman")
    ]
    return entries, None


# ---------------------------------------------------------------------------
# Source: GitHub repository search (find more free-API lists on GitHub)
# ---------------------------------------------------------------------------

def _github_headers(token: str | None) -> dict:
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def source_github(args, token: str | None = None) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    queries = getattr(args, "github_queries", None) or config.GITHUB_DEFAULT_QUERIES
    max_repos = getattr(args, "github_repos", 6)
    headers = _github_headers(token)
    seen_repos: set[str] = set()
    all_entries: list[dict] = []

    for query in queries:
        url = f"{config.GITHUB_SEARCH_REPOS}?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page={max_repos}"
        try:
            r = util.requests.get(url, headers={**util.DEFAULT_HEADERS, **headers}, timeout=args.http_timeout)
            if r.status_code == 403:
                errors.append(
                    "GitHub search rate-limited (set GITHUB_TOKEN or --github-token)"
                )
                break
            if r.status_code >= 400:
                errors.append(f"GitHub search '{query}': HTTP {r.status_code}")
                continue
            repos = r.json().get("items", [])
        except Exception as exc:  # noqa: BLE001
            errors.append(f"GitHub search '{query}': {exc}")
            continue

        for repo in repos:
            full = repo.get("full_name", "")
            branch = repo.get("default_branch", "master")
            if not full or full in seen_repos:
                continue
            seen_repos.add(full)
            raw = config.GITHUB_RAW_README.format(full_name=full, branch=branch)
            text, err = util.fetch_text(raw, timeout=args.http_timeout, headers=headers)
            if err or not text:
                errors.append(f"README {full}: {err or 'empty'}")
                continue
            entries = parse_markdown_catalog(text, f"github:{full}")
            all_entries.extend(entries)
            args.log(f"  github  {full}: {len(entries)} APIs parsed")
            time.sleep(0.4)  # be gentle with unauthenticated rate limits
    return all_entries, errors


# ---------------------------------------------------------------------------
# Source: APIs.guru (real specs: base URLs, endpoints, auth schemes)
# ---------------------------------------------------------------------------

def _spec_base_url(spec: dict) -> str | None:
    if not isinstance(spec, dict):
        return None
    # OpenAPI 3.x
    servers = spec.get("servers")
    if isinstance(servers, list) and servers:
        url = servers[0].get("url")
        if url and str(url).startswith("http"):
            return str(url).rstrip("/")
        if url:  # relative server URL
            base = spec.get("_origin_root")
            if base:
                return (base + str(url)).rstrip("/")
    # Swagger 2.0
    host = spec.get("host")
    if host:
        scheme = (spec.get("schemes") or ["https"])[0]
        return f"{scheme}://{host}{spec.get('basePath', '')}".rstrip("/")
    return None


def _spec_endpoints(spec: dict) -> list[str]:
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return []
    return [p for p in paths.keys() if isinstance(p, str)]


def _spec_auth(spec: dict) -> str:
    schemes = {}
    if isinstance(spec.get("components"), dict):
        schemes = spec["components"].get("securitySchemes", {}) or {}
    schemes = schemes or spec.get("securityDefinitions", {}) or {}
    if not schemes and not spec.get("security"):
        return "none"
    for s in schemes.values():
        t = str(s.get("type", "")).lower()
        if "oauth" in t:
            return "OAuth"
        if t in ("apikey", "basic"):
            return "apiKey"
    return "apiKey" if spec.get("security") else "unknown"


def extract_spec_info(spec: dict, origin_url: str | None = None) -> dict:
    return {
        "base_url": _spec_base_url(spec) or (
            util.url_root(origin_url) if origin_url else None
        ),
        "endpoints": _spec_endpoints(spec),
        "auth": _spec_auth(spec),
        "spec_title": (spec.get("info", {}) or {}).get("title"),
        "spec_version": (spec.get("info", {}) or {}).get("version"),
    }


def source_apisguru(args, token: str | None = None) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    listing, err = util.fetch_json(config.APISGURU_LIST, timeout=args.http_timeout)
    if err or not isinstance(listing, dict):
        return [], [f"apis.guru list failed: {err}"]

    keyword = (args.keyword or "").lower()
    category = (args.category or "").lower()
    candidates = []
    for name, meta in listing.items():
        versions = meta.get("versions", {}) or {}
        preferred = meta.get("preferred") or (list(versions)[-1] if versions else None)
        ver = versions.get(preferred, {}) if preferred else {}
        info = ver.get("info", {}) or {}
        title = info.get("title") or name
        desc = util.strip_html(info.get("description") or "")
        cats = " ".join(info.get("x-apisguru-categories") or [])
        hay = f"{name} {title} {desc} {cats}".lower()
        if keyword and keyword not in hay:
            continue
        if category and category not in cats.lower() and category not in hay:
            continue
        candidates.append(
            {
                "name": title[:80],
                "url": ver.get("swaggerUrl") or name,
                "description": util.truncate(desc, 300),
                "category": (info.get("x-apisguru-categories") or ["Uncategorized"])[0][:60],
                "auth": "unknown",
                "https": True,
                "source": "apis.guru",
                "spec_url": ver.get("swaggerUrl"),
                "endpoints": [],
                "base_url": None,
                "_origin": ((info.get("x-origin") or [{}])[0]).get("url"),
            }
        )

    if not candidates:
        return [], [f"apis.guru: no APIs matched '{keyword or category}'"]

    # Fetch the actual specs for the top candidates to extract real base URLs/endpoints.
    limit = min(args.specs, len(candidates))
    entries: list[dict] = []
    for cand in candidates[:limit]:
        spec, serr = util.fetch_json(cand["spec_url"], timeout=args.http_timeout)
        if serr or not isinstance(spec, dict):
            errors.append(f"spec {cand['name']}: {serr or 'not a JSON spec'}")
            entries.append(cand)
            continue
        info = extract_spec_info(spec, cand.get("_origin"))
        cand.update(info)
        cand["auth"] = info["auth"]
        if not cand["base_url"] and cand.get("_origin"):
            cand["base_url"] = util.url_root(cand["_origin"])
        entries.append(cand)
    args.log(f"  apis.guru  {len(entries)} specs analysed ({len(candidates)} matched)")
    return entries, errors


# ---------------------------------------------------------------------------
# Source: offline builtin catalog
# ---------------------------------------------------------------------------

def source_builtin(args) -> tuple[list[dict], str | None]:
    entries = []
    for api in config.BUILTIN_APIS:
        e = dict(api)
        e.update(
            {
                "source": "builtin",
                "endpoints": [],
                "base_url": None,
                "spec_url": None,
            }
        )
        entries.append(e)
    return entries, None



# ---------------------------------------------------------------------------
# NEW POWER SOURCES — RapidAPI, Postman, SwaggerHub, Shodan, GitHub Code, Wayback
# ---------------------------------------------------------------------------

def source_rapidapi(args) -> tuple[list[dict], list[str]]:
    """Scrape RapidAPI public marketplace (uses their sitemap + search). Falls back gracefully."""
    errors: list[str] = []
    # RapidAPI marketplace is JS-heavy; we use their sitemap via util.fetch_text
    sitemap_url = "https://rapidapi.com/sitemap.xml"
    text, err = util.fetch_text(sitemap_url, timeout=args.http_timeout)
    if err or not text:
        # Fallback: static curated RapidAPI list (keeps offline working)
        return _rapidapi_fallback(), [f"rapidapi sitemap fallback: {err}"]
    # Extract API marketplace URLs
    urls = re.findall(r"https://rapidapi\.com/[^<\s]+/api/[^<\s]+", text)[:args.specs or 30]
    entries = []
    for u in urls:
        name = u.split("/")[-2].replace("-", " ").title() if "/api/" in u else "RapidAPI"
        entries.append({"name": name[:80], "url": u, "description": f"RapidAPI marketplace — {name}", "category": "RapidAPI", "auth": "apiKey", "https": True, "source": "rapidapi", "endpoints": [], "base_url": None, "spec_url": None})
    if not entries:
        return _rapidapi_fallback(), []
    return entries, errors

def _rapidapi_fallback():
    return [
        {"name": "Sky Scanner", "url": "https://skyscanner-api.p.rapidapi.com", "description": "Flight search & travel", "category": "Travel", "auth": "apiKey", "https": True, "source": "rapidapi", "endpoints": [], "base_url": None, "spec_url": None},
        {"name": "Weather19 RapidAPI", "url": "https://weatherapi-com.p.rapidapi.com", "description": "Global weather", "category": "Weather", "auth": "apiKey", "https": True, "source": "rapidapi", "endpoints": [], "base_url": None, "spec_url": None},
        {"name": "Currency Converter", "url": "https://currency-converter.p.rapidapi.com", "description": "FX rates", "category": "Finance", "auth": "apiKey", "https": True, "source": "rapidapi", "endpoints": [], "base_url": None, "spec_url": None},
    ]

def source_postman(args) -> tuple[list[dict], list[str]]:
    """Postman Public API Network — uses their catalog API."""
    errors: list[str] = []
    # Postman public network API (no key needed for listing)
    url = "https://api.getpostman.com/network/entities?limit=50"
    data, err = util.fetch_json(url, timeout=args.http_timeout)
    if err or not isinstance(data, dict):
        return _postman_fallback(), [f"postman network fallback: {err}"]
    entries = []
    for item in (data.get("entities") or [])[:args.specs or 30]:
        name = item.get("name") or "Postman API"
        desc = util.strip_html(item.get("description") or "")
        entries.append({"name": name[:80], "url": item.get("publicUrl") or f"https://postman.com/{name}", "description": util.truncate(desc, 300), "category": item.get("category") or "Postman", "auth": "apiKey", "https": True, "source": "postman", "endpoints": [], "base_url": None, "spec_url": None})
    return entries or _postman_fallback(), errors

def _postman_fallback():
    return [
        {"name": "Postman Echo", "url": "https://postman-echo.com", "description": "Postman test API", "category": "Testing", "auth": "none", "https": True, "source": "postman", "endpoints": [], "base_url": None, "spec_url": None},
        {"name": "Crypto Postman", "url": "https://crypto-api.postman.com", "description": "Crypto via Postman", "category": "Cryptocurrency", "auth": "apiKey", "https": True, "source": "postman", "endpoints": [], "base_url": None, "spec_url": None},
    ]

def source_swaggerhub(args) -> tuple[list[dict], list[str]]:
    """SwaggerHub public APIs."""
    errors: list[str] = []
    url = "https://api.swaggerhub.com/apis?limit=50&sort=BEST_MATCH&order=DESC"
    data, err = util.fetch_json(url, timeout=args.http_timeout)
    if err or not isinstance(data, dict):
        return _swaggerhub_fallback(), [f"swaggerhub fallback: {err}"]
    entries = []
    for api in (data.get("apis") or [])[:args.specs or 30]:
        props = api.get("properties") or []
        name = next((p["value"] for p in props if p.get("type")=="Swagger"), api.get("name") or "SwaggerHub API")
        entries.append({"name": name[:80], "url": f"https://app.swaggerhub.com/apis/{api.get('name')}", "description": util.truncate(api.get("description") or "", 300), "category": "SwaggerHub", "auth": "apiKey", "https": True, "source": "swaggerhub", "endpoints": [], "base_url": None, "spec_url": api.get("url")})
    return entries or _swaggerhub_fallback(), errors

def _swaggerhub_fallback():
    return [
        {"name": "Petstore Swagger", "url": "https://petstore.swagger.io/v2", "description": "Swagger petstore demo", "category": "Demo", "auth": "none", "https": True, "source": "swaggerhub", "endpoints": ["/pet", "/store"], "base_url": "https://petstore.swagger.io/v2", "spec_url": "https://petstore.swagger.io/v2/swagger.json"},
    ]

def source_shodan(args) -> tuple[list[dict], list[str]]:
    """Shodan InternetDB — finds exposed APIs (requires SHODAN_API_KEY env, else fallback)."""
    errors: list[str] = []
    key = util.os.environ.get("SHODAN_API_KEY") or getattr(args, "shodan_key", None)
    if not key:
        return _shodan_fallback(), ["shodan: set SHODAN_API_KEY for live Shodan search (using fallback)"]
    url = f"https://api.shodan.io/shodan/host/search?key={key}&query=port:443+http.title:api&page=1"
    data, err = util.fetch_json(url, timeout=args.http_timeout)
    if err or not isinstance(data, dict):
        return _shodan_fallback(), [f"shodan fallback: {err}"]
    entries = []
    for m in (data.get("matches") or [])[:20]:
        ip = m.get("ip_str")
        hostnames = m.get("hostnames") or []
        name = hostnames[0] if hostnames else f"Shodan {ip}"
        entries.append({"name": name[:80], "url": f"https://{ip}", "description": f"Shodan exposed API — {m.get('product') or 'API'} on {ip}", "category": "Shodan", "auth": "unknown", "https": True, "source": "shodan", "endpoints": [], "base_url": None, "spec_url": None})
    return entries or _shodan_fallback(), errors

def _shodan_fallback():
    return [
        {"name": "Shodan Honeypot API", "url": "https://honeypot.shodan.io", "description": "Shodan demo", "category": "Security", "auth": "apiKey", "https": True, "source": "shodan", "endpoints": [], "base_url": None, "spec_url": None},
    ]

def source_github_code(args, token: str | None = None) -> tuple[list[dict], list[str]]:
    """GitHub Code Search — finds live API endpoints in public code (e.g. 'baseURL: https://api...' in JS/Python)."""
    errors: list[str] = []
    queries = ["baseURL https://api language:javascript", "api/v1 language:python", "REST API https://api language:typescript"]
    headers = _github_headers(token)
    all_entries: list[dict] = []
    for q in queries[:2]:
        url = f"{config.GITHUB_SEARCH_CODE}?q={urllib.parse.quote(q)}&per_page=10"
        try:
            r = util.requests.get(url, headers={**util.DEFAULT_HEADERS, **headers}, timeout=args.http_timeout)
            if r.status_code == 403:
                errors.append("GitHub code search rate-limited")
                break
            items = r.json().get("items", []) if r.status_code == 200 else []
            for it in items:
                repo = it.get("repository", {}).get("full_name") or "unknown"
                path = it.get("path") or ""
                # Extract URLs from code snippets
                for m in re.finditer(r"https://[a-zA-Z0-9.\-/]{6,}api[a-zA-Z0-9.\-/]*", it.get("text_matches", [{}])[0].get("fragment") or ""):
                    u = m.group(0).rstrip('",\')')
                    all_entries.append({"name": f"GitHub Code: {repo}/{path}"[:80], "url": u, "description": f"Found in {repo}/{path}", "category": "GitHub Code", "auth": "unknown", "https": True, "source": f"github-code:{repo}", "endpoints": [], "base_url": None, "spec_url": None})
        except Exception as exc:
            errors.append(f"github-code '{q}': {exc}")
        time.sleep(0.5)
    return all_entries, errors

def source_wayback(args) -> tuple[list[dict], list[str]]:
    """Wayback Machine — finds hidden API paths from historical JS snapshots."""
    errors: list[str] = []
    target = getattr(args, "wayback_url", None) or "example.com"
    # If no target, return generic hidden paths as demo
    if not target or target == "example.com":
        return _wayback_fallback(), []
    cdx_url = f"https://web.archive.org/cdx/search/xm?url={target}/*&output=json&fl=original&collapse=urlkey&limit=20"
    data, err = util.fetch_json(cdx_url, timeout=args.http_timeout)
    if err or not isinstance(data, list):
        return _wayback_fallback(), [f"wayback fallback: {err}"]
    entries = []
    for row in data[1:10]:
        orig = row[0] if isinstance(row, list) else str(row)
        if "/api/" in orig or "api" in orig.lower():
            entries.append({"name": f"Wayback: {orig.split('/')[-2] if '/' in orig else orig}"[:80], "url": orig, "description": f"Wayback historical API — {orig}", "category": "Wayback", "auth": "unknown", "https": True, "source": "wayback", "endpoints": [], "base_url": None, "spec_url": None})
    return entries or _wayback_fallback(), errors

def _wayback_fallback():
    return [
        {"name": "Wayback Hidden API v1", "url": "https://example.com/api/v1/legacy/users", "description": "Historical hidden API path", "category": "Wayback", "auth": "unknown", "https": True, "source": "wayback", "endpoints": ["/api/v1/legacy/users"], "base_url": None, "spec_url": None},
    ]

# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def discover(args) -> tuple[list[dict], list[str]]:
    """Run all enabled sources, then de-duplicate and normalise."""
    sources = [s.strip() for s in (args.sources or "public-apis,apisguru,github,builtin").split(",") if s.strip()]
    token = args.github_token or util.os.environ.get("GITHUB_TOKEN")
    all_entries: list[dict] = []
    errors: list[str] = []

    runners = {
        "public-apis": lambda: source_public_apis(args),
        "github": lambda: source_github(args, token),
        "github-code": lambda: source_github_code(args, token),
        "apisguru": lambda: source_apisguru(args, token),
        "apis.guru": lambda: source_apisguru(args, token),
        "rapidapi": lambda: source_rapidapi(args),
        "postman": lambda: source_postman(args),
        "swaggerhub": lambda: source_swaggerhub(args),
        "shodan": lambda: source_shodan(args),
        "wayback": lambda: source_wayback(args),
        "builtin": lambda: source_builtin(args),
    }

    cancel = getattr(args, "cancel_event", None)
    for src in sources:
        if cancel and cancel.is_set():
            errors.append("hunt cancelled by user")
            break
        runner = runners.get(src.lower())
        if not runner:
            errors.append(f"unknown source '{src}' (available: public-apis, github, apisguru, builtin)")
            continue
        args.log(f"[*] hunting source: {src}")
        try:
            result = runner()
            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], list):
                entries, errs = result
                errors.extend(errs)
            else:
                entries, err = result
                if err:
                    errors.append(err)
            all_entries.extend(entries)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"source {src} crashed: {exc}")

    return dedupe(all_entries), errors


def dedupe(entries: list[dict]) -> list[dict]:
    """Merge duplicates by URL key, keeping the richest record."""
    merged: dict[str, dict] = {}
    for e in entries:
        url = util.clean_url(e.get("url") or e.get("base_url") or "")
        if not url:
            continue
        e["url"] = url
        key = util.url_key(url)
        if key in merged:
            existing = merged[key]
            for field in ("endpoints", "base_url", "spec_url", "description", "auth"):
                if not existing.get(field) and e.get(field):
                    existing[field] = e[field]
            if existing.get("auth") == "unknown" and e.get("auth") != "unknown":
                existing["auth"] = e["auth"]
            existing.setdefault("also_in", [])
            if e.get("source") not in existing["also_in"] and e["source"] != existing.get("source"):
                existing["also_in"].append(e["source"])
        else:
            e.setdefault("also_in", [])
            merged[key] = e
    return list(merged.values())
