import type { PropsWithChildren, ReactNode } from "react";

interface DataTableFrameProps {
  title: string;
  description: string;
  meta?: ReactNode;
  actions?: ReactNode;
}

export function DataTableFrame({ title, description, meta, actions, children }: PropsWithChildren<DataTableFrameProps>) {
  return (
    <section className="table-shell">
      <header className="flex flex-col gap-4 border-b border-[#e8ede7] bg-white/70 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div>
            <h2 className="font-display text-sm font-semibold text-[#23312e]">{title}</h2>
            <p className="mt-0.5 text-xs text-[#7c8985]">{description}</p>
          </div>
          {meta}
        </div>
        {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
      </header>
      {children}
    </section>
  );
}
