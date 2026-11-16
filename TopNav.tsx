"use client";
import { Search, Bell, Settings, ChevronDown, Sparkles, Menu, X } from "lucide-react";
import { useState } from "react";

export function TopNav({ onThemeToggle, theme }: { onThemeToggle: () => void; theme: string }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <nav className="flex items-center justify-between gap-4 px-6 sm:px-8 py-4 border-b border-[var(--border-soft)]">
      {/* Logo */}
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-9 h-9 rounded-xl bg-[var(--text)] dark:bg-white grid place-items-center text-white dark:text-black shadow-sm flex-shrink-0">
          <Sparkles size={18} strokeWidth={2} />
        </div>
        <div className="hidden sm:block">
          <div className="text-[15px] font-bold tracking-tight leading-none">Acme Co.</div>
          <div className="text-[11px] text-[var(--text-faint)] font-medium">Dashboard</div>
        </div>
        {/* Mobile toggle */}
        <button onClick={() => setMobileOpen(!mobileOpen)} className="sm:hidden ml-2 p-2 rounded-lg border border-[var(--border)]">
          {mobileOpen ? <X size={16}/> : <Menu size={16}/>}
        </button>
      </div>

      {/* Center nav links */}
      <div className="hidden lg:flex items-center gap-1 bg-[var(--card-bg-soft)] p-1 rounded-full border border-[var(--border)]">
        {["Overview", "Projects", "Analytics", "Team", "Settings"].map((item, i) => (
          <a
            key={item}
            href="#"
            className={`px-4 py-1.5 rounded-full text-[13px] font-medium transition-colors ${i === 0 ? "bg-[var(--card-bg)] shadow-sm text-[var(--text)] border border-[var(--border)]" : "text-[var(--text-dim)] hover:text-[var(--text)]"}`}
          >
            {item}
          </a>
        ))}
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="absolute left-4 right-4 top-[64px] bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl p-3 shadow-[var(--shadow-lg)] lg:hidden z-30">
          <div className="flex flex-col gap-1">
            {["Overview","Projects","Analytics","Team","Settings"].map((item,i)=>(
              <a key={item} href="#" className={`px-4 py-2 rounded-xl text-sm ${i===0 ? "bg-[var(--primary-soft)] text-[var(--primary)] font-semibold" : "text-[var(--text-dim)]"}`}>{item}</a>
            ))}
          </div>
        </div>
      )}

      {/* Right controls */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <div className="hidden md:flex items-center gap-2 bg-[var(--card-bg-soft)] border border-[var(--border)] rounded-full px-3 py-1.5 focus-within:border-[var(--primary)] focus-within:shadow-[0_0_0_3px_var(--primary-ring)] transition">
          <Search size={14} className="text-[var(--text-faint)]" />
          <input placeholder="Search..." className="bg-transparent outline-none text-[13px] w-28 lg:w-36 placeholder:text-[var(--text-faint)]" />
          <span className="hidden lg:inline-flex items-center gap-1 text-[10px] font-semibold bg-[var(--card-bg)] border border-[var(--border)] px-1.5 py-0.5 rounded-md text-[var(--text-faint)]">⌘K</span>
        </div>
        <button onClick={onThemeToggle} className="w-9 h-9 grid place-items-center rounded-full bg-[var(--card-bg-soft)] border border-[var(--border)] text-[var(--text-dim)] hover:text-[var(--text)] transition" title="Toggle theme">
          {theme === "light" ? "🌙" : "☀️"}
        </button>
        <button className="w-9 h-9 grid place-items-center rounded-full bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-dim)] hover:text-[var(--text)] relative">
          <Bell size={16} />
          <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-[var(--card-bg)]" />
        </button>
        <button className="hidden sm:grid w-9 h-9 place-items-center rounded-full bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-dim)]">
          <Settings size={16} />
        </button>
        <div className="w-9 h-9 rounded-full overflow-hidden border-2 border-white shadow-sm bg-gradient-to-br from-violet-500 to-indigo-500 grid place-items-center text-white font-bold text-xs">
          AK
        </div>
      </div>
    </nav>
  );
}
