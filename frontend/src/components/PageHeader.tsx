import type { ReactNode } from "react";

interface PageHeaderProps {
  eyebrow: string;
  title: string;
  description: string;
  children?: ReactNode;
}

export function PageHeader({ eyebrow, title, description, children }: PageHeaderProps) {
  return (
    <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div>
        <p className="mb-1.5 font-display text-sm font-medium tracking-[-0.02em] text-[#24745c] sm:text-base">{eyebrow}</p>
        <h1 className="font-display text-[38px] font-normal leading-[1.03] tracking-[-0.055em] text-[#172321] sm:text-[48px]">{title}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-[#778480]">{description}</p>
      </div>
      {children}
    </div>
  );
}
