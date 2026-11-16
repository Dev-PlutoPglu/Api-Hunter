"""AI power: natural language hunt, docs generator, self-healing tests."""
from __future__ import annotations
import os, re, json

def natural_language_to_config(text: str, fallback_keyword: str = "") -> dict:
    """
    Dashboard: 'mujhe free weather apis chahiye jo fast ho' -> {keyword:'weather', auth:'none', category:'Weather'}
    Uses LLM if OPENAI_API_KEY/GROQ_API_KEY set, else heuristic.
    """
    text_low = text.lower()
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            import requests
            base = "https://api.groq.com/openai/v1" if os.environ.get("GROQ_API_KEY") else "https://api.openai.com/v1"
            model = "llama-3.1-8b-instant" if os.environ.get("GROQ_API_KEY") else "gpt-4o-mini"
            prompt = f"""Parse user hunt request into JSON. User: "{text}". Return ONLY JSON with keys: keyword, category, auth (any/none/apiKey/OAuth), limit (number). Example: {{"keyword":"weather","category":"Weather","auth":"none","limit":20}}"""
            r = requests.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 120}, timeout=10)
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                m = re.search(r"\{[^}]+\}", content, re.S)
                if m:
                    parsed = json.loads(m.group(0))
                    return {"keyword": parsed.get("keyword") or fallback_keyword, "category": parsed.get("category") or "", "auth": parsed.get("auth") or "any", "limit": int(parsed.get("limit") or 20)}
        except Exception:
            pass
    # Heuristic fallback — no key needed
    keyword = fallback_keyword
    # Extract keyword: look for known categories or last noun
    cat_map = {"weather": "Weather", "crypto": "Cryptocurrency", "anime": "Anime", "food": "Food", "game": "Games", "music": "Music", "news": "News", "finance": "Finance", "ai": "AI / ML", "health": "Health"}
    for k, cat in cat_map.items():
        if k in text_low:
            keyword = k
            break
    if not keyword:
        # fallback: longest word
        words = [w for w in re.findall(r"[a-zA-Z]{3,}", text) if w.lower() not in ("mujhe","chahiye","free","apis","jo","fast","ho","need","want")]
        if words:
            keyword = max(words, key=len).lower()
    auth = "none" if "free" in text_low or "without key" in text_low else "any"
    category = next((cat for k, cat in cat_map.items() if k in text_low), "")
    limit = 20
    if "fast" in text_low:
        limit = 30  # will sort by latency later
    return {"keyword": keyword, "category": category, "auth": auth, "limit": limit}

def generate_docs_for_api(entry: dict) -> dict:
    """AI docs generator: returns curl + python + js snippets for a working API."""
    name = entry.get("name") or "API"
    url = entry.get("base_url") or entry.get("url") or ""
    # Try LLM for richer docs
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            import requests
            base = "https://api.groq.com/openai/v1" if os.environ.get("GROQ_API_KEY") else "https://api.openai.com/v1"
            model = "llama-3.1-8b-instant" if os.environ.get("GROQ_API_KEY") else "gpt-4o-mini"
            prompt = f"Generate short API docs for {name} at {url}. Include curl, Python requests, and JS fetch examples. Keep under 200 words."
            r = requests.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 300}, timeout=12)
            if r.status_code == 200:
                docs = r.json()["choices"][0]["message"]["content"]
                return {"ai_docs": docs, "curl": f'curl -i "{url}"', "python": f'import requests\nr = requests.get("{url}")\nprint(r.json())', "js": f'fetch("{url}").then(r=>r.json()).then(console.log)'}
        except Exception:
            pass
    # Deterministic fallback — always works offline
    return {
        "curl": f'curl -i "{url}"',
        "curl_auth": f'curl -H "X-Api-Key: YOUR_KEY" "{url}"',
        "python": f'import requests\n# {name}\nresp = requests.get("{url}")\nprint(resp.status_code, resp.json() if resp.headers.get("content-type","").startswith("application/json") else resp.text[:500])',
        "js": f'// {name}\nfetch("{url}")\n  .then(r => r.json())\n  .then(data => console.log(data))\n  .catch(console.error);',
        "note": "Replace YOUR_KEY if auth required. Generated offline (set OPENAI_API_KEY for AI-enhanced docs)."
    }

def self_healing_test(entry: dict, args) -> dict | None:
    """
    Self-healing: if NEEDS_PARAMS (400/422), LLM generates valid JSON body and retries POST.
    Returns new probe result or None.
    """
    test = entry.get("test") or {}
    if test.get("status") != "needs_params":
        return None
    path = entry.get("url") or entry.get("base_url") or ""
    # Ask LLM for body
    from .tester import probe
    import os, json
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
    body = None
    if api_key:
        try:
            import requests, re
            base = "https://api.groq.com/openai/v1" if os.environ.get("GROQ_API_KEY") else "https://api.openai.com/v1"
            model = "llama-3.1-8b-instant" if os.environ.get("GROQ_API_KEY") else "gpt-4o-mini"
            prompt = f"API {entry.get('name')} at {path} returned 400 needs params. Generate minimal valid JSON POST body. Return ONLY JSON. Example: {{\"name\":\"test\",\"email\":\"test@example.com\"}}"
            r = requests.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 150}, timeout=10)
            if r.status_code == 200:
                txt = r.json()["choices"][0]["message"]["content"]
                m = re.search(r"\{[^}]+\}", txt, re.S)
                if m:
                    body = json.loads(m.group(0))
        except Exception:
            pass
    if not body:
        # Heuristic fallback
        body = {"name": "test", "q": "test", "id": 1, "page": 1}
    # Retry as POST with JSON
    try:
        import requests, time
        url = entry.get("base_url") or entry.get("url")
        r = requests.post(url, json=body, timeout=args.timeout, headers={**getattr(args, "headers", {}), "Content-Type": "application/json"})
        # Re-classify
        from .tester import classify
        status = classify(r.status_code, None)
        return {"healed": True, "method": "POST", "body": body, "http_status": r.status_code, "status": status, "sample": r.text[:400]}
    except Exception as exc:
        return {"healed": False, "error": str(exc), "body": body}
