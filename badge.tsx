export function Badge({ children, tone = "default", className = "" }: { children: React.ReactNode; tone?: "default"|"success"|"warning"|"primary"; className?: string }) {
  const tones: Record<string, string> = {
    default: "bg-[var(--card-bg-soft)] text-[var(--text-dim)] border-[var(--border)]",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900",
    warning: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400",
    primary: "bg-[var(--primary-soft)] text-[var(--primary)] border-[rgba(99,91,255,0.18)]",
  };
  return <span className={`inline-flex items-center gap-1.5 text-[11px] font-semibold tracking-wide px-2.5 py-1 rounded-full border ${tones[tone]} ${className}`}>{children}</span>;
}
