import * as React from "react";

export function Card({ className = "", children, hover = true, ...props }: React.HTMLAttributes<HTMLDivElement> & { hover?: boolean }) {
  return (
    <div
      className={`bg-[var(--card-bg)] border border-[var(--border)] rounded-[var(--radius)] shadow-[var(--shadow-card)] ${hover ? "card-transition hover-lift" : ""} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className = "", children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`flex items-center justify-between p-5 pb-3 ${className}`} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ className = "", children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={`text-[13px] font-semibold tracking-tight text-[var(--text-heading)] flex items-center gap-2 ${className}`} {...props}>
      {children}
    </h3>
  );
}

export function CardContent({ className = "", children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={`p-5 pt-0 ${className}`} {...props}>{children}</div>;
}

export function CardFooter({ className = "", children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={`p-5 pt-3 border-t border-[var(--border-soft)] ${className}`} {...props}>{children}</div>;
}
