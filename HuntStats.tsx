"use client";
export function HuntStats({ counts }: { counts: any }) {
  const items = [
    { label: "Discovered", value: counts?.discovered || 0, sub: "unique APIs", color: "text-violet-600 bg-violet-50 border-violet-100" },
    { label: "Tested", value: counts?.tested || 0, sub: "endpoints hit", color: "text-sky-600 bg-sky-50 border-sky-100" },
    { label: "Working", value: counts?.working || 0, sub: "2xx responses", color: "text-emerald-600 bg-emerald-50 border-emerald-100" },
    { label: "Dead / Error", value: counts?.dead || 0, sub: "failed", color: "text-red-600 bg-red-50 border-red-100" },
    { label: "Metadata APIs", value: counts?.meta || 0, sub: "OpenAPI/Swagger", color: "text-fuchsia-600 bg-fuchsia-50 border-fuchsia-100" },
    { label: "Secrets", value: counts?.secrets || 0, sub: "masked keys", color: "text-amber-600 bg-amber-50 border-amber-100" },
  ];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map(s => (
        <div key={s.label} className="bg-[var(--card-bg)] border border-[var(--border)] rounded-[var(--radius)] p-4 shadow-[var(--shadow-card)] card-transition hover-lift">
          <div className={`w-9 h-9 rounded-xl border grid place-items-center ${s.color} dark:bg-white/5 text-[16px]`}>●</div>
          <div className="text-[11px] font-bold tracking-widest uppercase text-[var(--text-faint)] mt-3">{s.label}</div>
          <div className="text-[22px] font-black tracking-tight">{s.value}</div>
          <div className="text-[11px] text-[var(--text-dim)]">{s.sub}</div>
        </div>
      ))}
    </div>
  );
}
