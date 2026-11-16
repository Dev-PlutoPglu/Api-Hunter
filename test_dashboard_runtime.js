/* Runtime smoke test for the API Hunter premium dashboard.

   Runs the real dashboard <script> (which is wrapped in an IIFE) against a fake
   DOM using Node's `vm`, feeds it realistic hunt payloads, and asserts that:
     1. the script evaluates with no parse/init errors,
     2. the boot path (state poll -> results poll -> render) works,
     3. every render path (state / results / detail modal / donut / history /
        meta cards / secrets / downloads / logs / chips) runs without throwing,
     4. user-controlled strings are HTML-escaped (no HTML injection),
     5. no template-literal artifacts leak into rendered output.

   Usage:  node test_dashboard_runtime.js
*/
const fs = require("fs");
const vm = require("vm");
const path = require("path");

const HTML_PATH = path.join(__dirname, "dashboard.html");
const html = fs.readFileSync(HTML_PATH, "utf8");

/* ── extract the dashboard script ─────────────────────────────── */
const scriptBlocks = html.split("<script>");
if (scriptBlocks.length < 2) {
  console.error("FAIL: no <script> block found in dashboard.html");
  process.exit(1);
}
let js = scriptBlocks[scriptBlocks.length - 1].split("</script>")[0];
if (!/\S/.test(js)) {
  console.error("FAIL: extracted script is empty");
  process.exit(1);
}

/* The script is wrapped in `(function(){ ... })();`, so internals are not
   globals. Inject a test hook immediately before the closing `})();`.
   Only names that really exist in the script are hooked. */
const HOOK =
  "window.__test = { renderState, renderResults, renderHistory, renderMetaCards," +
  " renderDownloads, renderDonut, showDetail, currentConfig, filteredResults, esc," +
  " api, toast, startWith, statusTag, applyConfig, loadPresetList, syncModeUI," +
  " validateConfig, get results() { return results; } };";
const closeIdx = js.lastIndexOf("})();");
if (closeIdx < 0) {
  console.error("FAIL: could not find IIFE terminator `})();`");
  process.exit(1);
}
js = js.slice(0, closeIdx) + HOOK + "\n" + js.slice(closeIdx);

/* ── fake DOM ─────────────────────────────────────────────────── */
function makeEl(id) {
  const el = {
    id,
    textContent: "",
    innerHTML: "",
    value: "",
    checked: false,
    disabled: false,
    hidden: false,
    className: "",
    style: {},
    dataset: {},
    children: [],
    addEventListener() {},
    removeEventListener() {},
    appendChild(c) {
      this.children.push(c);
      return c;
    },
    remove() {},
    setAttribute() {},
    getAttribute() {
      return "";
    },
    closest() {
      return null;
    },
    querySelector() {
      return null;
    },
    querySelectorAll() {
      return [];
    },
    select() {},
    focus() {},
    blur() {},
    scrollTop: 0,
    scrollHeight: 0,
  };
  /* A working classList backed by className, so hidden/visible assertions are
     real rather than a stub that always answers false. */
  el.classList = {
    add(...cs) {
      cs.forEach((c) => {
        if (!el.classList.contains(c)) el.className = (el.className + " " + c).trim();
      });
    },
    remove(...cs) {
      el.className = el.className.split(/\s+/).filter((c) => c && cs.indexOf(c) === -1).join(" ");
    },
    contains(c) {
      return el.className.split(/\s+/).indexOf(c) !== -1;
    },
    toggle(c, force) {
      const on = force === undefined ? !el.classList.contains(c) : !!force;
      if (on) el.classList.add(c);
      else el.classList.remove(c);
      return on;
    },
  };
  return el;
}

const els = {};
[...html.matchAll(/id="([^"]+)"/g)].forEach((m) => (els[m[1]] = makeEl(m[1])));

const noop = () => {};
const documentShim = {
  documentElement: {
    getAttribute() {
      return "dark";
    },
    setAttribute() {},
    dataset: {},
  },
  getElementById: (id) => els[id] || (els[id] = makeEl(id)),
  querySelectorAll: () => [],
  createElement: () => makeEl("dyn"),
  addEventListener: noop,
  execCommand: () => true,
  body: { appendChild: noop, removeChild: noop },
};

/* ── realistic payloads ───────────────────────────────────────── */
const RESULTS = [
  {
    name: "Cat Facts",
    url: "https://catfact.ninja/facts",
    base_url: "https://catfact.ninja",
    source: "reverse-apk:synthetic-app-real.apk",
    auth: "none",
    category: "Animals",
    description: "facts about cats",
    https: true,
    test: {
      status: "working",
      http_status: 200,
      latency_ms: 153.4,
      content_type: "application/json",
      sample: '{"fact":"cats are great"}',
      endpoint_tests: [
        { path: "/facts", status: "working" },
        { path: "/breeds", status: "working" },
      ],
    },
    metadata: { server: "cloudflare", powered_by: "", ratelimit: {}, json: { type: "object", keys: ["fact"] } },
    metadata_apis: [
      { kind: "openapi3", url: "https://catfact.ninja/docs?api-docs.json", base_url: null, endpoints: ["/facts", "/breeds"] },
    ],
    secrets: [],
  },
  {
    name: "AccuWeather",
    url: "https://developer.accuweather.com/apis",
    source: "public-apis",
    auth: "apiKey",
    category: "Weather",
    test: { status: "auth_required", http_status: 403, latency_ms: 210.1 },
    secrets: [{ type: "generic-api-key", key: "sk_live_abcdef1234567890", evidence: "classes.dex" }],
  },
  {
    name: "Broken API",
    url: "https://dead.example.org/api",
    source: "apis.guru",
    auth: "unknown",
    test: { status: "error", http_status: null, latency_ms: null, error: "ConnectionError" },
  },
  {
    name: "No <b>tags</b> & 'quotes' \"here\"",
    url: "https://x.test/v1?a=1&b=2",
    source: "github:foo/bar",
    auth: "OAuth",
    test: { status: "rate_limited", http_status: 429, latency_ms: 99.9 },
  },
  {
    name: "Needs Params",
    url: "https://api.example.org/search",
    source: "builtin",
    auth: "none",
    test: { status: "needs_params", http_status: 400, latency_ms: 12.5 },
  },
  {
    name: "Frankfurter",
    url: "https://api.frankfurter.app/latest",
    base_url: "https://api.frankfurter.app",
    source: "reverse-apk:synthetic-app-real.apk",
    auth: "none",
    test: {
      status: "working",
      http_status: 200,
      latency_ms: 88.2,
      content_type: "application/json",
      sample: '{"base":"EUR"}',
    },
    metadata_apis: [
      { kind: "openapi3", url: "https://api.frankfurter.app/openapi.json", endpoints: ["/latest", "/currencies"] },
    ],
    secrets: [{ type: "google-api-key", key: "AIzaSyTESTTESTTESTTESTTEST", evidence: "res/values/strings.xml" }],
  },
];

const HISTORY = [
  { id: "run-1", ts: 1794764033, mode: "hunt", summary: { total: 40, by_status: { working: 25 }, metadata_apis: 0 }, config: { keyword: "anime" } },
  { id: "run-2", ts: 1794763900, mode: "reverse-apk", summary: { total: 9, by_status: { working: 7 }, metadata_apis: 5 }, config: { apk: "tools/synthetic-app-real.apk" } },
];

const STATE = {
  status: "done",
  stage: "writing reports",
  started_at: 1794764000,
  finished_at: 1794764033,
  elapsed: 33.3,
  config: { mode: "hunt", keyword: "test" },
  counts: { discovered: 8098, tested: 40, working: 25, auth_required: 3, dead: 11, meta: 5, secrets: 2 },
  logs: [
    { ts: "17:40:17", msg: "[*] hunting <source> & done" },
    { ts: "17:40:30", msg: "tested X: working" },
  ],
  summary: { total: 40, by_status: { working: 25, auth_required: 3, error: 9 }, metadata_apis: 5, secrets: 2 },
  reports: { json: "apihunter_out/api-hunt-report.json", csv: "apihunter_out/api-hunt-report.csv" },
  error: null,
  total_results: RESULTS.length,
  viewing_history: null,
  automation: { enabled: true, interval_min: 30, next_run: 1794765000 },
  webhook: "",
  history: HISTORY,
};

/* ── sandbox ──────────────────────────────────────────────────── */
let stateCalls = 0;
let resultsCalls = 0;
const sandbox = {
  console,
  addEventListener: noop,
  removeEventListener: noop,
  dispatchEvent: () => true,
  matchMedia: () => ({ matches: false, addEventListener: noop, addListener: noop }),
  scrollTo: noop,
  requestAnimationFrame: (fn) => setTimeout(fn, 0),
  getSelection: () => ({ removeAllRanges: noop, toString: () => "" }),
  confirm: () => true,
  alert: noop,
  setTimeout,
  clearTimeout,
  /* Fire each interval callback once, asynchronously, so the dashboard's
     1500 ms poll loop is exercised without waiting in real time. */
  setInterval: (fn) => {
    setTimeout(() => {
      try {
        fn();
      } catch (e) {
        console.log("  FAIL interval callback threw -> " + e.message);
        failures++;
      }
    }, 0);
    return 1;
  },
  clearInterval: noop,
  prompt: () => null,
  navigator: { clipboard: { writeText: () => Promise.resolve() }, userAgent: "node-test" },
  document: documentShim,
  localStorage: { getItem: () => null, setItem: noop, removeItem: noop },
  fetch: (p) => {
    const s = String(p);
    if (s.includes("/api/samples")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(["tools/synthetic-app.apk", "tools/synthetic-app-real.apk"]),
      });
    }
    if (s.includes("/api/state")) {
      stateCalls++;
      return Promise.resolve({ ok: true, json: () => Promise.resolve(STATE) });
    }
    if (s.includes("/api/results")) {
      resultsCalls++;
      return Promise.resolve({ ok: true, json: () => Promise.resolve(RESULTS) });
    }
    if (s.includes("/api/history")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ entries: RESULTS }) });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  },
  EventSource: function () {
    return { onerror: null, onmessage: null, close: noop };
  },
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.self = sandbox;
sandbox.URL = Object.assign(function () {}, { createObjectURL: () => "blob:x", revokeObjectURL: noop });
vm.createContext(sandbox);

/* ── assertions ───────────────────────────────────────────────── */
let failures = 0;
function check(name, fn) {
  try {
    fn();
    console.log("  OK   " + name);
  } catch (e) {
    failures++;
    console.log("  FAIL " + name + " -> " + e.message);
  }
}
function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

console.log(
  "dashboard runtime smoke test — " + html.length + " bytes html / " + js.length + " bytes js\n"
);

try {
  vm.runInContext(js, sandbox, { filename: "dashboard.js" });
  console.log("  OK   script evaluated (no parse/init errors)");
} catch (e) {
  console.log("  FAIL script evaluation -> " + e.message);
  console.log("\n1 FAILURE");
  process.exit(1);
}

const T = sandbox.__test;
check("test hook installed", () => assert(T, "window.__test missing"));
for (const fn of [
  "renderState",
  "renderResults",
  "renderHistory",
  "renderMetaCards",
  "renderDownloads",
  "renderDonut",
  "showDetail",
  "currentConfig",
  "filteredResults",
  "esc",
  "api",
  "toast",
  "startWith",
  "statusTag",
  "applyConfig",
  "loadPresetList",
  "syncModeUI",
  "validateConfig",
]) {
  check("exposes " + fn, () => assert(typeof T[fn] === "function", "missing or not a function"));
}

/* Realistic form values so currentConfig() returns a usable config. */
Object.assign(els["mode"], { value: "hunt" });
Object.assign(els["target"], { value: "" });
Object.assign(els["keyword"], { value: "weather" });
Object.assign(els["category"], { value: "" });
Object.assign(els["auth"], { value: "any" });
Object.assign(els["limit"], { value: "40" });
Object.assign(els["workers"], { value: "12" });
Object.assign(els["timeout"], { value: "10" });
Object.assign(els["endpoints"], { value: "base" });
Object.assign(els["specs"], { value: "30" });
Object.assign(els["headers"], { value: "" });
Object.assign(els["meta_probe"], { checked: true });
Object.assign(els["apk_deep"], { checked: false });
Object.assign(els["insecure"], { checked: false });

/* Let the async boot fetches + first poll tick settle. */
setTimeout(() => {
  check("boot poll fetched /api/state", () => assert(stateCalls >= 1, "state never fetched"));
  check("boot poll fetched /api/results", () => assert(resultsCalls >= 1, "results never fetched"));
  check("boot poll populated results", () => {
    assert(Array.isArray(T.results), "results is not an array");
    assert(T.results.length === RESULTS.length, "expected " + RESULTS.length + " got " + T.results.length);
  });
  check("sample APK datalist rendered with labels", () => {
    const h2 = els["sampleApks"].innerHTML;
    assert(h2.includes("synthetic-app.apk"), "sample apk option missing value");
    assert((h2.match(/<option/g) || []).length === 2, "expected 2 <option> elements");
  });

  /* ── render paths ─────────────────────────────────────────── */
  check("renderState(done)", () => T.renderState(STATE));
  check("renderState(running)", () =>
    T.renderState({ ...STATE, status: "running", stage: "testing endpoints", finished_at: null }));
  check("renderState(idle, empty counts/logs/history)", () =>
    T.renderState({ status: "idle", logs: [], counts: {}, config: {}, history: [] }));
  check("renderState(minimal {})", () => T.renderState({}));
  check("renderState(viewing history)", () => T.renderState({ ...STATE, viewing_history: "run-1" }));
  check("renderResults()", () => T.renderResults());
  check("renderResults() twice (idempotent)", () => T.renderResults());
  check("renderHistory([])", () => T.renderHistory([]));
  check("renderHistory(list)", () => T.renderHistory(HISTORY));
  check("renderMetaCards()", () => T.renderMetaCards());
  check("renderDownloads()", () => T.renderDownloads());
  check("renderDonut(counts)", () => T.renderDonut({ working: 25, error: 9, auth_required: 3 }));
  check("renderDonut({})", () => T.renderDonut({}));
  for (let i = 0; i < RESULTS.length; i++) check("showDetail(" + i + ")", () => T.showDetail(i));
  check("showDetail(out of range)", () => T.showDetail(999));
  check("showDetail(-1)", () => T.showDetail(-1));
  check("currentConfig()", () => {
    const c = T.currentConfig();
    assert(c && typeof c === "object", "config not an object");
    assert(c.mode === "hunt", "unexpected mode: " + c.mode);
    assert(c.keyword === "weather", "unexpected keyword: " + c.keyword);
    assert(c.limit === 40, "unexpected limit: " + c.limit);
  });
  check("applyConfig() round-trip", () => {
    T.applyConfig({ mode: "reverse-web", target: "https://x.test", keyword: "k", limit: 7 });
    const c = T.currentConfig();
    assert(c.mode === "reverse-web", "mode not applied");
    assert(c.target === "https://x.test", "target not applied");
    assert(c.limit === 7, "limit not applied");
    T.applyConfig({ mode: "hunt", keyword: "weather", limit: 40 });
  });
  check("filteredResults()", () => {
    const r = T.filteredResults();
    assert(Array.isArray(r), "not an array");
    assert(r.length === RESULTS.length, "expected " + RESULTS.length + " got " + r.length);
  });
  check("esc() escapes", () => {
    assert(T.esc('<b>&"\'') === "&lt;b&gt;&amp;&quot;&#39;", "unexpected esc output");
  });
  check("esc(null/undefined safe)", () => {
    assert(T.esc(null) === "", "esc(null) not empty");
    assert(T.esc(undefined) === "", "esc(undefined) not empty");
  });
  check("statusTag()", () => assert(T.statusTag("working").includes("WORKING"), "no WORKING label"));

  /* ── XSS / escaping ───────────────────────────────────────── */
  const rowsHtml = els["rows"].innerHTML;
  check("rows rendered", () => assert(rowsHtml && rowsHtml.length > 50, "rows innerHTML empty"));
  check("table escapes <b> in name", () => {
    assert(!rowsHtml.includes("<b>tags</b>"), "unescaped HTML injected into table");
    assert(rowsHtml.includes("&lt;b&gt;tags&lt;/b&gt;"), "expected escaped form in table");
  });
  check("no template-literal artifacts in rows", () => {
    assert(!rowsHtml.includes("${"), "unresolved template literal in rows");
    assert(!rowsHtml.includes("[object"), "[object ...] leaked into rows");
    assert(!rowsHtml.includes("undefined</td>"), "bare undefined in rows");
  });
  check("row count matches results", () => {
    assert((rowsHtml.match(/class="row"/g) || []).length === RESULTS.length, "row count mismatch");
  });
  check("detail modal escapes", () => {
    T.showDetail(3);
    const h2 = els["mBody"].textContent;
    assert(!h2.includes("<b>tags</b>"), "unescaped HTML in detail modal");
    assert(!h2.includes("${"), "template literal in detail modal");
  });
  check("donut rendered", () => {
    T.renderResults();
    assert((els["donut"].innerHTML || "").includes("<circle"), "no <circle> in donut");
  });
  check("legend rendered", () =>
    assert((els["legend"].innerHTML || "").length > 10, "legend innerHTML empty"));
  check("history rendered", () => {
    T.renderState(STATE);
    const h2 = els["history"].innerHTML;
    assert(h2.includes("hitem"), "no history rows");
    assert(h2.includes("run-1"), "history id missing");
  });
  check("chips rendered", () =>
    assert((els["statusChips"].innerHTML || "").includes("chip"), "no chips rendered"));
  check("downloads rendered", () => {
    const h2 = els["dls"].innerHTML;
    assert(h2.includes("api-hunt-report.json"), "json report link missing");
    assert(h2.includes("api-hunt-report.csv"), "csv report link missing");
    assert(h2.includes("api-hunt-report.md"), "md report link missing");
  });
  check("logs rendered", () => {
    const h2 = els["log"].innerHTML;
    assert(h2.length > 10, "log innerHTML empty");
    assert(!h2.includes("<source>"), "log HTML not escaped");
  });
  check("meta + secret cards rendered, secrets masked", () => {
    const h2 = els["metaCards"].innerHTML;
    assert(h2.includes("card"), "no meta cards");
    assert(h2.includes("openapi3"), "metadata kind missing");
    assert(!h2.includes("sk_live_abcdef1234567890"), "secret value NOT masked");
    assert(h2.includes("(masked)"), "masked marker missing");
  });
  check("progress stats populated", () => {
    assert(els["c-discovered"].textContent === 8098, "discovered stat wrong: " + els["c-discovered"].textContent);
    assert(els["c-working"].textContent === 25, "working stat wrong");
    assert(els["c-meta"].textContent === 5, "meta stat wrong");
  });
  check("progress bar width set", () =>
    assert(String(els["progressBar"].style.width).includes("%"), "progress bar width not set"));

  /* ── the reported bug: keyword hunts must not demand an APK/URL ── */
  check("hunt mode with keyword only is accepted", () => {
    T.applyConfig({ mode: "hunt", keyword: "anime", limit: 40 });
    const cfg = T.currentConfig();
    assert(cfg.mode === "hunt", "mode wrong");
    assert(cfg.target === "", "target should be empty for hunt mode");
    assert(T.validateConfig(cfg) === null, "keyword hunt wrongly rejected: " + T.validateConfig(cfg));
  });
  check("discover mode with keyword only is accepted", () => {
    T.applyConfig({ mode: "discover", keyword: "weather" });
    assert(T.validateConfig(T.currentConfig()) === null, "discover wrongly rejected");
  });
  check("hunt mode with a category but no keyword is accepted", () => {
    T.applyConfig({ mode: "hunt", keyword: "", category: "Weather" });
    assert(T.validateConfig(T.currentConfig()) === null, "category-only hunt wrongly rejected");
  });
  check("hunt mode with neither keyword nor category is rejected", () => {
    T.applyConfig({ mode: "hunt", keyword: "", category: "" });
    const msg = T.validateConfig(T.currentConfig());
    assert(msg && /keyword/i.test(msg), "expected a keyword hint, got: " + msg);
  });
  check("reverse-web without target is rejected", () => {
    T.applyConfig({ mode: "reverse-web", target: "" });
    const msg = T.validateConfig(T.currentConfig());
    assert(msg && /target/i.test(msg), "expected a target hint, got: " + msg);
  });
  check("reverse-web with a URL is accepted", () => {
    T.applyConfig({ mode: "reverse-web", target: "https://catfact.ninja" });
    assert(T.validateConfig(T.currentConfig()) === null, "valid reverse-web rejected");
  });
  check("reverse-web with a non-URL is rejected", () => {
    T.applyConfig({ mode: "reverse-web", target: "catfact.ninja" });
    const msg = T.validateConfig(T.currentConfig());
    assert(msg && /URL/i.test(msg), "expected a URL hint, got: " + msg);
  });
  check("reverse-apk with a non-APK is rejected", () => {
    T.applyConfig({ mode: "reverse-apk", target: "https://example.com/app" });
    const msg = T.validateConfig(T.currentConfig());
    assert(msg && /\.apk/i.test(msg), "expected an .apk hint, got: " + msg);
  });
  check("reverse-apk with an .apk path is accepted", () => {
    T.applyConfig({ mode: "reverse-apk", target: "tools/synthetic-app.apk" });
    assert(T.validateConfig(T.currentConfig()) === null, "valid reverse-apk rejected");
  });
  check("syncModeUI hides the target box in hunt mode", () => {
    T.applyConfig({ mode: "hunt" });
    T.syncModeUI();
    assert(els["targetBox"].classList.contains("hidden"), "target box visible in hunt mode");
    assert(!els["keywordBox"].classList.contains("hidden"), "keyword box hidden in hunt mode");
  });
  check("syncModeUI hides the keyword box in reverse mode", () => {
    T.applyConfig({ mode: "reverse-apk" });
    T.syncModeUI();
    assert(!els["targetBox"].classList.contains("hidden"), "target box hidden in reverse mode");
    assert(els["keywordBox"].classList.contains("hidden"), "keyword box visible in reverse mode");
    T.applyConfig({ mode: "hunt", keyword: "anime" });
    T.syncModeUI();
  });

  /* ── sweep: no exceptions anywhere ────────────────────────── */
  check("sweep: every entry through showDetail + filter", () => {
    T.results.forEach((r, i) => {
      T.showDetail(i);
      T.filteredResults();
    });
    T.renderResults();
  });

  console.log(failures ? "\n" + failures + " FAILURE(S)" : "\nALL RUNTIME CHECKS PASSED");
  process.exit(failures ? 1 : 0);
}, 150);
