"use client";
import { MoreHorizontal, TrendingUp, TrendingDown, ArrowUpRight } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";

/* — Sparkline SVG — */
export function Sparkline({ color = "var(--primary)", points = [30,45,35,60,48,70,58,82] }: { color?: string; points?: number[] }) {
  const w = 100, h = 36;
  const max = Math.max(...points), min = Math.min(...points);
  const range = max - min || 1;
  const stepX = w / (points.length - 1);
  const d = points.map((p,i) => `${i===0?"M":"L"} ${i*stepX} ${h - ((p-min)/range)*h*0.8 - 4}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-9 overflow-visible">
      <path d={d} fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      <path d={`${d} L ${w} ${h} L 0 ${h} Z`} fill={color} opacity={0.08} />
    </svg>
  );
}

/* — Line Chart placeholder — */
export function LineChartPlaceholder() {
  return (
    <div className="relative w-full h-[220px] sm:h-[260px] overflow-hidden rounded-xl bg-[var(--card-bg-soft)] border border-[var(--border-soft)] p-4">
      {/* grid */}
      <div className="absolute inset-4 grid grid-rows-4 gap-0 opacity-60">
        {[0,1,2,3].map(i=> <div key={i} className="border-t border-dashed border-[var(--border)]" />)}
      </div>
      <svg viewBox="0 0 600 200" className="absolute inset-0 w-full h-full p-4">
        {/* area fills */}
        <path d="M0 140 C 80 120, 140 160, 200 110 S 320 80, 380 100 S 480 60, 520 90 S 580 40, 600 70 L 600 200 L 0 200 Z" fill="var(--primary)" opacity={0.08} />
        <path d="M0 160 C 80 150, 140 170, 220 140 S 340 120, 400 135 S 500 100, 600 120 L 600 200 L 0 200 Z" fill="var(--secondary)" opacity={0.06} />
        {/* lines */}
        <path d="M0 140 C 80 120, 140 160, 200 110 S 320 80, 380 100 S 480 60, 520 90 S 580 40, 600 70" fill="none" stroke="var(--primary)" strokeWidth="2.5" strokeLinecap="round" />
        <path d="M0 160 C 80 150, 140 170, 220 140 S 340 120, 400 135 S 500 100, 600 120" fill="none" stroke="var(--secondary)" strokeWidth="2" strokeLinecap="round" strokeDasharray="6 6" opacity={0.9} />
        {/* dots */}
        {[200,380,520,600].map((x,i)=> (
          <g key={i}>
            <circle cx={x} cy={[110,100,90,70][i]} r="6" fill="white" stroke="var(--primary)" strokeWidth="2" />
            <circle cx={x} cy={[110,100,90,70][i]} r="2" fill="var(--primary)" />
          </g>
        ))}
      </svg>
      {/* tooltip mock */}
      <div className="absolute left-[58%] top-[18%] bg-[var(--text)] text-white text-[11px] font-semibold px-3 py-1.5 rounded-full shadow-lg flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-[var(--primary)]" /> 68.4k
        <span className="opacity-60 font-normal">Mar 24</span>
      </div>
      <div className="absolute bottom-3 left-4 right-4 flex justify-between text-[11px] font-medium text-[var(--text-faint)]">
        <span>Jan</span><span>Feb</span><span>Mar</span><span>Apr</span><span>May</span><span>Jun</span><span>Jul</span>
      </div>
    </div>
  );
}

/* — Donut placeholder — */
export function DonutChart({ size=140, thickness=18 }: { size?: number; thickness?: number }) {
  const data = [
    { label: "Direct", value: 42, color: "var(--primary)" },
    { label: "Social", value: 28, color: "var(--secondary)" },
    { label: "Referral", value: 18, color: "#f59e0b" },
    { label: "Organic", value: 12, color: "#10b981" },
  ];
  const total = data.reduce((a,b)=>a+b.value,0);
  let offset = 0;
  return (
    <div className="flex items-center gap-6">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
          <circle cx={size/2} cy={size/2} r={(size-thickness)/2} fill="none" stroke="var(--border-soft)" strokeWidth={thickness} />
          {data.map((d,i)=>{
            const frac = d.value/total;
            const len = Math.PI*2*((size-thickness)/2);
            const seg = frac*len;
            const gap = 3;
            const dash = `${Math.max(0, seg-gap)} ${len}`;
            const c = <circle key={i} cx={size/2} cy={size/2} r={(size-thickness)/2} fill="none" stroke={d.color} strokeWidth={thickness} strokeDasharray={dash} strokeDashoffset={-offset*len} strokeLinecap="round" style={{ transition: "all 0.6s ease" }} />;
            offset += frac;
            return c;
          })}
        </svg>
        <div className="absolute inset-0 grid place-items-center">
          <div className="text-center">
            <div className="text-[22px] font-extrabold leading-none tracking-tight">86%</div>
            <div className="text-[10px] font-semibold tracking-widest uppercase text-[var(--text-faint)]">Engaged</div>
          </div>
        </div>
      </div>
      <div className="flex flex-col gap-2.5 flex-1">
        {data.map(d=>(
          <div key={d.label} className="flex items-center gap-2.5 text-[13px]">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
            <span className="font-medium text-[var(--text)] flex-1">{d.label}</span>
            <span className="font-semibold">{d.value}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* — Bar mini — */
export function MiniBars({ values = [40,65,45,80,55,90,60], color="var(--primary)" }: { values?: number[]; color?: string }) {
  return (
    <div className="flex items-end gap-1.5 h-10">
      {values.map((v,i)=> (
        <div key={i} className="flex-1 rounded-full transition-all duration-700" style={{ height: `${v}%`, background: color, opacity: 0.85 + i*0.02, animationDelay: `${i*80}ms` }} />
      ))}
    </div>
  );
}

export function Progress({ value, color="var(--primary)" }: { value: number; color?: string }) {
  return (
    <div className="h-1.5 bg-[var(--border-soft)] rounded-full overflow-hidden">
      <div className="h-full rounded-full transition-all duration-700 ease-out" style={{ width: `${value}%`, background: color }} />
    </div>
  );
}
