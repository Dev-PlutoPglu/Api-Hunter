"use client";
import { ChevronDown, Calendar, Plus, Sparkles } from "lucide-react";
import { Button } from "./ui/button";

export function DashboardHeader() {
  return (
    <div className="px-6 sm:px-8 py-6 sm:py-7 flex flex-col lg:flex-row lg:items-center justify-between gap-5 border-b border-[var(--border-soft)]">
      <div>
        <div className="flex items-center gap-2 text-[11px] font-semibold tracking-widest uppercase text-[var(--text-faint)] mb-2">
          <span>Home</span><span className="opacity-40">/</span><span className="text-[var(--text-dim)]">Dashboard</span>
        </div>
        <h1 className="text-[26px] sm:text-[30px] font-extrabold tracking-tight leading-none text-[var(--text-heading)]">
          Dashboard Overview
        </h1>
        <p className="text-[13px] text-[var(--text-dim)] mt-2 font-medium">Welcome back — here&apos;s what&apos;s happening today.</p>
      </div>

      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        {/* Dropdowns */}
        <div className="flex items-center gap-2">
          <button className="inline-flex items-center gap-2 text-[13px] font-medium bg-[var(--card-bg-soft)] border border-[var(--border)] px-3.5 py-2 rounded-full hover:bg-[var(--card-bg)] transition focus-ring">
            All Teams <ChevronDown size={14} className="text-[var(--text-faint)]" />
          </button>
          <button className="hidden sm:inline-flex items-center gap-2 text-[13px] font-medium bg-[var(--card-bg-soft)] border border-[var(--border)] px-3.5 py-2 rounded-full hover:bg-[var(--card-bg)] transition">
            <Calendar size={14} className="text-[var(--text-faint)]" />
            Last 7 days <ChevronDown size={14} className="text-[var(--text-faint)]" />
          </button>
        </div>

        <div className="h-6 w-px bg-[var(--border)] hidden sm:block" />

        <Button variant="ghost" size="md" className="rounded-full hidden sm:inline-flex">
          Export
        </Button>
        <Button variant="primary" size="md" className="rounded-full">
          <Plus size={16} /> New Project
        </Button>
      </div>
    </div>
  );
}
