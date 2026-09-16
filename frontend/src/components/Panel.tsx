import type { HTMLAttributes, PropsWithChildren } from "react";

export function Panel({ children, className = "", ...props }: PropsWithChildren<HTMLAttributes<HTMLElement>>) {
  return (
    <article className={`panel ${className}`} {...props}>
      {children}
    </article>
  );
}
