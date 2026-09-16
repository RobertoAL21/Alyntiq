import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { dashboardSnapshot } from "../data/dashboard-demo";
import { formatPercent } from "../lib/format";

export function StrategiesPage() {
  return (
    <>
      <PageHeader eyebrow="Research" title="Strategies" description="A leaderboard for comparing research strategies under their shared backtesting assumptions." />
      <DataTableFrame title="Research leaderboard" description="Comparable experiments under shared starting assumptions." meta={<span className="hidden rounded-full bg-[#fff5d9] px-2.5 py-1 text-[10px] font-bold text-[#946800] sm:inline-flex"><Trophy size={11} className="mr-1" />Top result</span>} actions={<button type="button" className="inline-flex items-center gap-2 rounded-lg border border-[#e2e8e1] bg-white px-3 py-2 text-xs font-medium text-[#5e6d68]"><ChartNoAxesCombined size={14} />All metrics <ChevronDown size={13} /></button>}><div className="overflow-x-auto"><table className="w-full min-w-[710px] text-left text-sm"><thead className="border-b border-[#e6ebe5] bg-[#f8faf7] text-[10px] font-bold uppercase tracking-[0.12em] text-[#84918c]"><tr><th className="w-16 px-5 py-3.5">Rank</th><th className="px-5 py-3.5">Strategy</th><th className="px-5 py-3.5">State</th><th className="px-5 py-3.5 text-right">Sharpe ratio</th><th className="px-5 py-3.5 text-right">Total return</th><th className="px-5 py-3.5 text-right">Max drawdown</th></tr></thead><tbody className="divide-y divide-[#edf0ec]">{dashboardSnapshot.strategies.map((strategy, index) => <motion.tr key={strategy.name} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22, delay: index * 0.04 }} className={`group transition-colors hover:bg-[#f8faf7] ${index === 0 ? "bg-[#f7fbf7]" : ""}`}><td className="px-5 py-3.5"><span className={`grid h-7 w-7 place-items-center rounded-lg text-xs font-bold ${index === 0 ? "bg-[#1b5f4a] text-white" : "bg-[#edf2ee] text-[#687670]"}`}>{index + 1}</span></td><td className="px-5 py-3.5"><p className="font-display font-semibold text-[#24302d]">{strategy.name}</p><p className="mt-0.5 text-[11px] text-[#87938f]">Independent virtual portfolio</p></td><td className="px-5 py-3.5"><StatusBadge tone={strategy.status === "Active" ? "positive" : "neutral"}>{strategy.status}</StatusBadge></td><td className="px-5 py-3.5 text-right"><span className="font-display font-semibold text-[#34413e]">{strategy.sharpeRatio.toFixed(2)}</span></td><td className="px-5 py-3.5 text-right"><span className="inline-flex items-center gap-1 font-display font-semibold text-[#16805d]"><ArrowUpRight size={14} />{formatPercent(strategy.totalReturn)}</span></td><td className="px-5 py-3.5 text-right font-display font-semibold text-[#d34c5e]">{formatPercent(strategy.maxDrawdown)}</td></motion.tr>)}</tbody></table></div></DataTableFrame>
      <p className="mt-4 text-xs text-[#7b8884]">Metrics are presentation data. Strategy calculations remain owned by the backend.</p>
    </>
  );
}
import { ArrowUpRight, ChartNoAxesCombined, ChevronDown, Trophy } from "lucide-react";
import { motion } from "motion/react";

import { DataTableFrame } from "../components/DataTableFrame";
