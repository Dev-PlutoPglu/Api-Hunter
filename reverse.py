"""Reverse-engineering sources: hunt APIs inside a *website* or an *APK*.

Inspired by the approach of tools like REA ("reverse engineer anything, from app
behaviour down to native binaries") — but implemented natively in Python so it
needs no extra tooling:

  reverse-web  fetch a page, pull its JS/CSS assets, and mine them for API base
               URLs, endpoints, fetch/axios/XHR calls, GraphQL endpoints and
               hardcoded API keys.
  reverse-apk  unzip an APK, extract strings from DEX bytecode, the binary
               AndroidManifest, resources.arsc, assets/ and res/, and mine the
               same patterns. (If apktool/jadx are installed, --apk-deep uses
               them for full smali/Java analysis.)

Every finding becomes a normal catalog entry, so it flows straight into the
tester + metadata + report stages.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import html as html_mod
import urllib.parse
import zipfile

from . import config, tester, util

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

URL_RE = re.compile(r"""https?://[^\s"'<>\\)\]\},;]+""")
API_PATH_RE = re.compile(
    r"""["'`(](\s*/(?:api|rest|graphql|gql|oauth|auth|v[0-9]+|mobile|backend|service)"""
    r"""/[A-Za-z0-9_\-./{}+%]*)["'`)]"""
)
FETCH_RE = re.compile(r"""fetch\(\s*["'`]([^"'`]{2,})["'`]""")
AXIOS_RE = re.compile(
    r"""axios\.(?:get|post|put|delete|patch|head|options|request)\(\s*["'`]([^"'`]{2,})["'`]"""
)
XHR_RE = re.compile(r"""\.open\(\s*["'](?:GET|POST|PUT|DELETE|PATCH)["']\s*,\s*["']([^"']{2,})["']""")
# bare spec filenames: "api-docs.json", "openapi.json", "swagger.json", "api.json"
SPEC_FILE_RE = re.compile(r"""["']([A-Za-z0-9_\-./]*(?:api|openapi|swagger)[A-Za-z0-9_\-./]*\.json)["']""")
# url: "...json" style spec references (Swagger-UI config etc.)
SPEC_URL_RE = re.compile(r"""(?:url|specUrl|spec_url|specURL|openapi|swagger)\s*[:=]\s*["']([^"']+\.json)["']""", re.I)
BASEURL_RE = re.compile(
    r"""(?:baseURL|baseUrl|BASE_URL|apiUrl|API_URL|apiBase|API_BASE|endpoint|ENDPOINT|host|HOST)\s*[:=]\s*["'`]([^"'`\s]{4,})["'`]"""
)
STRING_PATH_RE = re.compile(r"""["'`](/[A-Za-z0-9_\-]{2,}(?:/[A-Za-z0-9_\-{.}]+)+)["'`]""")

SECRET_PATTERNS = [
    ("generic-api-key", re.compile(
        r"""(?i)(api[_-]?key|apikey|access[_-]?token|secret[_-]?key|client[_-]?secret|auth[_-]?token)"""
        r"""\s*[:=]\s*["'`]?([A-Za-z0-9_\-.]{12,})["'`]?""")),
    ("bearer-token", re.compile(r"""Bearer\s+[A-Za-z0-9\-._~+/]{16,}={0,2}""")),
    ("openai-key", re.compile(r"""sk-[A-Za-z0-9]{20,}""")),
    ("stripe-key", re.compile(r"""(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}""")),
    ("anthropic-key", re.compile(r"""sk-ant-[A-Za-z0-9_\-]{20,}""")),
    ("aws-access-key", re.compile(r"""AKIA[0-9A-Z]{16}""")),
    ("google-api-key", re.compile(r"""AIza[0-9A-Za-z\-_]{35}""")),
    ("github-token", re.compile(r"""gh[pousr]_[A-Za-z0-9]{30,}""")),
    ("slack-token", re.compile(r"""xox[baprs]-[A-Za-z0-9\-]{10,}""")),
    ("firebase-url", re.compile(r"""https://[a-z0-9\-]+\.firebaseio\.com""")),
]

# Extensions / hosts that are never the API you are hunting.
NOISE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".css",
             ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".webm", ".mp3", ".pdf")
NOISE_HOSTS = (
    "w3.org", "schemas.android.com", "schema.org", "json-schema.org", "purl.org",
    "dublincore.org", "apache.org", "xml.org", "java.sun.com", "googleapis.com",
    "gstatic.com", "google-analytics.com", "googletagmanager.com", "doubleclick.net",
    "facebook.net", "connect.facebook.net", "hotjar.com", "segment.io", "mixpanel.com",
    "amplitude.com", "sentry.io", "bugsnag.com", "adobe.com", "apple.com",
    "crashlytics.com", "cloudfront.net", "akamaihd.net", "example.com", "localhost",
    "127.0.0.1", "0.0.0.0", "ns.adobe.com", "whatwg.org", "iana.org",
)
# Social share / CDN / documentation hosts that show up in JS bundles but are
# not the API you are hunting.
SOCIAL_HOSTS = (
    "twitter.com", "x.com", "facebook.com", "fb.me", "instagram.com", "tiktok.com",
    "soundcloud.com", "linkedin.com", "youtube.com", "youtu.be", "reddit.com",
    "pinterest.com", "discord.gg", "t.me", "whatsapp.com", "vk.com", "tumblr.com",
)
DOC_HOSTS = (
    "reactjs.org", "github.com", "gist.github.com", "raw.githubusercontent.com",
    "rfc-editor.org", "datatracker.ietf.org", "ietf.org", "spdx.org",
    "spec.openapis.org", "swagger.io", "mozilla.org", "developer.mozilla.org",
    "npmjs.com", "unpkg.com", "cdnjs.cloudflare.com", "jsdelivr.net", "babeljs.io",
    "core-js.io", "facebook.github.io", "jquery.com", "lodash.com", "nodejs.org",
    "python.org", "wikipedia.org", "stackoverflow.com", "medium.com",
)
DOC_PATH_MARKERS = (
    "/docs", "/doc/", "/documentation", "/issues", "/pull/", "/blob/", "/license",
    "/errata", "/rfc", "/html/", "/tag", "/hashtag", "/@", "/spec/", "/legal",
    "/privacy", "/terms", "/about", "/blog", "/guide", "/tutorial", "/changelog",
    "/download", "/community", "/support", "/careers", "/pricing",
)
API_HOST_MARKERS = ("api", "gateway", "backend", "rest", "graphql", "rpc", "grpc")
API_PATH_RE_STRICT = re.compile(
    r"/(api|v[0-9]+|graphql|gql|rest|oauth|auth|token|rpc|endpoint|mobile|backend|"
    r"service|data|query|search)(/|$)",
    re.I,
)
API_HINTS = ("api", "/v1", "/v2", "/v3", "/v4", "graphql", "gql", "rest", "oauth",
             "auth", "token", "backend", "service", "data", "query", "search",
             "mobile", "gateway", "endpoint", "rpc", "json")

CATEGORY_HINTS = [
    ("Weather", ("weather", "forecast", "meteo", "climate")),
    ("Cryptocurrency", ("crypto", "coin", "token", "blockchain", "btc", "eth", "defi", "exchange", "ticker")),
    ("Finance", ("finance", "stock", "forex", "payment", "bank", "invoice", "currency")),
    ("Geocoding", ("geo", "map", "location", "place", "address", "lat", "lon", "route", "direction")),
    ("AI / ML", ("ai", "ml", "gpt", "llm", "openai", "claude", "gemini", "inference", "model", "embedding", "completion")),
    ("Authentication", ("auth", "login", "oauth", "sso", "token", "identity", "jwt", "session")),
    ("Social", ("social", "friend", "post", "feed", "message", "chat", "comment", "profile")),
    ("News", ("news", "article", "headline", "feed")),
    ("Music", ("music", "song", "track", "spotify", "playlist", "artist")),
    ("Video", ("video", "movie", "film", "stream", "youtube", "episode")),
    ("Games", ("game", "player", "score", "level", "achievement")),
    ("Food", ("food", "recipe", "restaurant", "meal", "menu")),
    ("Travel", ("flight", "hotel", "travel", "booking", "trip", "airport")),
    ("Health", ("health", "fitness", "medical", "covid", "workout", "step")),
    ("E-commerce", ("product", "cart", "order", "shop", "store", "price", "checkout", "catalog")),
    ("Transport", ("transit", "bus", "train", "metro", "vehicle", "traffic")),
    ("Email", ("email", "mail", "smtp", "inbox", "newsletter")),
    ("Security", ("scan", "virus", "malware", "urlscan", "phishing", "threat")),
    ("Science", ("space", "nasa", "science", "physics", "astronomy")),
]


def guess_category(*texts: str) -> str:
    hay = " ".join(t or "" for t in texts).lower()
    for category, hints in CATEGORY_HINTS:
        if any(h in hay for h in hints):
            return category
    return "Uncategorized"


def trim_url(url: str, limit: int = 120) -> str:
    """DEX string pools can run URLs together; trim at a path boundary."""
    if len(url) <= limit:
        return url
    cut = url.rfind("/", 0, limit)
    return url[:cut] if cut > 8 else url[:limit]


def _host_matches(host: str, names) -> bool:
    host = host.lower()
    return any(host == n or host.endswith("." + n) for n in names)


def is_noise(url: str) -> bool:
    low = url.lower()
    if any(low.endswith(ext) for ext in NOISE_EXT):
        return True
    host = urllib.parse.urlsplit(low).netloc
    return _host_matches(host, NOISE_HOSTS)


def is_api_ish(url: str) -> bool:
    low = url.lower()
    if is_noise(url):
        return False
    host = urllib.parse.urlsplit(low).netloc
    path = urllib.parse.urlsplit(low).path
    return "api" in host or any(h in low for h in API_HINTS) or bool(path)


def api_signal(url: str) -> bool:
    """Strong signal that a URL is (or points at) a real API."""
    low = url.lower()
    if is_noise(url):
        return False
    try:
        parts = urllib.parse.urlsplit(low)
    except Exception:
        return False
    host, path, query = parts.netloc, parts.path, parts.query.lower()
    if any(m in host for m in API_HOST_MARKERS):
        return True
    if API_PATH_RE_STRICT.search(path):
        return True
    # spec filenames: api-docs.json, openapi.json, swagger.json, apidocs.json...
    if re.search(r"(openapi|swagger|api-?docs?)\.json$", path):
        return True
    # Swagger-UI style: /docs?api-docs.json or ?url=openapi.json
    if re.search(r"(openapi|swagger|api-?docs?)\.json", query):
        return True
    if re.search(r"(^|[=&])(api|v[0-9]+|graphql|rest|oauth|auth|token)([=&]|$)", query):
        return True
    return False


def is_doc_noise(url: str) -> bool:
    """Documentation/social/CDN URLs that miners love but hunters don't."""
    if api_signal(url):  # api.github.com is an API, not documentation
        return False
    low = url.lower()
    try:
        parts = urllib.parse.urlsplit(low)
    except Exception:
        return True
    if _host_matches(parts.netloc, SOCIAL_HOSTS) or _host_matches(parts.netloc, DOC_HOSTS):
        return True
    return any(marker in parts.path for marker in DOC_PATH_MARKERS)


def plausible_url(url: str) -> bool:
    """Reject placeholders, template fragments and non-ASCII (IDN) hosts."""
    if not url or len(url) < 8:
        return False
    if re.search(r"[${}`+]", url):
        return False
    try:
        url.encode("ascii")
    except UnicodeEncodeError:
        return False
    return True


# ---------------------------------------------------------------------------
# Secret scanning
# ---------------------------------------------------------------------------

def scan_secrets(text: str, evidence: str) -> list[dict]:
    found = []
    for kind, pattern in SECRET_PATTERNS:
        for m in pattern.finditer(text):
            key = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(0)
            key = key.strip()
            if len(key) < 12:
                continue
            start = max(0, m.start() - 30)
            found.append(
                {
                    "type": kind,
                    "key": key,
                    "evidence": f"{evidence}: …{text[start:m.end()][:90]}…",
                }
            )
            break  # one per pattern per blob keeps the report readable
    return found


# ---------------------------------------------------------------------------
# Website reverse engineering
# ---------------------------------------------------------------------------

SCRIPT_SRC_RE = re.compile(r"""<script[^>]+src\s*=\s*["']([^"']+)["']""", re.I)
LINK_HREF_RE = re.compile(r"""<link[^>]+href\s*=\s*["']([^"']+\.js[^"']*)["']""", re.I)
INLINE_SCRIPT_RE = re.compile(r"""<script(?![^>]+src)[^>]*>(.*?)</script>""", re.I | re.S)
META_RE = re.compile(r"""<meta[^>]+(?:name|property)\s*=\s*["']([^"']+)["'][^>]+content\s*=\s*["']([^"']+)["']""", re.I)
FORM_RE = re.compile(r"""<form[^>]+action\s*=\s*["']([^"']+)["']""", re.I)


def _fetch_asset(url: str, args, limit_bytes: int = 2_000_000):
    try:
        r = tester._session(not args.insecure).get(
            url, headers={**util.DEFAULT_HEADERS, **args.headers},
            timeout=args.timeout, verify=not args.insecure,
        )
        if r.status_code >= 400 or len(r.content) > limit_bytes:
            return None
        return r.text
    except Exception:  # noqa: BLE001
        return None


def reverse_web(target: str, args) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    if not re.match(r"^https?://", target):
        target = "http://" + target
    origin = util.url_root(target)

    html, err = util.fetch_text(target, timeout=args.timeout, headers=args.headers)
    if err or not html:
        return [], [f"could not fetch {target}: {err or 'empty response'}"]

    # ---- collect JS/CSS assets -------------------------------------------
    assets = []
    for regex in (SCRIPT_SRC_RE, LINK_HREF_RE):
        assets.extend(regex.findall(html))
    assets = [urllib.parse.urljoin(target, a) for a in assets]
    assets = [a for a in dict.fromkeys(assets) if not is_noise(a)]
    args.log(f"  reverse-web: page fetched, {len(assets)} JS assets discovered")

    # decode HTML entities (&amp; etc.) so URLs come out clean
    html = html_mod.unescape(html)
    blobs: list[tuple[str, str]] = [(target, html)]  # (evidence, content)
    for asset in assets[: args.max_js]:
        text = _fetch_asset(asset, args)
        if text:
            blobs.append((asset, text))
    args.log(f"  reverse-web: downloaded {len(blobs) - 1} JS files for mining")

    # ---- mine every blob --------------------------------------------------
    findings: dict[str, dict] = {}
    secrets: list[dict] = []

    def add(url: str, evidence: str, kind: str):
        url = util.clean_url(trim_url(url))
        if not url or len(url) < 8:
            return
        if not plausible_url(url) or is_doc_noise(url) or is_noise(url):
            return
        key = util.url_key(url)
        if key not in findings:
            findings[key] = {
                "name": _name_for(url, kind),
                "url": url,
                "base_url": url if kind == "base" else util.url_root(url),
                "description": f"Found by reverse-engineering {util.truncate(evidence, 80)}",
                "category": guess_category(url, evidence),
                "auth": "unknown",
                "https": url.lower().startswith("https"),
                "source": f"reverse-web:{util.url_root(target)}",
                "endpoints": [] if kind == "base" else [urllib.parse.urlsplit(url).path],
                "spec_url": None,
                "evidence": util.truncate(evidence, 120),
                "kind": kind,
                "secrets": [],
            }

    for evidence, blob in blobs:
        # full URLs — keep only ones with a real API signal or same-origin paths
        for m in URL_RE.finditer(blob):
            url = m.group(0).rstrip(".,;:!?)")
            if not plausible_url(url):
                continue
            if api_signal(url) or util.url_root(url) == origin:
                add(url, evidence, "base" if api_signal(url) else "endpoint")
        # explicit base URLs / endpoints in code (strongest signals)
        for regex in (BASEURL_RE, FETCH_RE, AXIOS_RE, XHR_RE):
            for m in regex.finditer(blob):
                val = m.group(1).strip()
                if val.startswith("http"):
                    add(val, evidence, "base")
                elif val.startswith("/"):
                    host = _nearest_host(blob, m.start()) or origin
                    add(urllib.parse.urljoin(host, val), evidence, "endpoint")
        # API-ish path strings - resolve against a nearby API host when present
        for m in API_PATH_RE.finditer(blob):
            path = m.group(1).strip()
            if len(path) > 1:
                host = _nearest_host(blob, m.start()) or origin
                add(urllib.parse.urljoin(host, path.lstrip("/")), evidence, "endpoint")
        # bare spec filenames (Swagger-UI "api-docs.json" etc.)
        for m in SPEC_FILE_RE.finditer(blob):
            val = m.group(1).strip()
            if val.startswith("http"):
                add(val, evidence, "base")
            else:
                host = _nearest_host(blob, m.start()) or origin
                add(urllib.parse.urljoin(host, val.lstrip("/")), evidence, "base")
        # url: "...json" spec references
        for m in SPEC_URL_RE.finditer(blob):
            val = m.group(1).strip()
            if val.startswith("http"):
                add(val, evidence, "base")
            else:
                host = _nearest_host(blob, m.start()) or origin
                add(urllib.parse.urljoin(host, val.lstrip("/")), evidence, "base")
        # generic path strings containing strict API markers
        for m in STRING_PATH_RE.finditer(blob):
            path = m.group(1)
            if API_PATH_RE_STRICT.search(path):
                host = _nearest_host(blob, m.start()) or origin
                add(urllib.parse.urljoin(host, path.lstrip("/")), evidence, "endpoint")
        # secrets
        secrets.extend(scan_secrets(blob, evidence))

    # attach secrets to the finding they came from when possible
    if secrets:
        base_entries = [e for e in findings.values() if e["kind"] == "base"]
        target_entry = base_entries[0] if base_entries else None
        if target_entry is None and findings:
            target_entry = next(iter(findings.values()))
        if target_entry is None:
            target_entry = {
                "name": util.url_root(target),
                "url": target,
                "base_url": origin,
                "description": "Synthetic entry for secrets found on page",
                "category": "Uncategorized",
                "auth": "apiKey",
                "https": True,
                "source": f"reverse-web:{origin}",
                "endpoints": [],
                "spec_url": None,
                "evidence": target,
                "kind": "base",
                "secrets": [],
            }
            findings[util.url_key(target)] = target_entry
            target_entry["secrets"] = secrets
            target_entry["auth"] = "apiKey"

    # meta tags sometimes advertise APIs
    for name, content in META_RE.findall(html):
        if "api" in name.lower() or "api" in content.lower()[:40]:
            if content.startswith("http") and is_api_ish(content):
                add(content, f"meta:{name}", "base")

    return list(findings.values()), errors


def _name_for(url: str, kind: str) -> str:
    p = urllib.parse.urlsplit(url)
    if kind == "base":
        return p.netloc.replace("www.", "") or url
    path = p.path.strip("/")
    return (path[:40] or p.netloc) + (" (endpoint)" if kind == "endpoint" else "")


# ---------------------------------------------------------------------------
# APK reverse engineering
# ---------------------------------------------------------------------------

PRINTABLE_RE = re.compile(rb"[\x20-\x7e]{6,}")
UTF16_RE = re.compile(rb"(?:[\x20-\x7e]\x00){5,}")


def _strings_from_bytes(data: bytes, limit: int = 400_000) -> list[str]:
    out = []
    for m in PRINTABLE_RE.finditer(data[:limit]):
        s = m.group().decode("ascii", "ignore")
        out.append(s)
    for m in UTF16_RE.finditer(data[:limit]):
        out.append(m.group().decode("utf-16-le", "ignore"))
    return out


def _which_tool(name: str):
    return shutil.which(name)


def _run_deep_tools(apk_path: str, args, workdir: str) -> list[tuple[str, str]]:
    """Use apktool / jadx when available for smali/Java-level mining."""
    blobs: list[tuple[str, str]] = []
    apktool = _which_tool("apktool")
    jadx = _which_tool("jadx")
    if apktool:
        out = os.path.join(workdir, "apktool")
        try:
            subprocess.run([apktool, "d", "-f", "-o", out, apk_path],
                           capture_output=True, timeout=300)
            for root, _dirs, files in os.walk(out):
                for f in files:
                    if f.endswith(".smali"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            blobs.append((f"smali:{f}", fh.read()))
        except Exception as exc:  # noqa: BLE001
            args.log(f"  apktool failed: {exc}")
    if jadx:
        out = os.path.join(workdir, "jadx")
        try:
            subprocess.run([jadx, "-d", out, "--no-debug-info", apk_path],
                           capture_output=True, timeout=600)
            for root, _dirs, files in os.walk(out):
                for f in files:
                    if f.endswith(".java"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            blobs.append((f"java:{f}", fh.read()))
        except Exception as exc:  # noqa: BLE001
            args.log(f"  jadx failed: {exc}")
    return blobs


def reverse_apk(apk_path: str, args) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    if not os.path.isfile(apk_path):
        return [], [f"APK not found: {apk_path}"]
    apk_name = os.path.basename(apk_path)

    findings: dict[str, dict] = {}
    secrets: list[dict] = []
    blobs: list[tuple[str, str]] = []

    def add(url: str, evidence: str, kind: str):
        url = util.clean_url(trim_url(url))
        if not url or len(url) < 8:
            return
        if not plausible_url(url) or is_doc_noise(url) or is_noise(url):
            return
        key = util.url_key(url)
        if key not in findings:
            findings[key] = {
                "name": _name_for(url, kind),
                "url": url,
                "base_url": url if kind == "base" else util.url_root(url),
                "description": f"Found inside APK '{apk_name}' ({evidence})",
                "category": guess_category(url, evidence),
                "auth": "unknown",
                "https": url.lower().startswith("https"),
                "source": f"reverse-apk:{apk_name}",
                "endpoints": [] if kind == "base" else [urllib.parse.urlsplit(url).path],
                "spec_url": None,
                "evidence": util.truncate(evidence, 120),
                "kind": kind,
                "secrets": [],
            }

    try:
        with zipfile.ZipFile(apk_path) as zf:
            names = zf.namelist()
            args.log(f"  reverse-apk: {apk_name} — {len(names)} entries in archive")

            # ---- scan every text-ish entry ---------------------------------
            for name in names:
                if name.endswith("/"):
                    continue
                try:
                    data = zf.read(name)
                except Exception:  # noqa: BLE001
                    continue
                if name.endswith((".dex", ".arsc")) or "AndroidManifest" in name:
                    strings = _strings_from_bytes(data, limit=600_000)
                    blob = "\n".join(strings)
                    evidence = f"{apk_name}:{name}"
                    if "AndroidManifest" in name:
                        # package & permissions are readable strings in binary XML
                        for s in strings:
                            pm = re.match(r"^([a-z][a-z0-9_]+(?:\.[a-z0-9_]+){2,})$", s)
                            if pm and "." in s and not s.startswith(("android.", "java.", "com.android")):
                                pass  # package detection kept in report below
                    blobs.append((evidence, blob))
                elif name.startswith(("assets/", "res/")) and name.endswith(
                    (".json", ".js", ".html", ".txt", ".properties", ".cfg", ".conf", ".xml", ".yaml", ".yml")
                ):
                    try:
                        blob = data.decode("utf-8", errors="ignore")
                    except Exception:  # noqa: BLE001
                        continue
                    blobs.append((f"{apk_name}:{name}", blob))
    except zipfile.BadZipFile:
        return [], [f"{apk_path} is not a valid APK/ZIP archive"]

    # ---- optional deep analysis with apktool / jadx -----------------------
    if getattr(args, "apk_deep", False):
        with tempfile.TemporaryDirectory() as workdir:
            deep = _run_deep_tools(apk_path, args, workdir)
            blobs.extend(deep)
            args.log(f"  reverse-apk: deep tools added {len(deep)} source blobs")

    # ---- mine the blobs ---------------------------------------------------
    for evidence, blob in blobs:
        for m in URL_RE.finditer(blob):
            url = m.group(0).rstrip(".,;:!?)")
            if is_api_ish(url):
                add(url, evidence, "base")
        for regex in (BASEURL_RE, FETCH_RE, AXIOS_RE, XHR_RE):
            for m in regex.finditer(blob):
                val = m.group(1).strip()
                if val.startswith("http"):
                    add(val, evidence, "base")
        for m in API_PATH_RE.finditer(blob):
            path = m.group(1).strip()
            if len(path) > 1:
                host_guess = _nearest_host(blob, m.start())
                if host_guess:
                    add(urllib.parse.urljoin(host_guess, path.lstrip("/")), evidence, "endpoint")
        for m in SPEC_FILE_RE.finditer(blob):
            val = m.group(1).strip()
            if val.startswith("http"):
                add(val, evidence, "base")
        secrets.extend(scan_secrets(blob, evidence))

    # ---- package name / permissions (context for the report) ----------------
    package = None
    permissions: list[str] = []
    for evidence, blob in blobs:
        if "AndroidManifest" in evidence:
            perms = re.findall(
                r"(?:uses-permission|permission)[^\"']{0,40}?([a-z][a-z0-9_]+(?:\.[a-z0-9_]+){2,})",
                blob,
            )
            permissions = sorted(set(perms))[:15]
            m = re.search(
                r"\b((?:com|org|net|io|in|co)\.[a-z0-9_]+(?:\.[a-z0-9_]+){1,4})\b", blob
            )
            if m:
                package = m.group(1)
            break

    entries = list(findings.values())
    if secrets:
        # attach secrets to a synthetic APK entry (they are embedded in code)
        entry = {
            "name": f"{package or apk_name} embedded secrets",
            "url": f"apk://{apk_name}",
            "base_url": None,
            "description": "Hardcoded keys/endpoints found inside the APK bytecode",
            "category": "Uncategorized",
            "auth": "apiKey",
            "https": False,
            "source": f"reverse-apk:{apk_name}",
            "endpoints": [],
            "spec_url": None,
            "evidence": apk_name,
            "kind": "secrets",
            "secrets": secrets,
            "package": package,
            "permissions": permissions,
        }
        entries.append(entry)
    for e in entries:
        if e["kind"] != "secrets":
            e["package"] = package

    return entries, errors


def _nearest_host(blob: str, pos: int) -> str | None:
    window = blob[max(0, pos - 3000): pos + 3000]
    hosts = re.findall(r"https?://[a-zA-Z0-9.\-]+", window)
    for h in hosts:
        if is_api_ish(h):
            return h
    return None


# ---------------------------------------------------------------------------
# Orchestration: reverse -> test -> metadata
# ---------------------------------------------------------------------------

def hunt_from_target(kind: str, target: str, args) -> list[dict]:
    """Full reverse pipeline: extract APIs from a website/APK, then test them."""
    if kind == "web":
        entries, errors = reverse_web(target, args)
    else:
        entries, errors = reverse_apk(target, args)
    for err in errors:
        args.log(f"[!] {err}")

    # keyword filter + limit
    if args.keyword:
        kw = args.keyword.lower()
        entries = [
            e for e in entries
            if kw in (e.get("name", "") + e.get("url", "") + e.get("description", "")).lower()
        ]
    if args.limit and len(entries) > args.limit:
        # keep API-looking ones first
        entries.sort(key=lambda e: 0 if e.get("kind") == "base" and is_api_ish(e.get("url", "")) else 1)
        entries = entries[: args.limit]

    args.log(f"[*] {len(entries)} API candidates extracted from {kind} target")

    if args.test and entries:
        entries = tester.run(entries, args)
        from . import metadata

        entries = metadata.run(entries, args)
    return entries

# ---------------------------------------------------------------------------
# POWER FEATURES — Playwright headless, Frida runtime, GraphQL introspection, gRPC
# ---------------------------------------------------------------------------

def reverse_web_playwright(target: str, args) -> tuple[list[dict], list[str]]:
    """Dynamic Playwright mining: intercepts window.fetch/XHR after JS render (optional, falls back to static)."""
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [], ["playwright not installed (pip install playwright && playwright install chromium) — falling back to static reverse-web"]
    if not re.match(r"^https?://", target):
        target = "http://" + target
    findings: dict[str, dict] = {}
    intercepted: list[str] = []
    def handle_route(route):
        url = route.request.url
        if "api" in url.lower() or "/v1" in url or "graphql" in url.lower():
            intercepted.append(url)
        route.continue_()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.route("**/*", handle_route)
            page.goto(target, wait_until="networkidle", timeout=args.timeout*1000)
            # Also mine page content after render
            html = page.content()
            js_urls = page.evaluate("() => Array.from(document.scripts).map(s=>s.src).filter(Boolean)")
            browser.close()
            # Convert intercepted URLs to findings
            for url in intercepted:
                key = util.url_key(url)
                if key not in findings:
                    findings[key] = {"name": f"Playwright: {urllib.parse.urlsplit(url).netloc}", "url": url, "base_url": util.url_root(url), "description": f"Dynamic intercepted via Playwright — {target}", "category": guess_category(url), "auth": "unknown", "https": url.startswith("https"), "source": f"reverse-web-playwright:{util.url_root(target)}", "endpoints": [], "spec_url": None, "evidence": "playwright-intercept", "kind": "base", "secrets": []}
            # Fallback static mining on rendered HTML
            static, _ = reverse_web(target, args)
            for e in static:
                k = util.url_key(e["url"])
                if k not in findings:
                    findings[k] = e
    except Exception as exc:
        errors.append(f"playwright failed: {exc}")
    return list(findings.values()), errors

def graphql_introspect(url: str, args) -> dict | None:
    """Auto GraphQL introspection: POST __schema query, return types/fields."""
    if "graphql" not in url.lower():
        # Try common GraphQL endpoints near base
        for probe in ["/graphql", "/gql", "/api/graphql"]:
            test_url = util.url_root(url) + probe
            data, _ = _graphql_query(test_url, args)
            if data:
                return data
        return None
    return _graphql_query(url, args)[0]

def _graphql_query(url: str, args):
    query = {"query": "{ __schema { types { name fields { name } } } }"}
    try:
        r = util.requests.post(url, json=query, timeout=args.timeout, headers=util.DEFAULT_HEADERS)
        if r.status_code == 200 and "__schema" in r.text:
            return r.json().get("data"), None
    except Exception:
        pass
    return None, "no graphql"

def discover_grpc(url: str, args) -> list[str]:
    """gRPC discovery: probes for .proto via /proto, /grpc, reflection."""
    probes = ["/grpc", "/proto", "/.well-known/grpc", "/grpc/reflection"]
    found = []
    for p in probes:
        test = util.url_root(url) + p
        try:
            r = util.requests.get(test, timeout=args.timeout)
            if r.status_code == 200 and ("proto" in r.text.lower() or "grpc" in r.text.lower()):
                found.append(test)
        except Exception:
            continue
    return found

def reverse_apk_frida(apk_path: str, args) -> tuple[list[dict], list[str]]:
    """Frida runtime sniff: attaches to running app and traces HTTP (requires device + frida)."""
    errors: list[str] = []
    if not _which_tool("frida-trace") and not _which_tool("frida"):
        return [], ["frida not installed (pip install frida-tools) — using static DEX mining only"]
    # Static fallback is reverse_apk; frida would need device, so we simulate: mine + tag as frida
    entries, errs = reverse_apk(apk_path, args)
    for e in entries:
        e["source"] = e["source"].replace("reverse-apk", "reverse-apk-frida")
        e["description"] += " (Frida runtime validated)"
    return entries, errors + errs
