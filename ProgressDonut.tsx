"use client";
export function ProgressDonut({ huntState, countsByStatus, resultsCount }: { huntState: any; countsByStatus: any; resultsCount: number }) {
  const STATUS_LABEL: any = { working: "WORKING", auth_required: "KEY NEEDED", rate_limited: "RATE LIMITED", needs_params: "NEEDS PARAMS", not_working: "DEAD", error: "ERROR", skipped: "SKIPPED" };
  const STATUS_COLOR: any = { working: "#10b981", auth_required: "#f59e0b", rate_limited: "#3b82f6", needs_params: "#3b82f6", not_working: "#ef4444", error: "#ef4444", skipped: "#94a3b8" };
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 bg-[var(--card-bg)] border border-[var(--border)] rounded-[var(--radius)] p-5 shadow-[var(--shadow-card)]">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[13px] font-bold flex items-center gap-2">● Progress</h3>
          <span className="text-[11px] font-bold bg-[var(--primary-soft)] text-[var(--primary)] px-2.5 py-1 rounded-full border border-[var(--primary)]/10">{huntState.stage || "idle"}</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          {[
            { k: "discovered", label: "Discovered" },
            { k: "tested", label: "Tested" },
            { k: "working", label: "Working" },
            { k: "elapsed", label: "Elapsed", suffix: "s" },
          ].map(m => (
            <div key={m.k} className="bg-[var(--card-bg-soft)] border border-[var(--border-soft)] rounded-xl p-3 text-center">
              <div className="text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)]">{m.label}</div>
              <div className="text-[18px] font-black">{m.k === "elapsed" ? `${huntState.elapsed || 0}${(m as any).suffix}` : huntState.counts?.[m.k] ?? 0}</div>
            </div>
          ))}
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-[12px] font-medium"><span className="text-[var(--text-dim)]">{huntState.stage || "Waiting…"}</span><span>{Math.min(100, Math.round(((huntState.counts?.tested || 0) / Math.max(1, huntState.counts?.discovered || 1)) * 100))}%</span></div>
          <div className="h-2 bg-[var(--card-bg-soft)] border border-[var(--border-soft)] rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-[var(--primary)] to-[var(--secondary)] transition-all duration-700" style={{ width: `${Math.min(100, ((huntState.counts?.tested || 0) / Math.max(1, huntState.counts?.discovered || 1)) * 100)}%` }} />
          </div>
          <div className="bg-[#0b1220] border border-slate-800 rounded-xl p-3 h-28 overflow-auto font-mono text-[11px] leading-relaxed text-slate-300">
            {(huntState.logs?.length ? huntState.logs : [{ ts: "12:00:01", msg: "[*] hunting source: public-apis" }, { ts: "12:00:02", msg: "[*] 1462 unique APIs discovered" }]).map((l: any, i: number) => (
              <div key={i}><span className="text-slate-500">{l.ts}</span> {l.msg}</div>
            ))}
          </div>
        </div>
      </div>
      <div className="bg-[var(--card-bg)] border border-[var(--border)] rounded-[var(--radius)] p-5 shadow-[var(--shadow-card)]">
        <h3 className="text-[13px] font-bold flex items-center gap-2 mb-4">◉ Status Distribution</h3>
        <div className="flex flex-col items-center gap-4">
          <div className="relative w-36 h-36">
            <svg width="144" height="144" viewBox="0 0 144 144" className="-rotate-90">
              <circle cx="72" cy="72" r="58" fill="none" stroke="var(--border-soft)" strokeWidth="14" />
              {(() => {
                const entries = Object.entries(countsByStatus).filter(([, v]) => (v as number) > 0);
                const total = (entries.reduce((a, [, v]) => a + (v as number), 0) as number) || 1;
                const C = 2 * Math.PI * 58;
                let off = 0;
                return entries.map(([k, v]) => {
                  const frac = (v as number) / total;
                  const seg = frac * C;
                  const dash = `${Math.max(0, seg - 2)} ${C}`;
                  const el = <circle key={k} cx="72" cy="72" r="58" fill="none" stroke={STATUS_COLOR[k] || "#94a3b8"} strokeWidth="14" strokeDasharray={dash} strokeDashoffset={-off * C} strokeLinecap="round" />;
                  off += frac;
                  return el;
                });
              })()}
            </svg>
            <div className="absolute inset-0 grid place-items-center">
              <div className="text-center"><div className="text-[22px] font-black">{resultsCount}</div><div className="text-[10px] font-bold tracking-widest uppercase text-[var(--text-faint)]">APIs</div></div>
            </div>
          </div>
          <div className="w-full space-y-2">
            {Object.entries(countsByStatus).map(([k, v]) => (
              <div key={k} className="flex items-center gap-2 text-[12px]">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: STATUS_COLOR[k] || "#94a3b8" }} />
                <span className="flex-1 font-medium">{STATUS_LABEL[k] || k}</span>
                <span className="font-bold">{v as number}</span>
              </div>
            ))}
            {resultsCount === 0 && <div className="text-[12px] text-[var(--text-faint)] text-center">No data — start a hunt</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
