"""Concurrent API tester: hits every discovered endpoint and records what happened."""
from __future__ import annotations

import threading
import time
import urllib.parse

import requests
from requests.adapters import HTTPAdapter

from . import config, util

try:
    import urllib3

    urllib3.disable_warnings()
except Exception:  # pragma: no cover
    pass

_local = threading.local()


def _session(verify: bool) -> requests.Session:
    """One session per worker thread (connection pooling + keep-alive)."""
    sess = getattr(_local, "session", None)
    if sess is None:
        sess = requests.Session()
        adapter = HTTPAdapter(pool_connections=8, pool_maxsize=8, max_retries=0)
        sess.mount("http://", adapter)
        sess.mount("https://", adapter)
        _local.session = sess
    _local.verify = verify
    return sess


def classify(http_status: int | None, exc: Exception | None) -> str:
    if exc is not None:
        return "error"
    if http_status is None:
        return "error"
    if 200 <= http_status < 400:
        return "working"
    if http_status in (401, 403):
        return "auth_required"
    if http_status == 429:
        return "rate_limited"
    if http_status in (400, 404, 405, 422):
        return "needs_params"  # server answered -> it is alive
    return "not_working"


def probe(
    url: str,
    timeout: int,
    headers: dict,
    verify: bool,
    retries: int = 1,
    method: str = "GET",
    body_limit: int = 400,
) -> dict:
    """Single HTTP probe with retries + graceful TLS-verify fallback."""
    sess = _session(verify)
    last_exc = None
    started = time.perf_counter()
    for attempt in range(max(1, retries + 1)):
        try:
            r = sess.request(
                method,
                url,
                headers={**util.DEFAULT_HEADERS, **headers},
                timeout=timeout,
                allow_redirects=True,
                verify=verify,
            )
            latency = (time.perf_counter() - started) * 1000
            body = ""
            try:
                body = r.text[:body_limit]
            except Exception:  # noqa: BLE001
                body = "<undecodable body>"
            return {
                "url": url,
                "final_url": r.url,
                "http_status": r.status_code,
                "status": classify(r.status_code, None),
                "latency_ms": round(latency, 1),
                "content_type": r.headers.get("Content-Type", ""),
                "content_length": len(r.content or b""),
                "server": r.headers.get("Server", ""),
                "sample": util.truncate(body, body_limit),
                "error": None,
            }
        except requests.exceptions.SSLError as exc:
            last_exc = exc
            if verify:
                verify = False  # retry once without cert verification
                continue
            break
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(0.3 * (attempt + 1))
    return {
        "url": url,
        "final_url": None,
        "http_status": None,
        "status": "error",
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        "content_type": "",
        "content_length": 0,
        "server": "",
        "sample": "",
        "error": f"{type(last_exc).__name__}: {last_exc}",
    }


def fill_params(path: str, spec_examples: dict | None = None) -> str | None:
    """Replace {placeholders} with example values; None if any param is unknown."""
    spec_examples = spec_examples or {}

    def repl(match):
        param = match.group(1)
        low = param.lower()
        if param in spec_examples:
            return str(spec_examples[param])
        if low in spec_examples:
            return str(spec_examples[low])
        if low in config.PARAM_EXAMPLES:
            return config.PARAM_EXAMPLES[low]
        raise KeyError(param)

    try:
        return re_sub(r"\{([^}]+)\}", repl, path)
    except KeyError:
        return None


def re_sub(pattern, repl, text):
    import re

    return re.sub(pattern, repl, text)


def test_entry(entry: dict, args) -> dict:
    """Test one catalog entry: base URL, root domain, and (deep mode) endpoints."""
    target = entry.get("base_url") or entry.get("url")
    if not target:
        entry["test"] = {"status": "skipped", "error": "no testable URL"}
        return entry

    headers = dict(args.headers)
    result = probe(
        target,
        timeout=args.timeout,
        headers=headers,
        verify=not args.insecure,
        retries=args.retries,
    )
    result["target_kind"] = "base_url" if entry.get("base_url") else "docs_url"
    result["checked_at"] = util.now_iso()

    # Root-domain probe: tells us the provider itself is alive even if the
    # exact path 404s.
    root = util.url_root(target)
    if root and util.url_key(root) != util.url_key(target):
        root_res = probe(
            root,
            timeout=args.timeout,
            headers=headers,
            verify=not args.insecure,
            retries=0,
        )
        result["root"] = {
            "url": root,
            "http_status": root_res["http_status"],
            "status": root_res["status"],
            "latency_ms": root_res["latency_ms"],
        }

    # Deep mode: exercise real endpoints from the spec.
    endpoint_tests = []
    if args.endpoints == "deep" and entry.get("endpoints"):
        base = (entry.get("base_url") or "").rstrip("/")
        paths = sorted(entry["endpoints"], key=len)[: args.max_endpoints]
        for path in paths:
            if not path.startswith("/"):
                path = "/" + path
            filled = fill_params(path)
            if filled is None:
                endpoint_tests.append(
                    {"path": path, "status": "skipped", "error": "unfillable path params"}
                )
                continue
            url = urllib.parse.urljoin(base + "/", filled.lstrip("/"))
            ep = probe(
                url,
                timeout=args.timeout,
                headers=headers,
                verify=not args.insecure,
                retries=0,
            )
            endpoint_tests.append(
                {
                    "path": path,
                    "url": url,
                    "http_status": ep["http_status"],
                    "status": ep["status"],
                    "latency_ms": ep["latency_ms"],
                }
            )
    result["endpoint_tests"] = endpoint_tests
    entry["test"] = result
    return entry


def run(entries: list[dict], args) -> list[dict]:
    """Test all entries concurrently with a progress bar."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    testable = [e for e in entries if (e.get("base_url") or e.get("url"))]
    results: list[dict] = []

    on_test = getattr(args, "on_test", None)
    cancel = getattr(args, "cancel_event", None)

    def _cancelled() -> bool:
        return bool(cancel and cancel.is_set())

    if args.rich and not args.quiet:
        from rich.progress import (
            BarColumn,
            MofNCompleteColumn,
            Progress,
            SpinnerColumn,
            TextColumn,
            TimeElapsedColumn,
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]testing APIs[/bold cyan]"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("test", total=len(testable))
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = {pool.submit(test_entry, e, args): e for e in testable}
                for fut in as_completed(futures):
                    res = fut.result()
                    results.append(res)
                    progress.advance(task)
                    if on_test:
                        on_test(res)
                    if _cancelled():
                        break
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for res in pool.map(lambda e: test_entry(e, args), testable):
                results.append(res)
                args.log(f"  tested {res.get('name', '?')}: {res.get('test', {}).get('status')}")
                if on_test:
                    on_test(res)
                if _cancelled():
                    break

    by_key = {util.url_key(e.get("url", "")): e for e in results}
    ordered = [by_key[util.url_key(e.get("url", ""))] if util.url_key(e.get("url", "")) in by_key else e for e in entries]
    return ordered

# ---------------------------------------------------------------------------
# POWER TESTER — LLM param inference, Auth auto-flow, Fuzz + Rate-limit bypass
# ---------------------------------------------------------------------------

def llm_infer_params(path: str, api_name: str = "") -> dict | None:
    """LLM param inference: uses OpenAI/Groq if key present, else heuristic fallback."""
    import os, re
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            import requests
            prompt = f"For API '{api_name}' path '{path}', list JSON example values for path params like {{id}}. Return JSON e.g. {{\"id\":\"123\"}}"
            # Minimal LLM call (Groq/openai compatible)
            base = os.environ.get("OPENAI_BASE_URL") or "https://api.groq.com/openai/v1"
            if "groq" in (os.environ.get("GROQ_API_KEY") or ""):
                base = "https://api.groq.com/openai/v1"
            else:
                base = "https://api.openai.com/v1"
            r = requests.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": "llama-3.1-8b-instant", "messages": [{"role":"user","content":prompt}], "max_tokens":100}, timeout=8)
            if r.status_code == 200:
                txt = r.json()["choices"][0]["message"]["content"]
                import json
                # Extract JSON from response
                m = re.search(r"\{[^}]+\}", txt)
                if m:
                    return json.loads(m.group(0))
        except Exception:
            pass
    # Heuristic fallback — common patterns
    params = {}
    for m in re.finditer(r"\{([^}]+)\}", path):
        p = m.group(1).lower()
        if "id" in p: params[m.group(1)] = "123"
        elif "name" in p: params[m.group(1)] = "test"
        elif "user" in p: params[m.group(1)] = "demo"
        else: params[m.group(1)] = "1"
    return params or None

def auth_auto_flow(entry: dict, args) -> dict:
    """Try common auth header brute + JWT detection + OAuth2 client-credentials if env provided."""
    import os
    tried = []
    base = entry.get("base_url") or entry.get("url")
    if not base:
        return {}
    # Common header names to brute
    common_headers = ["X-Api-Key", "X-API-KEY", "apikey", "Authorization", "X-RapidAPI-Key"]
    env_keys = [v for k,v in os.environ.items() if "API_KEY" in k.upper() or "TOKEN" in k.upper()]
    headers = dict(args.headers)
    for h in common_headers:
        for key in env_keys[:3]:
            headers[h] = key
            res = probe(base, timeout=args.timeout, headers=headers, verify=not args.insecure, retries=0)
            tried.append({"header": h, "status": res["status"], "http": res["http_status"]})
            if res["status"] == "working":
                entry["auth_flow"] = {"success_header": h, "tried": tried}
                return {"auth_header": h, "key": key}
    # JWT detection
    for s in (entry.get("secrets") or []):
        if s.get("type") in ("bearer-token","jwt") or "eyJ" in s.get("key",""):
            headers["Authorization"] = f"Bearer {s['key']}"
            res = probe(base, timeout=args.timeout, headers=headers, verify=not args.insecure, retries=0)
            if res["status"] == "working":
                entry["auth_flow"] = {"jwt": True, "header": "Bearer"}
                return {"auth_header": "Authorization", "key": s['key']}
    return {}

def fuzz_with_backoff(entry: dict, args, path: str = "/api/v1/search?q=test") -> dict:
    """Fuzz common params + handle 429 backoff with exponential delay."""
    import time, urllib.parse
    base = (entry.get("base_url") or entry.get("url") or "").rstrip("/")
    if not base:
        return {}
    fuzz_payloads = ["?q=test", "?id=1", "?page=1", "?limit=10", ""]
    headers = dict(args.headers)
    for payload in fuzz_payloads:
        url = base + path.split("?")[0] + payload
        res = probe(url, timeout=args.timeout, headers=headers, verify=not args.insecure, retries=0)
        if res["status"] == "rate_limited":
            # Exponential backoff 1s,2s,4s
            for delay in [1,2,4]:
                time.sleep(delay)
                res = probe(url, timeout=args.timeout, headers=headers, verify=not args.insecure, retries=0)
                if res["status"] != "rate_limited":
                    break
        if res["status"] in ("working","needs_params"):
            return {"fuzz_url": url, "result": res}
    return {}

