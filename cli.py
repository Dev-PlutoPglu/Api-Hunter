"""API Hunter CLI — hunt free APIs from GitHub & the internet, or reverse-engineer
them out of a website / APK, then test every endpoint and hunt metadata APIs."""
from __future__ import annotations

import argparse
import os
import sys

from . import config, metadata, report, reverse, sources, tester, util

VERSION = "1.0.0"

BANNER = r"""
    _    ____ ___ ____   _   _    _   _ _____ ___ ____  _   _ __  __
   / \  |  _ \_ _|  _ \ / \ | |  | | | |_   _|_ _|  _ \| | | |  \/  |
  / _ \ | |_) | || |_) / _ \| |  | |_| | | |  | || |_) | |_| | |\/| |
 / ___ \|  __/| ||  __/ ___ \ |___|  _  | | |  | ||  _ <|  _  | |  | |
/_/   \_\_|  |___|_| /_/   \_____|_| |_| |_| |___|_| \_\_| |_|_|  |_|
"""


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apihunter",
        description=(
            "API Hunter — hunt free/public APIs from GitHub and the internet, or "
            "reverse-engineer the APIs hidden inside a website or APK. Every API is "
            "tested for reachability, auth requirements, latency and metadata "
            "(OpenAPI/Swagger descriptors, rate limits, response shape)."
        ),
        epilog=(
            "examples:\n"
            "  apihunter run -k weather -n 40\n"
            "  apihunter run -s public-apis,apisguru --endpoints deep -k finance\n"
            "  apihunter discover -k animals -o out\n"
            "  apihunter test out/catalog.json\n"
            "  apihunter reverse-web https://example.com --max-js 20\n"
            "  apihunter reverse-apk ./app.apk --apk-deep\n"
            "  apihunter report out/results.json\n"
            "  apihunter ui --port 8787          # live web dashboard\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"api-hunter {VERSION}")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-k", "--keyword", default="", help="only keep APIs matching this keyword")
    common.add_argument("-c", "--category", default="", help="only keep APIs in this category")
    common.add_argument(
        "-a", "--auth", default="any",
        choices=["any", "none", "apiKey", "OAuth", "unknown"],
        help="filter by auth type (default: any)",
    )
    common.add_argument("-n", "--limit", type=int, default=config.DEFAULT_LIMIT,
                        help=f"max APIs to keep (0 = no limit, default {config.DEFAULT_LIMIT})")
    common.add_argument("-w", "--workers", type=int, default=config.DEFAULT_WORKERS,
                        help=f"concurrent testers (default {config.DEFAULT_WORKERS})")
    common.add_argument("-t", "--timeout", type=int, default=config.DEFAULT_TIMEOUT,
                        help=f"HTTP timeout seconds (default {config.DEFAULT_TIMEOUT})")
    common.add_argument("--retries", type=int, default=config.DEFAULT_RETRIES,
                        help="retries per request on network errors")
    common.add_argument("--http-timeout", type=int, default=25, dest="http_timeout",
                        help="timeout for catalog/spec downloads")
    common.add_argument("-H", "--header", action="append", default=[],
                        help="extra header for API calls, e.g. -H 'X-Api-Key: abc' (repeatable)")
    common.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN", ""),
                        help="GitHub token (raises search rate limits)")
    common.add_argument("--insecure", action="store_true",
                        help="skip TLS certificate verification")
    common.add_argument("-o", "--outdir", default="apihunter_out",
                        help="output directory for reports (default: apihunter_out)")
    common.add_argument("--no-color", action="store_true", help="disable coloured output")
    common.add_argument("--quiet", "-q", action="store_true", help="less chatter")
    common.add_argument("--verbose", "-v", action="store_true", help="more detail (incl. dead APIs)")
    common.add_argument("--endpoints", choices=["off", "base", "deep"], default="base",
                        help="base: test base URLs; deep: also test spec endpoints (default: base)")

    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", parents=[common],
                           help="full pipeline: hunt -> test -> metadata -> report (default)")
    p_run.add_argument("-s", "--sources", default="public-apis,apisguru,github,builtin",
                       help="comma list: public-apis, github, apisguru, builtin")
    p_run.add_argument("--specs", type=int, default=config.DEFAULT_SPECS,
                       help=f"max apis.guru specs to fetch (default {config.DEFAULT_SPECS})")
    p_run.add_argument("--github-repos", type=int, default=6, dest="github_repos",
                       help="max GitHub repos per search query (default 6)")
    p_run.add_argument("--github-queries", default=",".join(config.GITHUB_DEFAULT_QUERIES),
                       dest="github_queries",
                       help="comma-separated GitHub search queries")

    p_disc = sub.add_parser("discover", parents=[common], help="only hunt & save the catalog")
    p_disc.add_argument("-s", "--sources", default="public-apis,apisguru,github,builtin")
    p_disc.add_argument("--specs", type=int, default=config.DEFAULT_SPECS)
    p_disc.add_argument("--github-repos", type=int, default=6, dest="github_repos")
    p_disc.add_argument("--github-queries", default=",".join(config.GITHUB_DEFAULT_QUERIES),
                        dest="github_queries")

    p_test = sub.add_parser("test", parents=[common], help="test APIs from a saved catalog/results file")
    p_test.add_argument("input", help="path to catalog.json or results.json")

    p_meta = sub.add_parser("metadata", parents=[common],
                            help="enrich a results file with metadata & metadata-API hunting")
    p_meta.add_argument("input", help="path to results.json")

    p_rep = sub.add_parser("report", parents=[common], help="render/export a report from a results file")
    p_rep.add_argument("input", help="path to results.json")

    p_rweb = sub.add_parser("reverse-web", parents=[common],
                            help="reverse-engineer a website: mine its JS for hidden APIs")
    p_rweb.add_argument("url", help="website URL, e.g. https://example.com")
    p_rweb.add_argument("--max-js", type=int, default=15, dest="max_js",
                        help="max JS assets to download & mine (default 15)")
    p_rweb.add_argument("--no-test", action="store_true", help="extract only, do not test")

    p_rapk = sub.add_parser("reverse-apk", parents=[common],
                            help="reverse-engineer an APK: mine DEX/strings for hidden APIs")
    p_rapk.add_argument("apk", help="path to the .apk file")
    p_rapk.add_argument("--apk-deep", action="store_true",
                        help="use apktool/jadx if installed for smali/Java mining")
    p_rapk.add_argument("--no-test", action="store_true", help="extract only, do not test")

    p_ui = sub.add_parser("ui", parents=[common],
                          help="launch the localhost web dashboard (live progress)")
    p_ui.add_argument("--host", default="127.0.0.1",
                      help="bind host (use 0.0.0.0 to share on your network)")
    p_ui.add_argument("--port", type=int, default=8787, help="port (default 8787)")
    p_ui.add_argument("--no-browser", action="store_true",
                      help="do not auto-open the browser")

    sub.add_parser("sources", help="list the available hunt sources")

    # shared testing/metadata tunables on every command that needs them
    for p in (p_run, p_test, p_meta, p_rweb, p_rapk):
        p.add_argument("--max-endpoints", type=int, default=config.DEFAULT_MAX_ENDPOINTS,
                       dest="max_endpoints",
                       help=f"max spec endpoints to test per API in deep mode (default {config.DEFAULT_MAX_ENDPOINTS})")
        p.add_argument("--no-meta-probe", action="store_true", dest="no_meta_probe",
                       help="skip probing for OpenAPI/Swagger/metadata endpoints")
        p.add_argument("--no-test-meta-endpoints", action="store_true", dest="no_test_meta_endpoints",
                       help="do not test endpoints advertised by metadata APIs")

    parser.set_defaults(func=cmd_run, rich=None)
    p_run.set_defaults(func=cmd_run)
    p_disc.set_defaults(func=cmd_discover)
    p_test.set_defaults(func=cmd_test)
    p_meta.set_defaults(func=cmd_metadata)
    p_rep.set_defaults(func=cmd_report)
    p_rweb.set_defaults(func=cmd_reverse_web)
    p_rapk.set_defaults(func=cmd_reverse_apk)
    sub.choices["sources"].set_defaults(func=cmd_sources)
    p_ui.set_defaults(func=cmd_ui)
    return parser


def parse_headers(header_list: list[str]) -> dict:
    headers = {}
    for item in header_list or []:
        if ":" in item:
            key, _, value = item.partition(":")
            headers[key.strip()] = value.strip()
    return headers


def finalize_args(args) -> None:
    args.headers = parse_headers(getattr(args, "header", []))
    args.rich = (
        (not getattr(args, "no_color", False)
         and not os.environ.get("NO_COLOR")
         and (sys.stdout.isatty() or os.environ.get("APIHUNTER_FORCE_RICH")))
    )
    args.log = lambda msg: _log(msg, args)
    args.meta_probe = not getattr(args, "no_meta_probe", False)
    args.test_meta_endpoints = not getattr(args, "no_test_meta_endpoints", False)
    args.test = not getattr(args, "no_test", False)
    args.specs = getattr(args, "specs", config.DEFAULT_SPECS)
    args.max_endpoints = getattr(args, "max_endpoints", config.DEFAULT_MAX_ENDPOINTS)
    args.github_repos = getattr(args, "github_repos", 6)
    args.github_queries = [
        q.strip() for q in (getattr(args, "github_queries", "") or "").split(",") if q.strip()
    ] or config.GITHUB_DEFAULT_QUERIES
    args.sources = getattr(args, "sources", "")
    args.max_js = getattr(args, "max_js", 15)
    args.apk_deep = getattr(args, "apk_deep", False)
    args.endpoints = getattr(args, "endpoints", "base")
    args.input = getattr(args, "input", None)


def _log(msg: str, args) -> None:
    if args.rich:
        from rich.console import Console

        Console(stderr=True).print(f"[dim]{msg}[/dim]")
    elif not args.quiet:
        print(msg, file=sys.stderr)


def print_banner(args) -> None:
    if args.quiet:
        return
    if args.rich:
        from rich.console import Console

        Console().print(f"[bold cyan]{BANNER}[/bold cyan]")
    else:
        print(BANNER)


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def filter_entries(entries: list[dict], args) -> list[dict]:
    if args.keyword:
        kw = args.keyword.lower()
        entries = [
            e for e in entries
            if kw in " ".join(
                str(e.get(f, "")) for f in ("name", "url", "description", "category")
            ).lower()
        ]
    if args.category:
        cat = args.category.lower()
        entries = [e for e in entries if cat in str(e.get("category", "")).lower()]
    if args.auth and args.auth != "any":
        entries = [e for e in entries if str(e.get("auth", "unknown")).lower() == args.auth.lower()]
    if args.limit and len(entries) > args.limit:
        # keep the richest / most testable first
        entries.sort(key=lambda e: (0 if e.get("base_url") else 1, -len(e.get("endpoints") or [])))
        entries = entries[: args.limit]
    return entries


def finish(entries: list[dict], args, title: str) -> None:
    """Render console report + write JSON/CSV/Markdown exports."""
    report.render_console(entries, args, title=title)
    paths = report.save_report(entries, args.outdir, args)
    summary = report.summarize(entries)
    if args.rich:
        from rich.console import Console

        console = Console()
        msg = (
            f"[bold green]done.[/bold green] {summary['total']} APIs | "
            f"working: {summary['by_status'].get('working', 0)} | "
            f"metadata APIs: {summary['metadata_apis']} | secrets: {summary['secrets']}\n"
            f"reports: [cyan]{paths['json']}[/cyan], [cyan]{paths['csv']}[/cyan], [cyan]{paths['md']}[/cyan]"
        )
        console.print(msg)
    else:
        print(
            f"done. {summary['total']} APIs | working: {summary['by_status'].get('working', 0)} | "
            f"metadata APIs: {summary['metadata_apis']} | secrets: {summary['secrets']}"
        )
        for p in paths.values():
            print(f"  report: {p}")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_run(args) -> int:
    print_banner(args)
    args.log("[*] stage 1/4: hunting catalogs (github + internet)")
    entries, errors = sources.discover(args)
    for err in errors:
        args.log(f"[!] {err}")
    args.log(f"[*] {len(entries)} unique APIs discovered")

    entries = filter_entries(entries, args)
    args.log(f"[*] {len(entries)} APIs after filters (keyword='{args.keyword}', category='{args.category}', auth={args.auth})")
    util.write_json(os.path.join(args.outdir, "catalog.json"), entries)

    args.log("[*] stage 2/4: testing endpoints")
    entries = tester.run(entries, args)

    args.log("[*] stage 3/4: analysing metadata + hunting metadata APIs")
    entries = metadata.run(entries, args)

    util.write_json(os.path.join(args.outdir, "results.json"), entries)
    args.log("[*] stage 4/4: reporting")
    finish(entries, args, title="API HUNT RESULTS")
    return 0


def cmd_discover(args) -> int:
    print_banner(args)
    entries, errors = sources.discover(args)
    for err in errors:
        args.log(f"[!] {err}")
    entries = filter_entries(entries, args)
    path = os.path.join(args.outdir, "catalog.json")
    util.write_json(path, entries)
    args.log(f"[*] {len(entries)} APIs saved to {path}")
    report.render_console(entries, args, title="DISCOVERED CATALOG")
    print(f"catalog saved: {path}")
    return 0


def cmd_test(args) -> int:
    print_banner(args)
    entries = util.read_json(args.input)
    if isinstance(entries, dict):
        entries = entries.get("apis", [])
    entries = filter_entries(entries, args)
    args.log(f"[*] testing {len(entries)} APIs from {args.input}")
    entries = tester.run(entries, args)
    entries = metadata.run(entries, args)
    path = os.path.join(args.outdir, "results.json")
    util.write_json(path, entries)
    finish(entries, args, title="API TEST RESULTS")
    return 0


def cmd_metadata(args) -> int:
    print_banner(args)
    entries = util.read_json(args.input)
    if isinstance(entries, dict):
        entries = entries.get("apis", [])
    args.log(f"[*] analysing metadata for {len(entries)} APIs")
    entries = metadata.run(entries, args)
    path = os.path.join(args.outdir, "results.json")
    util.write_json(path, entries)
    finish(entries, args, title="API METADATA REPORT")
    return 0


def cmd_report(args) -> int:
    print_banner(args)
    entries = util.read_json(args.input)
    if isinstance(entries, dict):
        entries = entries.get("apis", [])
    finish(entries, args, title="API HUNT REPORT")
    return 0


def cmd_reverse_web(args) -> int:
    print_banner(args)
    args.log(f"[*] reverse-engineering website: {args.url}")
    entries = reverse.hunt_from_target("web", args.url, args)
    if not entries:
        print("no API candidates found in the website.")
        return 1
    util.write_json(os.path.join(args.outdir, "results.json"), entries)
    finish(entries, args, title=f"REVERSE-WEB: {args.url}")
    return 0


def cmd_reverse_apk(args) -> int:
    print_banner(args)
    args.log(f"[*] reverse-engineering APK: {args.apk}")
    entries = reverse.hunt_from_target("apk", args.apk, args)
    if not entries:
        print("no API candidates found in the APK.")
        return 1
    util.write_json(os.path.join(args.outdir, "results.json"), entries)
    finish(entries, args, title=f"REVERSE-APK: {os.path.basename(args.apk)}")
    return 0


def cmd_ui(args) -> int:
    from . import ui

    return ui.serve(
        host=getattr(args, "host", "127.0.0.1"),
        port=getattr(args, "port", 8787),
        open_browser=not getattr(args, "no_browser", False),
    )


def cmd_sources(args) -> int:
    print("Available hunt sources (use with -s/--sources):\n")
    print("  public-apis  GitHub: public-apis/public-apis markdown catalog (~1400 APIs)")
    print("  github       GitHub repository search for other free-API lists (READMEs mined)")
    print("  apisguru     APIs.guru directory (2500+ real OpenAPI specs: base URLs + endpoints)")
    print("  builtin      Offline fallback catalog of ~30 known no-key APIs\n")
    print("Reverse targets:")
    print("  apihunter reverse-web https://site.com   mine a website's JS for APIs")
    print("  apihunter reverse-apk app.apk            mine an APK's DEX/strings for APIs")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        # no subcommand given -> default to the full pipeline
        args = parser.parse_args(["run"] + argv)
    finalize_args(args)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\ninterrupted — partial results may be in the output directory.")
        return 130
