"""Metadata analysis + metadata-API hunting.

Two jobs:
  1. Extract rich metadata from each tested API (server headers, rate limits,
     JSON shape/keys, sample payload).
  2. Hunt *metadata APIs*: probe common descriptor paths (/openapi.json,
     /swagger.json, /api-docs, /.well-known/openid-configuration, ...) on every
     reachable API, and if a descriptor is found, pull its base URL, endpoints
     and auth scheme — then optionally test those endpoints too.
"""
from __future__ import annotations

import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import config, tester, util

SPEC_MARKERS = ("openapi", "swagger", "paths")
OPENID_MARKERS = ("issuer", "jwks_uri", "authorization_endpoint")

RATELIMIT_HEADERS = (
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset",
    "X-Rate-Limit-Limit",
    "X-Rate-Limit-Remaining",
    "RateLimit-Limit",
    "RateLimit-Remaining",
    "RateLimit-Reset",
    "Retry-After",
    "X-Api-Quota",
)


def _looks_like_spec(payload) -> str | None:
    if not isinstance(payload, dict):
        return None
    if "openapi" in payload and "paths" in payload:
        return "openapi3"
    if "swagger" in payload and ("paths" in payload or "basePath" in payload):
        return "swagger2"
    return None


def _looks_like_openid(payload) -> bool:
    return isinstance(payload, dict) and any(m in payload for m in OPENID_MARKERS)


def analyze_entry(entry: dict, args) -> dict:
    """Metadata about the API's own response (from the test stage)."""
    test = entry.get("test") or {}
    meta: dict = {"analyzed_at": util.now_iso()}

    # Header-derived metadata comes from a fresh lightweight probe when needed.
    resp = probe(test.get("final_url") or test.get("url") or entry.get("url"), args)
    if resp:
        headers = resp.get("headers", {})
        meta["server"] = headers.get("Server", "")
        meta["powered_by"] = headers.get("X-Powered-By", "")
        meta["ratelimit"] = {h: headers[h] for h in RATELIMIT_HEADERS if h in headers}
        meta["content_type"] = resp.get("content_type", "")
        payload = resp.get("json")
        if payload is not None:
            meta["is_metadata_api"] = _looks_like_spec(payload) is not None or _looks_like_openid(payload)
            if isinstance(payload, dict):
                meta["json"] = {
                    "type": "object",
                    "keys": list(payload.keys())[:15],
                    "key_count": len(payload),
                }
            elif isinstance(payload, list):
                meta["json"] = {
                    "type": "array",
                    "items": len(payload),
                    "sample_keys": list(payload[0].keys())[:10]
                    if payload and isinstance(payload[0], dict)
                    else [],
                }
    if "is_metadata_api" not in meta:
        meta["is_metadata_api"] = False
    return meta


def probe(url: str, args) -> dict | None:
    """GET a URL once and return status/headers/JSON (or None on failure)."""
    try:
        r = tester._session(not args.insecure).get(
            url,
            headers={**util.DEFAULT_HEADERS, **args.headers},
            timeout=args.timeout,
            verify=not args.insecure,
        )
        payload = None
        ctype = r.headers.get("Content-Type", "")
        if "json" in ctype or r.text[:1] in ("{", "["):
            try:
                payload = r.json()
            except Exception:  # noqa: BLE001
                payload = None
        return {
            "http_status": r.status_code,
            "headers": dict(r.headers),
            "content_type": ctype,
            "json": payload,
            "text": r.text[:2000],
        }
    except Exception:  # noqa: BLE001
        return None


def _fetch_spec(url: str, args) -> dict | None:
    payload, err = util.fetch_json(url, timeout=args.timeout, headers=args.headers)
    return payload if isinstance(payload, dict) else None


def _spec_details(spec: dict, descriptor_url: str | None = None) -> dict:
    import urllib.parse

    info = spec.get("info", {}) or {}
    kind = "openapi3" if "openapi" in spec else "swagger2"
    servers = spec.get("servers") or []
    base_url = servers[0].get("url") if servers and isinstance(servers[0], dict) else None
    # relative server URLs ("/v1") must be resolved against the descriptor host
    if base_url and not str(base_url).startswith("http") and descriptor_url:
        root = urllib.parse.urlsplit(descriptor_url)
        root = f"{root.scheme}://{root.netloc}"
        base_url = urllib.parse.urljoin(root + "/", str(base_url).lstrip("/"))
    if not base_url and spec.get("host"):
        scheme = (spec.get("schemes") or ["https"])[0]
        base_url = f"{scheme}://{spec['host']}{spec.get('basePath', '')}"
    endpoints = list((spec.get("paths") or {}).keys())
    return {
        "kind": kind,
        "title": info.get("title") or "",
        "version": info.get("version") or "",
        "base_url": base_url,
        "endpoints": endpoints,
    }


def hunt_metadata_apis(entry: dict, args) -> list[dict]:
    """Probe descriptor paths on one API; return any metadata APIs found."""
    base = entry.get("base_url") or entry.get("url")
    if not base:
        return []
    base = urllib.parse.urljoin(base.rstrip("/") + "/", "")  # ensure trailing slash form
    found: list[dict] = []
    candidates = [urllib.parse.urljoin(base, p.lstrip("/")) for p in config.METADATA_PROBE_PATHS]

    def check(url: str):
        resp = probe(url, args)
        if not resp or resp["http_status"] >= 400:
            return None
        payload = resp.get("json")
        kind = _looks_like_spec(payload)
        if kind == "openapi3":
            spec = payload
            details = _spec_details(spec, url)
            details.update({"url": url, "kind": "openapi3"})
            return details
        if kind == "swagger2":
            details = _spec_details(payload, url)
            details.update({"url": url, "kind": "swagger2"})
            return details
        if _looks_like_openid(payload):
            return {
                "url": url,
                "kind": "openid-configuration",
                "issuer": payload.get("issuer"),
                "endpoints": [
                    payload.get("authorization_endpoint"),
                    payload.get("token_endpoint"),
                    payload.get("userinfo_endpoint"),
                    payload.get("jwks_uri"),
                ],
            }
        # health/actuator style endpoints still count as machine-readable metadata
        # — but only when they actually return structured (JSON) data, otherwise
        # SPA catch-all routes would produce false positives.
        if (
            any(k in url for k in ("/health", "/actuator", "/metadata"))
            and resp["http_status"] < 300
            and (resp.get("json") is not None or "json" in (resp.get("content_type") or ""))
        ):
            return {
                "url": url,
                "kind": "service-metadata",
                "content_type": resp.get("content_type", ""),
                "sample": util.truncate(resp.get("text", ""), 200),
            }
        return None

    with ThreadPoolExecutor(max_workers=min(6, args.workers)) as pool:
        for res in pool.map(check, candidates):
            if res:
                res["endpoints"] = [e for e in (res.get("endpoints") or []) if e]
                found.append(res)
    return found


def run(entries: list[dict], args) -> list[dict]:
    """Analyse every tested entry and hunt metadata APIs on reachable ones."""
    reachable = [
        e
        for e in entries
        if (e.get("test") or {}).get("status")
        in ("working", "needs_params", "auth_required", "rate_limited")
    ]

    results: dict[str, dict] = {}

    def work(entry: dict):
        meta = analyze_entry(entry, args)
        metas = hunt_metadata_apis(entry, args) if args.meta_probe else []
        return util.url_key(entry.get("url", "")), meta, metas

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
            TextColumn("[bold magenta]analysing metadata[/bold magenta]"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("meta", total=len(reachable))
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = [pool.submit(work, e) for e in reachable]
                for fut in as_completed(futures):
                    key, meta, metas = fut.result()
                    results[key] = {"metadata": meta, "metadata_apis": metas}
                    progress.advance(task)
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for key, meta, metas in pool.map(work, reachable):
                results[key] = {"metadata": meta, "metadata_apis": metas}

    for entry in entries:
        key = util.url_key(entry.get("url", ""))
        if key in results:
            entry.update(results[key])
            if entry.get("metadata_apis"):
                entry["is_metadata_api"] = True
        # an entry whose own URL *is* an OpenAPI/Swagger descriptor counts as a
        # metadata API too — surface it with its base URL + endpoints.
        if (entry.get("metadata") or {}).get("is_metadata_api") and not entry.get("metadata_apis"):
            self_api = _self_metadata_api(entry, args)
            if self_api:
                entry.setdefault("metadata_apis", []).append(self_api)
                entry["is_metadata_api"] = True

    # notify listeners now that every entry carries its metadata_apis / secrets
    on_meta = getattr(args, "on_meta", None)
    if on_meta:
        for entry in entries:
            on_meta(entry)

    # Optionally test the endpoints advertised by discovered metadata APIs.
    if args.test_meta_endpoints:
        _test_metadata_endpoints(entries, args)
    return entries


def _self_metadata_api(entry: dict, args) -> dict | None:
    """Entry URL itself returns an OpenAPI/Swagger spec -> describe it."""
    payload, err = util.fetch_json(entry.get("url", ""), timeout=args.timeout, headers=args.headers)
    if not isinstance(payload, dict):
        return None
    kind = _looks_like_spec(payload)
    if not kind:
        return None
    details = _spec_details(payload, entry.get("url"))
    details["url"] = entry.get("url")
    details["kind"] = kind
    return details


def _test_metadata_endpoints(entries: list[dict], args) -> None:
    """For every discovered metadata API, test its base URL + a few endpoints."""
    jobs = []
    for entry in entries:
        for meta_api in entry.get("metadata_apis") or []:
            if not meta_api.get("base_url") and meta_api.get("kind") not in (
                "service-metadata",
                "openid-configuration",
            ):
                continue
            base = meta_api.get("base_url") or meta_api.get("url")
            paths = sorted(meta_api.get("endpoints") or [], key=len)[:3]
            jobs.append((entry, meta_api, base, paths))

    def check(job):
        entry, meta_api, base, paths = job
        results = []
        if base:
            results.append(
                {
                    "url": base,
                    "path": "(base)",
                    "status": tester.probe(
                        base, timeout=args.timeout, headers=args.headers,
                        verify=not args.insecure,
                    )["status"],
                }
            )
        for path in paths:
            filled = tester.fill_params(path)
            if filled is None:
                continue
            url = urllib.parse.urljoin(base.rstrip("/") + "/", filled.lstrip("/"))
            res = tester.probe(
                url, timeout=args.timeout, headers=args.headers, verify=not args.insecure
            )
            results.append(
                {"url": url, "path": path, "status": res["status"], "http_status": res["http_status"]}
            )
        return entry, meta_api, results

    if not jobs:
        return
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for entry, meta_api, results in pool.map(check, jobs):
            meta_api["endpoint_tests"] = results
