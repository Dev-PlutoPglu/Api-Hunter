"""Shared helpers: HTTP fetching, URL cleaning, JSON I/O, small utilities."""
from __future__ import annotations

import json
import os
import re
import urllib.parse
from datetime import datetime, timezone

import requests

from . import config

DEFAULT_HEADERS = {"User-Agent": config.USER_AGENT, "Accept": "*/*"}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def truncate(text, limit: int = 200) -> str:
    if text is None:
        return ""
    text = str(text).replace("\n", " ").replace("\r", " ").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def clean_url(url: str) -> str:
    """Normalise a URL for testing: drop fragments/utm params/placeholders."""
    if not url:
        return ""
    url = url.strip().strip("<>").strip()
    url = re.sub(r"[)\]>,;'\"]+$", "", url)
    if not re.match(r"^https?://", url, re.I):
        url = "http://" + url
    try:
        parts = urllib.parse.urlsplit(url)
        if parts.query and "=" not in parts.query:
            # not key=value pairs (e.g. "?api-docs.json") — keep verbatim
            new_query = parts.query
        else:
            query = [
                (k, v)
                for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
                if not k.lower().startswith("utm_")
            ]
            new_query = urllib.parse.urlencode(query)
        cleaned = urllib.parse.urlunsplit(
            (parts.scheme, parts.netloc, parts.path, new_query, "")
        )
    except Exception:
        return url
    return cleaned.rstrip("/") if cleaned.count("/") > 3 else cleaned


def has_placeholders(url: str) -> bool:
    return bool(re.search(r"\{[^}]+\}", url or ""))


def url_root(url: str) -> str:
    try:
        p = urllib.parse.urlsplit(url)
        return f"{p.scheme}://{p.netloc}"
    except Exception:
        return url


def url_key(url: str) -> str:
    """Dedupe key: scheme-agnostic, case-insensitive host+path."""
    try:
        p = urllib.parse.urlsplit((url or "").lower())
        host = p.netloc[4:] if p.netloc.startswith("www.") else p.netloc
        path = p.path.rstrip("/")
        return f"{host}{path}"
    except Exception:
        return url or ""


def fetch_text(url: str, timeout: int = 25, headers: dict | None = None):
    """GET a URL as text. Returns (text, error)."""
    try:
        r = requests.get(
            url,
            headers={**DEFAULT_HEADERS, **(headers or {})},
            timeout=timeout,
            allow_redirects=True,
        )
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}"
        return r.text, None
    except Exception as exc:  # noqa: BLE001 - report any network failure
        return None, f"{type(exc).__name__}: {exc}"


def fetch_json(url: str, timeout: int = 30, headers: dict | None = None):
    try:
        r = requests.get(
            url, headers={**DEFAULT_HEADERS, **(headers or {})}, timeout=timeout
        )
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}"
        return r.json(), None
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"


def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def read_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def human_size(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num) < 1024:
            return f"{num:.1f}{unit}"
        num /= 1024
    return f"{num:.1f}TB"


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path
