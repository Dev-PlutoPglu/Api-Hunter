"use client";
export function ResultsTable({ rows, countsByStatus, filterStatus, setFilterStatus, searchText, setSearchText, sortKey, setSortKey, sortDir, setSortDir, onRowClick, onCopyWorking, total }: any) {
  const STATUS_LABEL: any = { working: "WORKING", auth_required: "KEY NEEDED", rate_limited: "RATE LIMITED", needs_params: "NEEDS PARAMS", not_working: "DEAD", error: "ERROR", skipped: "SKIPPED" };
  const STATUS_COLOR: any = { working: "#10b981", auth_required: "#f59e0b", rate_limited: "#3b82f6", needs_params: "#3b82f6", not_working: "#ef4444", error: "#ef4444", skipped: "#94a3b8" };
  return (
    <div className="bg-[var(--card-bg)] border border-[var(--border)] rounded-[var(--radius)] shadow-[var(--shadow-card)] overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-5 border-b border-[var(--border-soft)]">
        <h3 className="text-[13px] font-bold flex items-center gap-2">▦ Results <span className="text-[11px] font-medium bg-[var(--card-bg-soft)] border border-[var(--border)] px-2 py-0.5 rounded-full">{total} APIs</span></h3>
        <div className="flex items-center gap-2">
          <button onClick={onCopyWorking} className="px-3 py-1.5 rounded-full bg-[var(--card-bg-soft)] border border-[var(--border)] text-[12px] font-semibold">Copy working</button>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 p-4 bg-[var(--card-bg-soft)]/50 border-b border-[var(--border-soft)]">
        <div className="flex flex-wrap gap-1.5">
          {["all", "working", "auth_required", "rate_limited", "needs_params", "not_working", "error"].map(k => {
            const cnt = k === "all" ? total : countsByStatus[k] || 0;
            if (k !== "all" && cnt === 0) return null;
            return <button key={k} onClick={() => setFilterStatus(k)} className={`px-3 py-1 rounded-full text-[11px] font-bold border transition ${filterStatus === k ? "bg-[var(--primary)] text-white border-[var(--primary)] shadow" : "bg-[var(--card-bg)] text-[var(--text-dim)] border-[var(--border)]"}`}>{k === "all" ? `All ${cnt}` : `${STATUS_LABEL[k]} ${cnt}`}</button>;
          })}
        </div>
        <div className="ml-auto flex items-center gap-2 bg-[var(--card-bg)] border border-[var(--border)] rounded-full px-3 py-1.5">
          <span className="text-[var(--text-faint)]">⌕</span>
          <input value={searchText} onChange={e => setSearchText(e.target.value)} placeholder="Filter by name/url/category…" className="bg-transparent outline-none text-[12px] w-40 sm:w-56 placeholder:text-[var(--text-faint)]" />
        </div>
      </div>
      <div className="overflow-auto max-h-[520px]">
        <table className="w-full text-[13px]">
          <thead className="sticky top-0 bg-[var(--card-bg-soft)] backdrop-blur border-b border-[var(--border)] z-10">
            <tr className="text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)]">
              {(["name", "source", "auth", "status", "http", "ms", "url"] as const).map(k => (
                <th key={k} onClick={() => { setSortKey(k); setSortDir(sortKey === k ? -sortDir : 1); }} className="text-left px-4 py-3 cursor-pointer hover:text-[var(--primary)] whitespace-nowrap">{k} ↕</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(({ e, i }: any) => {
              const t = e.test || {};
              return (
                <tr key={i} onClick={() => onRowClick(e)} className="border-b border-[var(--border-soft)] hover:bg-[var(--primary-soft)] cursor-pointer transition">
                  <td className="px-4 py-3 font-semibold">{e.name}</td>
                  <td className="px-4 py-3 text-[var(--text-dim)] font-mono text-[11px]">{e.source}</td>
                  <td className="px-4 py-3"><span className="px-2 py-0.5 rounded-full bg-[var(--card-bg-soft)] border border-[var(--border)] text-[11px] font-semibold">{e.auth || "?"}</span></td>
                  <td className="px-4 py-3"><span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-black tracking-wide text-white" style={{ background: STATUS_COLOR[t.status || "skipped"] }}>{STATUS_LABEL[t.status || "skipped"] || t.status}</span></td>
                  <td className="px-4 py-3 font-mono text-center">{t.http_status ?? "-"}</td>
                  <td className="px-4 py-3 font-mono text-center">{t.latency_ms ? Math.round(t.latency_ms) : "-"}</td>
                  <td className="px-4 py-3 font-mono text-[11px] max-w-[220px] truncate">{e.base_url || e.url}</td>
                </tr>
              );
            })}
            {rows.length === 0 && <tr><td colSpan={7} className="text-center py-12 text-[13px] text-[var(--text-faint)]">No APIs match filter — try a hunt!</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
