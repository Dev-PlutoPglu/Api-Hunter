 "use client";
import { useEffect, useState, useMemo } from "react";
import { Search, Bell, Github, Moon, Sun, Menu, X, ChevronRight, Play, Square, RotateCcw, Star, Crown, Gift, CheckCircle2, AlertCircle, Sparkles, ExternalLink, Copy, Download, History, Settings, Target, Sparkles as SparkIcon, Flame, Shield, Rocket } from "lucide-react";
import { HuntStats } from "@/components/HuntStats";
import { ProgressDonut } from "@/components/ProgressDonut";
import { ResultsTable } from "@/components/ResultsTable";
import { ReversePremium } from "@/components/ReversePremium";

const STATUS_LABEL: any = { working: "WORKING", auth_required: "KEY NEEDED", rate_limited: "RATE LIMITED", needs_params: "NEEDS PARAMS", not_working: "DEAD", error: "ERROR", skipped: "SKIPPED" };
const DUMMY = [
  { name: "Cat Facts", source: "public-apis", auth: "none", category: "Animals", url: "https://catfact.ninja", base_url: "https://catfact.ninja", test: { status: "working", http_status: 200, latency_ms: 212, sample: '{"fact":"Cats sleep 70%"}' }, metadata_apis: [], secrets: [], endpoints: ["/fact"] },
  { name: "PokeAPI", source: "apisguru", auth: "none", category: "Games", url: "https://pokeapi.co/api/v2/pokemon", base_url: "https://pokeapi.co", test: { status: "working", http_status: 200, latency_ms: 340 }, metadata_apis: [{ kind: "openapi3", url: "https://pokeapi.co/api/v2/openapi.json", base_url: "https://pokeapi.co", endpoints: ["/pokemon"] }], secrets: [], endpoints: [] },
  { name: "WeatherAPI", source: "github", auth: "apiKey", category: "Weather", url: "https://api.weatherapi.com/v1/current.json", base_url: "https://api.weatherapi.com", test: { status: "auth_required", http_status: 401, latency_ms: 180 }, metadata_apis: [], secrets: [{ type: "apiKey", key: "sk-****abcd", evidence: "apiKey=sk-1234" }], endpoints: [] },
  { name: "CoinGecko", source: "builtin", auth: "none", category: "Crypto", url: "https://api.coingecko.com/api/v3/ping", base_url: "https://api.coingecko.com", test: { status: "working", http_status: 200, latency_ms: 420 }, metadata_apis: [], secrets: [], endpoints: [] },
  { name: "GitHub API", source: "public-apis", auth: "OAuth", category: "Dev", url: "https://api.github.com/users", base_url: "https://api.github.com", test: { status: "rate_limited", http_status: 429, latency_ms: 98 }, metadata_apis: [], secrets: [], endpoints: [] },
  { name: "Dead API", source: "apisguru", auth: "none", category: "Test", url: "https://dead.example.com/api", base_url: "https://dead.example.com", test: { status: "not_working", http_status: 500, latency_ms: 1200 }, metadata_apis: [], secrets: [], endpoints: [] },
];

export default function Page(){
  const [theme,setTheme]=useState("light"); const [mobileNav,setMobileNav]=useState(false);
  const [huntState,setHuntState]=useState<any>({ status:"idle", stage:"", counts:{discovered:0,tested:0,working:0,dead:0,meta:0,secrets:0}, elapsed:0, logs:[] });
  const [results,setResults]=useState<any[]>(DUMMY);
  const [filterStatus,setFilterStatus]=useState("all"); const [searchText,setSearchText]=useState("");
  const [sortKey,setSortKey]=useState("status"); const [sortDir,setSortDir]=useState(1);
  const [selected,setSelected]=useState<any>(null); const [toast,setToast]=useState<any>(null);
  const [mode,setMode]=useState("hunt"); const [keyword,setKeyword]=useState(""); const [category,setCategory]=useState(""); const [auth,setAuth]=useState("any");
  const [limit,setLimit]=useState(40); const [workers,setWorkers]=useState(12); const [timeout,setTimeoutVal]=useState(10);
  const [endpoints,setEndpoints]=useState("base"); const [specs,setSpecs]=useState(30);
  const [sources,setSources]=useState<string[]>(["public-apis","apisguru","github","builtin"]);
  const [headers,setHeaders]=useState(""); const [insecure,setInsecure]=useState(false); const [metaProbe,setMetaProbe]=useState(true); const [apkDeep,setApkDeep]=useState(false);
  const [target,setTarget]=useState(""); const [revUrl,setRevUrl]=useState(""); const [revMaxJs,setRevMaxJs]=useState(15); const [revApkPath,setRevApkPath]=useState(""); const [revApkDeep,setRevApkDeep]=useState(false);
  const [assistantInput,setAssistantInput]=useState(""); const [assistantExpanded,setAssistantExpanded]=useState(true);
  const [assistantMsgs,setAssistantMsgs]=useState<any[]>([{role:"assistant",text:"Hi! I'm your API Hunter assistant. Ask me about hunts or reverse-engineering."}]);

  useEffect(()=>{ const s=localStorage.getItem("ah-theme")||"light"; setTheme(s); document.documentElement.setAttribute("data-theme",s);
    const fetchState=()=>{ fetch("/api/state").then(r=>r.ok?r.json():Promise.reject()).then(s=>{setHuntState(s); return fetch("/api/results").then(r=>r.json())}).then(r=>{if(Array.isArray(r)&&r.length) setResults(r)}).catch(()=>{}); };
    fetchState(); const id=setInterval(fetchState,1500);
    try{ const es=new EventSource("/events"); es.onmessage=ev=>{ try{ const m=JSON.parse(ev.data); if(m.type==="state") setHuntState(m.data);}catch{}} }catch{}
    return()=>clearInterval(id);
  },[]);
  const toggleTheme=()=>{ const t=theme==="light"?"dark":"light"; setTheme(t); document.documentElement.setAttribute("data-theme",t); localStorage.setItem("ah-theme",t); };
  const showToast=(title:string,sub?:string,tone="info")=>{ setToast({title,sub,tone}); setTimeout(()=>setToast(null),4000); };
  const currentConfig=()=>({ mode,target,keyword,category,auth,limit,workers,timeout,endpoints,specs,sources:sources.join(","),headers,insecure,meta_probe:metaProbe,apk_deep:apkDeep,outdir:"apihunter_out",max_js:revMaxJs });
  const startHunt=(cfg:any)=>{
    const rev=String(cfg.mode||"").includes("reverse"); if(rev&&!cfg.target){showToast("Check form","Enter target URL or APK path","err");return;} if(!rev&&!cfg.keyword&&!cfg.category){showToast("Check form","Enter keyword (e.g. weather, crypto)","err");return;}
    fetch("/api/start",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(cfg)}).then(r=>r.json().then(j=>({ok:r.ok,j}))).then(({ok})=>{
      if(!ok) showToast("Backend offline (demo)","Showing dummy data — run 'python3 apihunter.py ui' for live hunts","info"); else showToast("Hunt started",cfg.keyword||cfg.target||cfg.mode,"ok");
      if(!ok){ setHuntState({status:"running",stage:"hunting catalogs (github + internet)",counts:{discovered:1462,tested:12,working:3,dead:1,meta:1,secrets:1},elapsed:2,logs:[{ts:"12:00:01",msg:"[*] hunting source: public-apis"},{ts:"12:00:02",msg:"[*] 1462 unique APIs discovered"}]});
        setTimeout(()=>{ setHuntState((s:any)=>({...s,status:"done",stage:"✓ ready",counts:{discovered:12,tested:12,working:4,dead:2,meta:1,secrets:1},elapsed:8})); showToast("Hunt finished (demo)","12 APIs · 4 working · 1 metadata","ok"); },2500);
      }
    }).catch(()=>showToast("Backend offline (demo)","Start Python backend for live hunts","info"));
  };

  const countsByStatus=useMemo(()=>{ const c:Record<string,number>={}; results.forEach(r=>{ const s=(r.test||{}).status||"skipped"; c[s]=(c[s]||0)+1; }); return c; },[results]);
  const filtered=useMemo(()=>{
    let rows=results.map((e,i)=>({e,i})); if(filterStatus!=="all") rows=rows.filter(r=>((r.e.test||{}).status||"skipped")===filterStatus);
    if(searchText){ const q=searchText.toLowerCase(); rows=rows.filter(r=>((r.e.name||"")+" "+(r.e.url||"")+" "+(r.e.category||"")).toLowerCase().includes(q)); }
    const val=(r:any)=>{ const t=r.e.test||{}; switch(sortKey){ case "http": return t.http_status||0; case "ms":return t.latency_ms||0; case "status":return t.status||"zzz"; case "url":return (r.e.base_url||r.e.url||"").toLowerCase(); default:return String(r.e[sortKey]||"").toLowerCase(); } };
    rows.sort((a,b)=>{ const x=val(a),y=val(b); return (x>y?1:x<y?-1:0)*sortDir; }); return rows;
  },[results,filterStatus,searchText,sortKey,sortDir]);

  return (
    <div className="min-h-screen bg-[var(--bg)] p-2 sm:p-4 lg:p-6 flex justify-center">
      <div className="w-full max-w-[1440px] bg-[var(--card-bg)] rounded-[var(--radius-xl)] shadow-[var(--shadow-lg)] border border-white/60 dark:border-white/5 overflow-hidden">
        <nav className="flex items-center justify-between gap-3 px-5 sm:px-7 py-4 border-b border-[var(--border-soft)] sticky top-0 bg-[var(--card-bg)]/80 backdrop-blur-xl z-20">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] grid place-items-center text-white shadow-md"><Search size={18}/></div>
            <div className="hidden sm:block"><div className="text-[15px] font-extrabold leading-none flex items-center gap-1.5">API <span className="bg-gradient-to-r from-[var(--primary)] to-[var(--secondary)] bg-clip-text text-transparent">HUNTER</span> <span className="hidden lg:inline text-[11px] font-bold bg-[var(--primary-soft)] text-[var(--primary)] px-2 py-0.5 rounded-full">v1.1</span></div><div className="text-[11px] font-medium text-[var(--text-faint)] flex items-center gap-1"><span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"/> localhost</div></div>
            <button onClick={()=>setMobileNav(!mobileNav)} className="sm:hidden p-2 rounded-xl border border-[var(--border)] ml-1">{mobileNav?<X size={16}/>:<Menu size={16}/>}</button>
          </div>
          <div className="hidden lg:flex items-center gap-1 bg-[var(--card-bg-soft)] p-1 rounded-full border border-[var(--border)]">
            {[{label:"Hunt",active:true},{label:"Reverse",active:false},{label:"Reports",active:false},{label:"Docs",active:false}].map(item=>(
              <a key={item.label} href="#" className={`px-4 py-1.5 rounded-full text-[13px] font-semibold ${item.active?"bg-[var(--card-bg)] shadow-sm border border-[var(--border)]":"text-[var(--text-dim)]"}`}>{item.label}</a>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden md:flex items-center gap-2 bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-full px-3 py-1.5">
              <Search size={14} className="text-[var(--text-faint)]"/><input placeholder="Search APIs…" value={searchText} onChange={e=>setSearchText(e.target.value)} className="bg-transparent outline-none text-[13px] w-32 lg:w-40 placeholder:text-[var(--text-faint)]"/><span className="hidden lg:inline text-[10px] font-bold bg-[var(--card-bg)] border border-[var(--border)] px-1.5 py-0.5 rounded-md text-[var(--text-faint)]">⌘K</span>
            </div>
            <div className={`hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold tracking-wide border ${huntState.status==="running"?"bg-sky-50 text-sky-700 border-sky-200 animate-pulse":"bg-[var(--card-bg-soft)] text-[var(--text-dim)] border-[var(--border)]"}`}>
              <span className={`w-2 h-2 rounded-full ${huntState.status==="running"?"bg-sky-500 animate-pulse":"bg-[var(--text-faint)]"}`}/> {huntState.status||"idle"}
            </div>
            <button onClick={toggleTheme} className="w-9 h-9 grid place-items-center rounded-full bg-[var(--card-bg-soft)] border border-[var(--border)]">{theme==="light"?<Moon size={16}/>:<Sun size={16}/>}</button>
            <a href="https://github.com/Dev-PlutoPglu/api-hunter" target="_blank" className="hidden sm:grid w-9 h-9 place-items-center rounded-full bg-[var(--card-bg)] border border-[var(--border)]"><Github size={16}/></a>
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-600 to-indigo-600 grid place-items-center text-white font-bold text-xs border-2 border-white shadow">AH</div>
          </div>
        </nav>

        <div className="px-5 sm:px-7 py-6 border-b border-[var(--border-soft)] bg-gradient-to-b from-[var(--card-bg)] to-[var(--card-bg-soft)]/30">
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-5">
            <div>
              <div className="flex items-center gap-2 text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)] mb-2"><span>Home</span><ChevronRight size={12} className="opacity-40"/><span className="text-[var(--primary)]">API Hunter</span><span className="hidden sm:inline-flex items-center gap-1 ml-2 bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full text-[10px]"><Star size={10}/> Best API Discovery</span></div>
              <h1 className="text-[26px] sm:text-[32px] font-black tracking-tight leading-none flex items-center gap-3"><span className="bg-gradient-to-r from-[var(--primary)] via-violet-600 to-[var(--secondary)] bg-clip-text text-transparent">Hunt. Reverse. Test.</span><span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-full"><span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"/> LIVE</span></h1>
              <div className="mt-3 flex gap-2"><input id="nlInput" placeholder="💬 Natural language: e.g. 'mujhe free weather apis chahiye jo fast ho' — AI will parse" className="flex-1 bg-[var(--card-bg)] border border-[var(--border)] rounded-full px-4 py-2.5 text-[13px] placeholder:text-[var(--text-faint)]" onKeyDown={e=>{ if(e.key==='Enter'){ const v=(e.target as HTMLInputElement).value.trim(); if(v){ fetch("/api/start",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...currentConfig(), natural_language:v})}).then(()=>showToast("AI Hunt started",v,"ok")); (e.target as HTMLInputElement).value=""; }}}} /><button onClick={()=>{ const el=document.getElementById("nlInput") as HTMLInputElement; const v=el?.value.trim(); if(v){ fetch("/api/start",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...currentConfig(), natural_language:v})}).then(()=>showToast("AI Hunt started",v,"ok")); el.value=""; }}} className="bg-gradient-to-r from-violet-600 to-indigo-600 text-white px-5 py-2.5 rounded-full text-[13px] font-bold">AI Hunt ✨</button></div>
              <p className="text-[13px] text-[var(--text-dim)] mt-2 max-w-[680px]">Discover 2500+ free APIs from GitHub & internet, reverse-engineer hidden APIs from any website or APK, test every endpoint live.</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="hidden sm:flex items-center gap-1 text-[12px] bg-[var(--card-bg)] border border-[var(--border)] rounded-full px-3 py-1.5"><span className="w-2 h-2 bg-emerald-500 rounded-full"/> {countsByStatus["working"]||0} working <span className="w-px h-4 bg-[var(--border)] mx-1"/> {results.length} total</div>
              <button onClick={()=>startHunt(currentConfig())} disabled={huntState.status==="running"} className="inline-flex items-center gap-2 bg-[var(--primary)] text-white px-5 py-2.5 rounded-full text-[13px] font-bold shadow hover:bg-[var(--primary-hover)] disabled:opacity-50"><Play size={16}/> Start Hunt</button>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 mt-5 pt-5 border-t border-[var(--border-soft)]">
            <span className="text-[12px] font-semibold text-[var(--text-faint)]">Mode</span>
            <select value={mode} onChange={e=>setMode(e.target.value)} className="bg-[var(--card-bg)] border border-[var(--border)] rounded-full px-3 py-1.5 text-[13px] font-medium"><option value="hunt">Full hunt — catalogs + test + metadata</option><option value="discover">Discover only</option><option value="reverse-web">Reverse-web (JS mining)</option><option value="reverse-apk">Reverse-apk (DEX mining)</option></select>
            <div className="hidden sm:flex items-center gap-1 text-[12px] bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-full px-2 py-1">
              {["public-apis","apisguru","github","builtin"].map(s=>(
                <label key={s} className={`px-2.5 py-1 rounded-full text-[11px] font-bold border cursor-pointer ${sources.includes(s)?"bg-[var(--primary)] text-white border-[var(--primary)]":"bg-[var(--card-bg)] text-[var(--text-dim)] border-transparent"}`}><input type="checkbox" checked={sources.includes(s)} onChange={e=>setSources(p=>e.target.checked?[...p,s]:p.filter(x=>x!==s))} className="hidden"/>{s}</label>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-[#f8f9fb] dark:bg-[#0b1120]/40 p-3 sm:p-5 lg:p-6 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex bg-[var(--card-bg)] border border-[var(--border)] rounded-full p-1 gap-1">
              {["Overview","Live Hunt","Reports"].map((t,i)=>(<button key={t} className={`px-4 py-1.5 rounded-full text-[12px] font-bold ${i===1?"bg-[var(--text)] text-white dark:bg-white dark:text-black shadow":"text-[var(--text-dim)]"}`}>{t}</button>))}
            </div>
            <div className="text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)]">✨ Premium • Customizable via CSS variables</div>
          </div>

          <HuntStats counts={huntState.counts} />

          <ProgressDonut huntState={huntState} countsByStatus={countsByStatus} resultsCount={results.length} />

          <div className="bg-[var(--card-bg)] border border-[var(--border)] rounded-[var(--radius)] p-5 shadow-[var(--shadow-card)]">
            <h3 className="text-[13px] font-bold flex items-center gap-2 mb-4">⚙️ Hunt Controls <span className="text-[10px] font-bold bg-[var(--primary-soft)] text-[var(--primary)] px-2 py-0.5 rounded-full">LIVE</span></h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div><label className="text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)]">Keyword</label><input value={keyword} onChange={e=>setKeyword(e.target.value)} placeholder="weather, crypto, anime…" className="mt-1 w-full bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl px-3 py-2 text-[13px]"/></div>
              <div><label className="text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)]">Category</label><input value={category} onChange={e=>setCategory(e.target.value)} placeholder="any" className="mt-1 w-full bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl px-3 py-2 text-[13px]"/></div>
              <div><label className="text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)]">Auth</label><select value={auth} onChange={e=>setAuth(e.target.value)} className="mt-1 w-full bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl px-3 py-2 text-[13px]"><option>any</option><option>none</option><option>apiKey</option><option>OAuth</option></select></div>
              <div><label className="text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)]">Limit</label><input type="number" value={limit} onChange={e=>setLimit(parseInt(e.target.value)||0)} className="mt-1 w-full bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl px-3 py-2 text-[13px]"/></div>
              <div><label className="text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)]">Workers</label><input type="number" value={workers} onChange={e=>setWorkers(parseInt(e.target.value)||12)} className="mt-1 w-full bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl px-3 py-2 text-[13px]"/></div>
              <div><label className="text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)]">Timeout</label><input type="number" value={timeout} onChange={e=>setTimeoutVal(parseInt(e.target.value)||10)} className="mt-1 w-full bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl px-3 py-2 text-[13px]"/></div>
              <div><label className="text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)]">Endpoints</label><select value={endpoints} onChange={e=>setEndpoints(e.target.value)} className="mt-1 w-full bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl px-3 py-2 text-[13px]"><option value="base">base URLs</option><option value="deep">deep (spec)</option><option value="off">off</option></select></div>
              <div><label className="text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)]">Specs</label><input type="number" value={specs} onChange={e=>setSpecs(parseInt(e.target.value)||30)} className="mt-1 w-full bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl px-3 py-2 text-[13px]"/></div>
            </div>
            {mode.includes("reverse") && (<div className="mt-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 rounded-xl p-3 flex items-center gap-3"><input value={target} onChange={e=>setTarget(e.target.value)} placeholder={mode==="reverse-web"?"https://example.com":"./app.apk"} className="flex-1 bg-white border border-[var(--border)] rounded-full px-4 py-2 text-[13px]"/><span className="text-[11px] text-amber-700 hidden sm:block">Target required</span></div>)}
            <div className="mt-4 space-y-3">
              <textarea value={headers} onChange={e=>setHeaders(e.target.value)} placeholder="Headers (one per line, e.g. X-Api-Key: abc)" rows={2} className="w-full bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl px-3 py-2 text-[12px] font-mono"/>
              <div className="flex flex-wrap gap-2">
                <button onClick={()=>startHunt(currentConfig())} disabled={huntState.status==="running"} className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 bg-[var(--primary)] text-white px-6 py-2.5 rounded-full text-[13px] font-bold shadow disabled:opacity-50"><Play size={16}/> Start Hunt</button>
                <button onClick={()=>fetch("/api/stop",{method:"POST"})} className="px-5 py-2.5 rounded-full border text-[13px] font-bold bg-[var(--card-bg)] border-[var(--border)]"><Square size={14} className="inline mr-1"/> Stop</button>
                <button onClick={()=>fetch("/api/retry-dead",{method:"POST"}).then(()=>showToast("Retrying","Re-queued dead APIs","ok"))} className="px-5 py-2.5 rounded-full bg-[var(--card-bg)] border border-[var(--border)] text-[13px] font-bold"><RotateCcw size={14} className="inline mr-1"/> Retry Failed</button>
              </div>
            </div>
          </div>

          <ReversePremium revUrl={revUrl} setRevUrl={setRevUrl} revMaxJs={revMaxJs} setRevMaxJs={setRevMaxJs} revApkPath={revApkPath} setRevApkPath={setRevApkPath} revApkDeep={revApkDeep} setRevApkDeep={setRevApkDeep} onMineWeb={()=>startHunt({...currentConfig(),mode:"reverse-web",target:revUrl,max_js:revMaxJs})} onMineApk={()=>startHunt({...currentConfig(),mode:"reverse-apk",target:revApkPath,apk_deep:revApkDeep})} />

          <ResultsTable rows={filtered} countsByStatus={countsByStatus} filterStatus={filterStatus} setFilterStatus={setFilterStatus} searchText={searchText} setSearchText={setSearchText} sortKey={sortKey} setSortKey={setSortKey} sortDir={sortDir} setSortDir={setSortDir} onRowClick={setSelected} onCopyWorking={()=>{ const u=results.filter(r=>(r.test||{}).status==="working").map(r=>r.base_url||r.url).join("\n"); navigator.clipboard?.writeText(u); showToast("Copied",`${results.filter(r=>r.test?.status==="working").length} URLs copied`,"ok"); }} total={results.length} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="bg-[var(--card-bg)] border border-[var(--border)] rounded-[var(--radius)] p-5 shadow-[var(--shadow-card)]">
              <h3 className="text-[13px] font-bold mb-3">📦 Metadata & Secrets</h3>
              <div className="space-y-3 max-h-[260px] overflow-auto pr-1">
                {results.flatMap(r=>(r.metadata_apis||[]).map((m:any)=>({r,m}))).slice(0,4).map(({r,m}:any,i:number)=>(
                  <div key={i} className="bg-[var(--card-bg-soft)] border border-[var(--border-soft)] rounded-xl p-3"><div className="text-[10px] font-black uppercase text-fuchsia-600">{m.kind}</div><div className="text-[13px] font-semibold">{r.name}</div><div className="text-[11px] font-mono text-[var(--text-dim)] truncate">{m.url}</div></div>
                ))}
                {results.flatMap(r=>r.secrets||[]).slice(0,2).map((s:any,i:number)=>(
                  <div key={`s-${i}`} className="bg-amber-50 border border-amber-200 rounded-xl p-3"><div className="text-[10px] font-black uppercase text-amber-700">{s.type}</div><div className="text-[11px] font-mono">{s.key?.slice(0,10)}… masked</div></div>
                ))}
                {results.flatMap(r=>r.metadata_apis||[]).length===0 && results.flatMap(r=>r.secrets||[]).length===0 && <div className="text-[12px] text-[var(--text-faint)] text-center py-6">Metadata appears after hunting</div>}
              </div>
            </div>
            <div className="bg-[var(--card-bg)] border border-[var(--border)] rounded-[var(--radius)] p-5 shadow-[var(--shadow-card)]">
              <h3 className="text-[13px] font-bold mb-3 flex items-center gap-2"><History size={14}/> Hunt History</h3>
              <div className="space-y-2">
                {[{mode:"hunt",kw:"weather",total:40,working:8,time:"2m ago"},{mode:"reverse-web",kw:"example.com",total:12,working:3,time:"1h ago"},{mode:"reverse-apk",kw:"app.apk",total:18,working:5,time:"3h ago"}].map((h,i)=>(
                  <div key={i} className="flex items-center gap-3 bg-[var(--card-bg-soft)] border border-[var(--border-soft)] rounded-xl px-3 py-2.5"><span className="px-2 py-0.5 rounded-full bg-[var(--primary-soft)] text-[var(--primary)] text-[10px] font-black uppercase">{h.mode}</span><div className="flex-1 min-w-0"><div className="text-[12px] font-semibold truncate">{h.kw}</div><div className="text-[11px] text-[var(--text-faint)]">{h.time}</div></div><div className="text-[11px] font-bold text-right">{h.total} APIs<br/><span className="text-emerald-600">{h.working} working</span></div></div>
                ))}
              </div>
            </div>
            <div className="bg-[var(--card-bg)] border border-[var(--border)] rounded-[var(--radius)] p-5 shadow-[var(--shadow-card)]">
              <h3 className="text-[13px] font-bold mb-3 flex items-center gap-2"><Download size={14}/> Reports</h3>
              <div className="grid grid-cols-2 gap-2">
                {[{label:"JSON",desc:"Machine"},{label:"CSV",desc:"Spreadsheet"},{label:"MD",desc:"Human"},{label:"Catalog",desc:"Raw"}].map(r=>(
                  <a key={r.label} href="#" className="bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl p-3 hover:border-[var(--primary)]"><div className="text-[12px] font-bold">{r.label}</div><div className="text-[11px] text-[var(--text-faint)]">{r.desc}</div></a>
                ))}
              </div>
              <div className="mt-4 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-xl p-4 text-white"><div className="text-[11px] font-black uppercase flex items-center gap-1"><Crown size={12}/> PRO TIP</div><div className="text-[12px] mt-1">Add <code className="bg-white/20 px-1.5 py-0.5 rounded">-H "X-Api-Key: …"</code> to test protected APIs</div></div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2 rounded-[var(--radius)] overflow-hidden border border-violet-900/20 shadow-[var(--shadow-lg)] relative isolate">
              <div className="absolute inset-0 bg-gradient-to-br from-[#1e1b4b] via-[#312e81] to-[#4338ca]"/><div className="absolute -top-12 -right-12 w-64 h-64 bg-white/10 rounded-full blur-3xl"/><div className="absolute -bottom-10 -left-10 w-56 h-56 bg-cyan-400/20 rounded-full blur-3xl"/>
              <div className="relative p-6 sm:p-7 text-white">
                <div className="flex flex-wrap gap-2 mb-3"><span className="inline-flex items-center gap-1.5 text-[11px] font-black uppercase bg-white/15 border border-white/20 px-3 py-1 rounded-full"><Rocket size={12}/> MOST LOVED HUNTER</span><span className="text-[11px] font-bold bg-emerald-400 text-emerald-950 px-2.5 py-1 rounded-full">⭐ 1.2k stars</span></div>
                <h3 className="text-[22px] font-black leading-tight">The only API hunter you’ll ever need</h3>
                <p className="text-white/85 text-[13px] mt-2 max-w-[560px]">Hunt free APIs, reverse-engineer hidden endpoints from any site or APK, test live, hunt OpenAPI/Swagger — terminal + premium dashboard. <b>Offline-capable, no vendor lock-in.</b></p>
                <div className="flex flex-wrap gap-3 mt-5"><a href="https://github.com/Dev-PlutoPglu/api-hunter" target="_blank" className="inline-flex items-center gap-2 bg-white text-[#1e1b4b] font-bold text-[13px] px-5 py-2.5 rounded-full">Star on GitHub →</a><button onClick={()=>showToast("Sponsor","Thanks! Link in README","ok")} className="inline-flex items-center gap-2 bg-white/10 border border-white/20 text-white font-semibold text-[13px] px-5 py-2.5 rounded-full"><Gift size={14}/> Sponsor</button></div>
              </div>
            </div>
            <div className="bg-[var(--card-bg)] border border-[var(--border)] rounded-[var(--radius)] shadow-[var(--shadow-card)] flex flex-col overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b border-[var(--border-soft)]"><h3 className="text-[13px] font-bold flex items-center gap-2"><span className="w-7 h-7 rounded-full bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] grid place-items-center text-white">●</span> Assistant <span className="text-[10px] font-black uppercase bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full">LIVE</span></h3><button onClick={()=>setAssistantExpanded(!assistantExpanded)} className="w-7 h-7 grid place-items-center rounded-full hover:bg-[var(--card-bg-soft)] border">{assistantExpanded?"▲":"▼"}</button></div>
              <div className={`px-4 flex-1 space-y-3 overflow-auto ${assistantExpanded?"max-h-[220px] opacity-100 py-3":"max-h-0 opacity-0"}`}>
                {assistantMsgs.map((m:any,i:number)=>(<div key={i} className={`flex gap-2 ${m.role==="user"?"justify-end":"justify-start"}`}><div className={`max-w-[80%] rounded-2xl px-3 py-2 text-[13px] ${m.role==="user"?"bg-[var(--primary)] text-white rounded-br-md":"bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-bl-md"}`}>{m.text}</div></div>))}
                <div className="flex gap-1.5 pt-1">{["Find weather APIs","How to reverse APK?","Show working only"].map(chip=>(<button key={chip} onClick={()=>setAssistantInput(chip)} className="text-[11px] font-semibold bg-[var(--card-bg)] border border-[var(--border)] px-3 py-1 rounded-full">{chip}</button>))}</div>
              </div>
              <div className="p-3 bg-[var(--card-bg-soft)] border-t border-[var(--border-soft)]">
                <div className="bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl p-2 flex items-end gap-2 focus-within:border-[var(--primary)]">
                  <textarea value={assistantInput} onChange={e=>setAssistantInput(e.target.value)} onFocus={()=>setAssistantExpanded(true)} onKeyDown={e=>{ if(e.key==="Enter"&&!e.shiftKey){ e.preventDefault(); const v=assistantInput.trim(); if(v){ setAssistantMsgs(m=>[...m,{role:"user",text:v},{role:"assistant",text:`Got it — hunting for "${v.slice(0,40)}". Demo mode; connect backend for live.`}]); setAssistantInput(""); }}}} placeholder="Ask anything… (e.g. ‘find crypto APIs’)" rows={assistantExpanded?2:1} className="flex-1 bg-transparent outline-none resize-none text-[13px] placeholder:text-[var(--text-faint)] py-1.5 min-h-[24px]"/>
                  <button onClick={()=>{ const v=assistantInput.trim(); if(!v) return; setAssistantMsgs(m=>[...m,{role:"user",text:v},{role:"assistant",text:`Hunting for "${v.slice(0,40)}" — demo. Start backend for live.`}]); setAssistantInput(""); }} className="w-8 h-8 grid place-items-center rounded-full bg-[var(--primary)] text-white">▶</button>
                </div>
                <div className="text-[11px] text-[var(--text-faint)] mt-2 text-center">Press Enter to send • Backend when running</div>
              </div>
            </div>
          </div>
        </div>

        <div className="px-5 sm:px-7 py-4 bg-[var(--card-bg-soft)] border-t border-[var(--border-soft)] flex flex-wrap items-center justify-between gap-3">
          <div className="text-[11px] text-[var(--text-faint)] font-medium">🔍 API Hunter — customizable via <code className="bg-[var(--card-bg)] border border-[var(--border)] px-1.5 py-0.5 rounded">--primary --secondary --bg --card-bg --border</code></div>
          <div className="flex items-center gap-2"><span className="text-[11px] font-black uppercase text-[var(--text-faint)]">Theme</span><div className="flex bg-[var(--card-bg)] border border-[var(--border)] rounded-full p-1">{["Light","Dark"].map(t=>(<button key={t} onClick={toggleTheme} className={`px-3 py-1 rounded-full text-[12px] font-bold ${((theme==="light"&&t==="Light")||(theme==="dark"&&t==="Dark"))?"bg-[var(--text)] text-white dark:bg-white dark:text-black":"text-[var(--text-dim)]"}`}>{t}</button>))}</div></div>
        </div>
      </div>

      {selected && (
        <div onClick={()=>setSelected(null)} className="fixed inset-0 bg-black/50 backdrop-blur-sm grid place-items-center p-4 z-50">
          <div onClick={e=>e.stopPropagation()} className="bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl max-w-[720px] w-full max-h-[85vh] overflow-auto p-6 shadow-2xl">
            <div className="flex justify-between"><h2 className="text-[18px] font-black">{selected.name}</h2><button onClick={()=>setSelected(null)} className="w-8 h-8 grid place-items-center rounded-full border">✕</button></div>
            <div className="text-[12px] text-[var(--text-dim)] break-all">{selected.url}</div>
            <div className="mt-4 grid grid-cols-2 gap-3 text-[12px]">
              <div className="bg-[var(--card-bg-soft)] border rounded-xl p-3"><div className="text-[11px] font-bold text-[var(--text-faint)]">STATUS</div><div className="font-bold">{STATUS_LABEL[selected.test?.status]||selected.test?.status}</div><div className="font-mono text-[var(--text-dim)]">HTTP {selected.test?.http_status??"-"} • {selected.test?.latency_ms?`${Math.round(selected.test.latency_ms)}ms`:"-"}</div></div>
              <div className="bg-[var(--card-bg-soft)] border rounded-xl p-3"><div className="text-[11px] font-bold text-[var(--text-faint)]">AUTH</div><div className="font-bold">{selected.auth}</div><div className="text-[var(--text-dim)]">{selected.category}</div></div>
            </div>
            {selected.test?.sample && <pre className="mt-4 bg-[#0b1220] text-slate-300 p-4 rounded-xl text-[11px] overflow-auto max-h-[240px]">{String(selected.test.sample).slice(0,1200)}</pre>}
          </div>
        </div>
      )}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 bg-[var(--card-bg)] border border-[var(--border)] shadow-[var(--shadow-lg)] rounded-2xl p-4 flex gap-3 max-w-[360px]">
          <div className={`w-9 h-9 rounded-xl grid place-items-center text-white ${toast.tone==="ok"?"bg-emerald-500":toast.tone==="err"?"bg-red-500":"bg-[var(--primary)]"}`}>●</div>
          <div className="flex-1"><div className="text-[13px] font-bold">{toast.title}</div>{toast.sub&&<div className="text-[12px] text-[var(--text-dim)]">{toast.sub}</div>}</div>
          <button onClick={()=>setToast(null)} className="text-[var(--text-faint)]">✕</button>
        </div>
      )}
    </div>
  );
}
