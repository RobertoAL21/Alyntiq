import type { ReactNode } from "react";
import { motion } from "motion/react";

interface MetricCardProps {
  label: string;
  value: string;
  detail: string;
  positive?: boolean;
  icon: ReactNode;
}

export function MetricCard({ label, value, detail, positive, icon }: MetricCardProps) {
  return (
    <motion.article whileHover={{ y: -3 }} transition={{ type: "spring", stiffness: 380, damping: 25 }} className="panel p-5">
      <div className="mb-5 flex items-start justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#7c8985]">{label}</p>
        <span className="rounded-xl bg-[#eef4ee] p-2.5 text-[#286a55]">{icon}</span>
      </div>
      <p className="font-display text-[26px] font-semibold tracking-[-0.04em] text-[#1f2a28]">{value}</p>
      <p className={`mt-2 text-xs font-semibold ${positive === undefined ? "text-[#778480]" : positive ? "text-[#16805d]" : "text-[#d34c5e]"}`}>
        {detail}
      </p>
    </motion.article>
  );
}
