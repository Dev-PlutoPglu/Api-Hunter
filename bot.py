"""Telegram/Discord bot: 'Hunter bot: weather apis?' -> 5 working links"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from apihunter import sources, tester, util, config
from apihunter.cli import filter_entries
import argparse

def hunt_sync(keyword="weather", n=5):
    args = argparse.Namespace(keyword=keyword, category="", auth="none", limit=n, workers=6, timeout=10, retries=1, http_timeout=15, headers={}, github_token="", insecure=False, outdir="apihunter_out", quiet=True, verbose=False, rich=False, endpoints="base", max_endpoints=3, meta_probe=False, specs=10, github_repos=3, github_queries=config.GITHUB_DEFAULT_QUERIES, sources="public-apis,builtin", max_js=5, apk_deep=False, cancel_event=None, log=lambda m: print(m))
    entries,_ = sources.discover(args)
    entries = filter_entries(entries, args)
    entries = tester.run(entries, args)
    working = [e for e in entries if (e.get("test") or {}).get("status")=="working"][:n]
    return working

if __name__ == "__main__":
    # Telegram polling (requires TELEGRAM_BOT_TOKEN)
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        import requests
        print("Telegram bot polling...")
        # Minimal long-poll example
        offset=0
        while True:
            r=requests.get(f"https://api.telegram.org/bot{token}/getUpdates?offset={offset+1}&timeout=10").json()
            for upd in r.get("result",[]):
                offset=upd["update_id"]
                text=(upd.get("message") or {}).get("text") or ""
                chat=(upd.get("message") or {}).get("chat",{}).get("id")
                if text.lower().startswith("hunt") or "api" in text.lower():
                    kw=text.split()[-1] if len(text.split())>1 else "weather"
                    working=hunt_sync(kw)
                    reply="\n".join([f"✅ {e['name']}: {e.get('base_url') or e['url']}" for e in working]) or "No working APIs found"
                    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id":chat,"text":f"🔍 {kw} — {len(working)} working APIs:\n"+reply})
    else:
        print(hunt_sync("weather",3))
