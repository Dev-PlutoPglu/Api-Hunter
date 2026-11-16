import * as React from "react";

type Variant = "primary" | "secondary" | "ghost" | "outline";
type Size = "sm" | "md" | "lg";

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size }) {
  const base = "inline-flex items-center justify-center font-semibold tracking-tight rounded-full transition-all duration-200 focus-ring active:scale-[0.98]";
  const variants: Record<Variant, string> = {
    primary: "bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)] shadow-[0_6px_20px_rgba(99,91,255,0.25)] hover:shadow-[0_8px_24px_rgba(99,91,255,0.32)] hover:-translate-y-[1px]",
    secondary: "bg-[var(--text)] text-white hover:bg-[#1e293b] dark:bg-white dark:text-black",
    ghost: "bg-transparent text-[var(--text-dim)] hover:bg-[var(--hover-bg)] hover:text-[var(--text)]",
    outline: "bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text)] hover:border-[var(--border-strong)] hover:bg-[var(--card-bg-soft)]",
  };
  const sizes: Record<Size, string> = {
    sm: "text-[12px] px-3.5 py-1.5 gap-1.5",
    md: "text-[13px] px-4 py-2 gap-2",
    lg: "text-[13.5px] px-5 py-2.5 gap-2",
  };
  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  );
}

export function IconButton({ className = "", children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`w-9 h-9 grid place-items-center rounded-full bg-[var(--card-bg)] border border-[var(--border)] text-[var(--text-dim)] hover:text-[var(--text)] hover:border-[var(--border-strong)] hover:bg-[var(--hover-bg)] transition-all duration-200 focus-ring ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
