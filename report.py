"""Rendering & export: rich console tables plus JSON / CSV / Markdown reports."""
from __future__ import annotations

import csv
import os

from . import util

STATUS_ORDER = [
    "working",
    "auth_required",
    "rate_limited",
    "needs_params",
    "not_working",
    "error",
    "skipped",
]

STATUS_STYLE = {
    "working": "bold green",
    "auth_required": "yellow",
    "rate_limited": "cyan",
    "needs_params": "blue",
    "not_working": "red",
    "error": "dim red",
    "skipped": "dim",
}

STATUS_LABEL = {
    "working": "WORKING",
    "auth_required": "KEY NEEDED",
    "rate_limited": "RATE LIMITED",
    "needs_params": "NEEDS PARAMS",
    "not_working": "DEAD",
    "error": "ERROR",
    "skipped": "SKIPPED",
}


def summarize(entries: list[dict]) -> dict:
    counts: dict[str, int] = {}
    meta_apis = 0
    keys_found = 0
    sources: dict[str, int] = {}
    for e in entries:
        status = (e.get("test") or {}).get("status", "skipped")
        counts[status] = counts.get(status, 0) + 1
        sources[e.get("source", "?")] = sources.get(e.get("source", "?"), 0) + 1
        if e.get("metadata_apis"):
            meta_apis += len(e["metadata_apis"])
        keys_found += len(e.get("secrets") or [])
    return {
        "total": len(entries),
        "by_status": counts,
        "by_source": sources,
        "metadata_apis": meta_apis,
        "secrets": keys_found,
    }


def _sort_key(entry: dict):
    status = (entry.get("test") or {}).get("status", "skipped")
    rank = STATUS_ORDER.index(status) if status in STATUS_ORDER else len(STATUS_ORDER)
    latency = (entry.get("test") or {}).get("latency_ms") or 99999
    return (rank, latency)


# ---------------------------------------------------------------------------
# Console
# ---------------------------------------------------------------------------

def render_console(entries: list[dict], args, title: str = "API HUNT RESULTS") -> None:
    if not entries:
        print("No APIs matched the hunt.")
        return

    ordered = sorted(entries, key=_sort_key)
    summary = summarize(entries)

    if not (args.rich and not args.quiet):
        _render_plain(ordered, summary)
        return

    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    console = Console()
    console.rule(f"[bold cyan]{title}[/bold cyan]")

    stats = Text()
    for status in STATUS_ORDER:
        n = summary["by_status"].get(status, 0)
        if n:
            stats.append(f"  {STATUS_LABEL[status]}: ", style=STATUS_STYLE[status])
            stats.append(f"{n}", style="bold")
    stats.append(f"\n  Metadata APIs discovered: {summary['metadata_apis']}")
    if summary["secrets"]:
        stats.append(f"   |   Potential API keys/secrets: {summary['secrets']}", style="bold yellow")
    console.print(Panel(stats, title="Summary", border_style="cyan", expand=False))

    table = Table(box=box.SIMPLE_HEAD, expand=True, show_lines=False)
    table.add_column("API", style="bold", max_width=34, no_wrap=True)
    table.add_column("Source", max_width=22, no_wrap=True)
    table.add_column("Auth", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("HTTP", justify="right")
    table.add_column("ms", justify="right")
    table.add_column("URL", overflow="ellipsis", max_width=52, no_wrap=True)

    for e in ordered:
        test = e.get("test") or {}
        status = test.get("status", "skipped")
        http = test.get("http_status")
        table.add_row(
            util.truncate(e.get("name", "?"), 34),
            e.get("source", "?"),
            e.get("auth", "unknown"),
            Text(STATUS_LABEL.get(status, status), style=STATUS_STYLE.get(status, "")),
            str(http) if http else "-",
            f"{test['latency_ms']:.0f}" if test.get("latency_ms") is not None else "-",
            util.truncate(e.get("base_url") or e.get("url") or "", 52),
        )
    console.print(table)

    # ---- metadata APIs ----------------------------------------------------
    meta_rows = []
    for e in ordered:
        for m in e.get("metadata_apis") or []:
            meta_rows.append((e, m))
    if meta_rows:
        mtable = Table(
            title="METADATA APIs discovered (machine-readable descriptors)",
            box=box.SIMPLE_HEAD,
            expand=True,
        )
        mtable.add_column("Parent API", style="bold", max_width=28, no_wrap=True)
        mtable.add_column("Kind", style="magenta")
        mtable.add_column("Descriptor URL", overflow="fold", max_width=44)
        mtable.add_column("Base URL", overflow="fold", max_width=32)
        mtable.add_column("Endpoints", justify="right")
        for e, m in meta_rows:
            mtable.add_row(
                util.truncate(e.get("name", "?"), 28),
                m.get("kind", "?"),
                util.truncate(m.get("url", ""), 44),
                util.truncate(m.get("base_url") or "-", 32),
                str(len(m.get("endpoints") or [])),
            )
        console.print(mtable)

    # ---- secrets -----------------------------------------------------------
    secret_rows = [
        (e, s) for e in ordered for s in (e.get("secrets") or [])
    ]
    if secret_rows:
        stable = Table(
            title="Potential API keys / secrets found in source (reverse mode)",
            box=box.SIMPLE_HEAD,
            expand=True,
        )
        stable.add_column("API", style="bold", max_width=28, no_wrap=True)
        stable.add_column("Type", style="yellow")
        stable.add_column("Key (masked)", max_width=34)
        stable.add_column("Evidence", overflow="fold", max_width=50)
        for e, s in secret_rows:
            key = s.get("key", "")
            masked = key[:6] + "…" + key[-4:] if len(key) > 12 else "…"
            stable.add_row(
                util.truncate(e.get("name", "?"), 28),
                s.get("type", "?"),
                masked,
                util.truncate(s.get("evidence", ""), 50),
            )
        console.print(stable)

    # ---- errors ------------------------------------------------------------
    dead = [e for e in ordered if (e.get("test") or {}).get("status") in ("error", "not_working")]
    if dead and args.verbose:
        etable = Table(title="Dead / errored APIs", box=box.SIMPLE_HEAD, expand=True)
        etable.add_column("API", style="bold", max_width=30, no_wrap=True)
        etable.add_column("Error", overflow="fold")
        for e in dead:
            etable.add_row(
                util.truncate(e.get("name", "?"), 30),
                (e.get("test") or {}).get("error") or f"HTTP {(e.get('test') or {}).get('http_status')}",
            )
        console.print(etable)


def _render_plain(ordered: list[dict], summary: dict) -> None:
    print(f"\n  {summary['total']} APIs | " + " | ".join(
        f"{STATUS_LABEL.get(s, s)}: {n}" for s, n in summary["by_status"].items()
    ))
    print(f"  Metadata APIs: {summary['metadata_apis']} | Secrets: {summary['secrets']}\n")
    for e in ordered:
        test = e.get("test") or {}
        status = test.get("status", "skipped")
        print(
            f"  [{STATUS_LABEL.get(status, status):>12}] "
            f"{util.truncate(e.get('name', '?'), 30):30} "
            f"auth={e.get('auth', '?'):10} "
            f"{str(test.get('http_status') or '-'):>4} "
            f"{util.truncate(e.get('base_url') or e.get('url') or '', 60)}"
        )
        for m in e.get("metadata_apis") or []:
            print(f"       + metadata api ({m.get('kind')}): {m.get('url')} "
                  f"base={m.get('base_url') or '-'} endpoints={len(m.get('endpoints') or [])}")
        for s in e.get("secrets") or []:
            print(f"       ! secret ({s.get('type')}): {s.get('key', '')[:10]}… in {s.get('evidence', '')[:60]}")


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

def export_json(entries: list[dict], path: str) -> str:
    payload = {
        "generated_at": util.now_iso(),
        "summary": summarize(entries),
        "apis": entries,
    }
    util.write_json(path, payload)
    return path


def export_csv(entries: list[dict], path: str) -> str:
    fields = [
        "name", "source", "category", "auth", "https", "url", "base_url",
        "status", "http_status", "latency_ms", "content_type", "error",
        "is_metadata_api", "metadata_api_urls", "endpoints", "description",
    ]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for e in entries:
            test = e.get("test") or {}
            writer.writerow(
                {
                    "name": e.get("name", ""),
                    "source": e.get("source", ""),
                    "category": e.get("category", ""),
                    "auth": e.get("auth", ""),
                    "https": e.get("https"),
                    "url": e.get("url", ""),
                    "base_url": e.get("base_url", ""),
                    "status": test.get("status", ""),
                    "http_status": test.get("http_status", ""),
                    "latency_ms": test.get("latency_ms", ""),
                    "content_type": test.get("content_type", ""),
                    "error": test.get("error", ""),
                    "is_metadata_api": e.get("is_metadata_api", False),
                    "metadata_api_urls": ";".join(
                        m.get("url", "") for m in (e.get("metadata_apis") or [])
                    ),
                    "endpoints": ";".join(e.get("endpoints") or []),
                    "description": e.get("description", ""),
                }
            )
    return path


def export_markdown(entries: list[dict], path: str) -> str:
    ordered = sorted(entries, key=_sort_key)
    summary = summarize(entries)
    lines = [
        "# API Hunt Report",
        "",
        f"_Generated {util.now_iso()} by API Hunter_",
        "",
        f"- Total APIs: **{summary['total']}**",
    ]
    for status in STATUS_ORDER:
        n = summary["by_status"].get(status, 0)
        if n:
            lines.append(f"- {STATUS_LABEL.get(status, status)}: **{n}**")
    lines += [
        f"- Metadata APIs discovered: **{summary['metadata_apis']}**",
        f"- Potential secrets: **{summary['secrets']}**",
        "",
        "## Results",
        "",
        "| API | Source | Auth | Status | HTTP | ms | URL |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in ordered:
        test = e.get("test") or {}
        status = test.get("status", "skipped")
        lines.append(
            "| {name} | {src} | {auth} | {status} | {http} | {ms} | {url} |".format(
                name=e.get("name", "?").replace("|", "\\|"),
                src=e.get("source", "?"),
                auth=e.get("auth", "?"),
                status=STATUS_LABEL.get(status, status),
                http=test.get("http_status", "-"),
                ms=f"{test['latency_ms']:.0f}" if test.get("latency_ms") is not None else "-",
                url=e.get("base_url") or e.get("url") or "",
            )
        )

    meta_rows = [(e, m) for e in ordered for m in (e.get("metadata_apis") or [])]
    if meta_rows:
        lines += ["", "## Metadata APIs", "", "| Parent API | Kind | Descriptor URL | Base URL | Endpoints |", "|---|---|---|---|---|"]
        for e, m in meta_rows:
            lines.append(
                f"| {e.get('name', '?')} | {m.get('kind', '?')} | {m.get('url', '')} "
                f"| {m.get('base_url') or '-'} | {len(m.get('endpoints') or [])} |"
            )
        for e, m in meta_rows:
            if m.get("endpoints"):
                lines += ["", f"### `{e.get('name', '?')}` endpoints ({m.get('kind')})", ""]
                lines += [f"- `{p}`" for p in m["endpoints"][:40]]

    secret_rows = [(e, s) for e in ordered for s in (e.get("secrets") or [])]
    if secret_rows:
        lines += ["", "## Potential API keys / secrets (handle responsibly)", "",
                  "| API | Type | Masked key | Evidence |", "|---|---|---|---|"]
        for e, s in secret_rows:
            key = s.get("key", "")
            masked = key[:6] + "…" + key[-4:] if len(key) > 12 else "…"
            lines.append(f"| {e.get('name', '?')} | {s.get('type', '?')} | `{masked}` | {s.get('evidence', '')[:60]} |")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def save_report(entries: list[dict], outdir: str, args) -> dict:
    # AI + Security enrichments (optional, env-driven)
    os.makedirs(outdir, exist_ok=True)
    paths = {
        "json": os.path.join(outdir, "api-hunt-report.json"),
        "csv": os.path.join(outdir, "api-hunt-report.csv"),
        "md": os.path.join(outdir, "api-hunt-report.md"),
        "html": os.path.join(outdir, "api-hunt-report.html"),
    }
    export_json(entries, paths["json"])
    export_csv(entries, paths["csv"])
    export_markdown(entries, paths["md"])
    try:
        export_html(entries, paths["html"])
    except Exception:
        pass
    # Self-healing: retry NEEDS_PARAMS with AI-generated body
    try:
        from . import ai
        for e in entries:
            if (e.get("test") or {}).get("status") == "needs_params":
                healed = ai.self_healing_test(e, args)
                if healed and healed.get("status") == "working":
                    e["test"].update(healed)
                    e["healed"] = True
    except Exception:
        pass
    # AI docs for working APIs
    try:
        from . import ai as ai2
        for e in entries:
            if (e.get("test") or {}).get("status") == "working":
                e["ai_docs"] = ai2.generate_docs_for_api(e)
    except Exception:
        pass
    # Security: CVE + secret validation
    try:
        from . import security
        for e in entries:
            server = (e.get("test") or {}).get("server") or (e.get("metadata") or {}).get("server") or ""
            if server:
                e["cves"] = security.cve_scan(server)
        validated = security.validate_all_secrets(entries)
        if validated:
            # Attach validation to each secret
            vmap = {(v.get("key") or ""): v for v in validated}
            for e in entries:
                for s in e.get("secrets") or []:
                    v = vmap.get(s.get("key"))
                    if v:
                        s.update(v)
    except Exception:
        pass
    return paths

# ---------------------------------------------------------------------------
# POWER REPORTS — Interactive HTML, GitHub Pages ready
# ---------------------------------------------------------------------------

def export_html(entries: list[dict], path: str) -> str:
    """Interactive HTML report — searchable, copy curl, GitHub Pages ready."""
    import json, html
    ordered = sorted(entries, key=_sort_key)
    summary = summarize(entries)
    # Build rows as JSON for client-side filtering
    rows_json = json.dumps([{
        "name": e.get("name",""), "source": e.get("source",""), "category": e.get("category",""),
        "auth": e.get("auth",""), "url": e.get("url",""), "base_url": e.get("base_url") or e.get("url",""),
        "status": (e.get("test") or {}).get("status","skipped"), "http": (e.get("test") or {}).get("http_status"),
        "ms": (e.get("test") or {}).get("latency_ms"), "sample": (e.get("test") or {}).get("sample","")[:400],
        "secrets": len(e.get("secrets") or []), "meta": len(e.get("metadata_apis") or [])
    } for e in ordered])
    summary_json = json.dumps(summary)
    html_content = f'''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>API Hunter Report — {summary["total"]} APIs</title>
<style>
:root{{--primary:#635bff;--bg:#eef0f3;--card:#fff;--border:#e2e8f0;--text:#0f172a;--dim:#64748b;--radius:16px}}
body{{background:var(--bg);color:var(--text);font:14px/1.6 Inter,system-ui;padding:24px}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px;box-shadow:0 4px 24px rgba(15,23,42,.06)}}
.badge{{padding:4px 10px;border-radius:999px;font-size:11px;font-weight:700;color:#fff}}
.b-working{{background:#10b981}} .b-auth_required{{background:#f59e0b}} .b-rate_limited{{background:#3b82f6}} .b-not_working{{background:#ef4444}} .b-error{{background:#94a3b8}}
input{{width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:999px;outline:none}}
table{{width:100%;border-collapse:collapse}} th{{text-align:left;font-size:11px;letter-spacing:.08em;color:var(--dim);padding:12px;border-bottom:1px solid var(--border);cursor:pointer}} td{{padding:10px 12px;border-bottom:1px solid #f1f5f9}}
tr:hover{{background:rgba(99,91,255,.06)}}
</style>
</head>
<body>
<div style="max-width:1100px;margin:0 auto">
  <div class="card" style="background:linear-gradient(135deg,#1e1b4b,#4338ca);color:#fff;border:none">
    <h1 style="margin:0;font-size:28px">🔍 API Hunter Report</h1>
    <p style="opacity:.9">Total: {summary["total"]} APIs • Working: {summary["by_status"].get("working",0)} • Metadata: {summary["metadata_apis"]} • Secrets: {summary["secrets"]}</p>
    <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap">
      <input id="search" placeholder="🔎 Search by name/url/category..." oninput="filter()" style="flex:1;min-width:200px;background:#fff;color:#0f172a">
      <select id="filterStatus" onchange="filter()" style="padding:10px 14px;border-radius:999px;border:1px solid #e2e8f0"><option value="all">All statuses</option><option value="working">WORKING</option><option value="auth_required">KEY NEEDED</option><option value="rate_limited">RATE LIMITED</option><option value="not_working">DEAD</option></select>
      <button onclick="copyWorking()" style="padding:10px 16px;border-radius:999px;background:#fff;color:#1e1b4b;font-weight:700;border:none;cursor:pointer">Copy Working URLs</button>
    </div>
  </div>
  <div class="card" style="margin-top:16px;overflow:auto">
    <table><thead><tr><th onclick="sortBy('name')">API</th><th>Source</th><th>Status</th><th>HTTP</th><th>ms</th><th>URL</th><th>Curl</th></tr></thead><tbody id="rows"></tbody></table>
  </div>
  <p style="text-align:center;color:var(--dim);font-size:12px;margin-top:16px">Generated by API Hunter • <a href="https://github.com/Dev-PlutoPglu/api-hunter">GitHub</a> • Share this file on GitHub Pages!</p>
</div>
<script>
const rows = {rows_json};
const summary = {summary_json};
let sortKey="status", sortDir=-1;
function render(list){{ const tbody=document.getElementById("rows"); tbody.innerHTML=list.map(r=>`<tr><td><b>${{r.name}}</b><div style="font-size:11px;color:#64748b">${{r.category}}</div></td><td>${{r.source}}</td><td><span class="badge b-${{r.status}}">${{r.status.toUpperCase()}}</span></td><td>${{r.http??"-"}}</td><td>${{r.ms?Math.round(r.ms):"-"}}</td><td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${{r.url}}">${{r.base_url}}</td><td><button onclick="copyCurl('${{r.base_url}}')" style="padding:4px 8px;border-radius:999px;border:1px solid #e2e8f0;background:#fff;cursor:pointer;font-size:11px">curl</button></td></tr>`).join(""); }}
function filter(){{ const q=document.getElementById("search").value.toLowerCase(); const s=document.getElementById("filterStatus").value; let list=rows; if(s!=="all") list=list.filter(r=>r.status===s); if(q) list=list.filter(r=>(r.name+" "+r.url+" "+r.category).toLowerCase().includes(q)); render(list); }}
function sortBy(k){{ if(sortKey===k) sortDir*=-1; else{{sortKey=k;sortDir=1}} rows.sort((a,b)=>{{let x=a[k]||"",y=b[k]||"";return (x>y?1:x<y?-1:0)*sortDir}}); filter(); }}
function copyCurl(url){{ navigator.clipboard.writeText(`curl -i "${{url}}"`); alert("Copied: curl -i "+url); }}
function copyWorking(){{ const urls=rows.filter(r=>r.status==="working").map(r=>r.base_url).join("\\n"); navigator.clipboard.writeText(urls); alert(urls?`Copied ${{rows.filter(r=>r.status==="working").length}} URLs`:"No working APIs"); }}
render(rows);
</script>
</body>
</html>'''
    p = pathlib.Path(path) if 'pathlib' in dir() else None
    # Use os path directly
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html_content)
    return path

