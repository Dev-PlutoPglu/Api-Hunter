"use client";
export function ReversePremium({ revUrl, setRevUrl, revMaxJs, setRevMaxJs, revApkPath, setRevApkPath, revApkDeep, setRevApkDeep, onMineWeb, onMineApk }: any) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div className="bg-[var(--card-bg)] border border-[var(--border)] rounded-[var(--radius)] p-5 shadow-[var(--shadow-card)] card-transition hover-lift">
        <h3 className="text-[13px] font-bold flex items-center gap-2">🌐 Website <span className="text-[10px] font-bold bg-sky-50 text-sky-700 border border-sky-200 px-2 py-0.5 rounded-full">JS MINING</span></h3>
        <p className="text-[12px] text-[var(--text-dim)] mt-1">Mines <code className="bg-[var(--card-bg-soft)] px-1.5 py-0.5 rounded text-[11px]">fetch/axios/XHR, baseURL, /api/v1…, GraphQL</code></p>
        <input value={revUrl} onChange={e => setRevUrl(e.target.value)} placeholder="https://example.com" className="mt-3 w-full bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl px-3 py-2.5 text-[13px] focus:outline-none focus:border-[var(--primary)]" />
        <div className="flex gap-2 mt-3">
          <div className="flex-1"><label className="text-[11px] font-bold text-[var(--text-faint)]">JS assets</label><input type="number" value={revMaxJs} onChange={e => setRevMaxJs(parseInt(e.target.value) || 15)} className="mt-1 w-full bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl px-3 py-2 text-[13px]" /></div>
          <button onClick={onMineWeb} className="self-end bg-gradient-to-r from-sky-600 to-cyan-500 text-white px-5 py-2.5 rounded-full text-[13px] font-bold hover:opacity-90">Mine APIs ▶</button>
        </div>
      </div>
      <div className="bg-[var(--card-bg)] border border-[var(--border)] rounded-[var(--radius)] p-5 shadow-[var(--shadow-card)] card-transition hover-lift">
        <h3 className="text-[13px] font-bold flex items-center gap-2">📱 APK <span className="text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full">DEX MINING</span></h3>
        <p className="text-[12px] text-[var(--text-dim)] mt-1">Unzips APK, mines DEX bytecode, <code className="bg-[var(--card-bg-soft)] px-1.5 py-0.5 rounded text-[11px]">AndroidManifest, resources.arsc</code></p>
        <input value={revApkPath} onChange={e => setRevApkPath(e.target.value)} placeholder="./app.apk" list="sampleApks" className="mt-3 w-full bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-xl px-3 py-2.5 text-[13px] focus:outline-none focus:border-[var(--primary)]" />
        <datalist id="sampleApks"><option value="tools/synthetic-app.apk" /><option value="tools/synthetic-app-real.apk" /></datalist>
        <div className="flex items-center justify-between mt-3">
          <label className="flex items-center gap-1.5 text-[12px] font-medium"><input type="checkbox" checked={revApkDeep} onChange={e => setRevApkDeep(e.target.checked)} /> apktool/jadx deep scan</label>
          <button onClick={onMineApk} className="bg-gradient-to-r from-emerald-600 to-teal-500 text-white px-5 py-2.5 rounded-full text-[13px] font-bold hover:opacity-90">Mine APIs ▶</button>
        </div>
      </div>
    </div>
  );
}
