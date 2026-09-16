interface StatusBadgeProps {
  children: string;
  tone?: "positive" | "negative" | "neutral" | "warning";
}

const tones = {
  positive: "bg-[#e7f7ec] text-[#137352] ring-[#76c99a]/30",
  negative: "bg-[#fff0f1] text-[#c43f55] ring-[#ea9daa]/30",
  neutral: "bg-[#eff2ef] text-[#596763] ring-[#96a19d]/20",
  warning: "bg-[#fff6dc] text-[#9a6a00] ring-[#e5b946]/25",
};

export function StatusBadge({ children, tone = "neutral" }: StatusBadgeProps) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1 ring-inset ${tones[tone]}`}>{children}</span>;
}
