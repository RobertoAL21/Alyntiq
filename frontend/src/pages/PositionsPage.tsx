import { BriefcaseBusiness, ChevronDown, SlidersHorizontal } from "lucide-react";
import { motion } from "motion/react";

import { DataTableFrame } from "../components/DataTableFrame";
import { PageHeader } from "../components/PageHeader";
import { dashboardSnapshot } from "../data/dashboard-demo";
import { formatCurrency, formatPercent } from "../lib/format";

export function PositionsPage() {
  return (
    <>
      <PageHeader eyebrow="Portfolio" title="Positions" description="Current holdings, valuation, and unrealized performance from the dashboard sample." />
      <DataTableFrame
        title="Current holdings"
        description="Valuation snapshot across the research portfolio."
        meta={<span className="hidden rounded-full bg-[#edf6ef] px-2.5 py-1 text-[10px] font-bold text-[#207258] sm:inline-flex">{dashboardSnapshot.positions.length} open</span>}
        actions={<><button type="button" className="inline-flex items-center gap-2 rounded-lg border border-[#e2e8e1] bg-white px-3 py-2 text-xs font-medium text-[#5e6d68]"><BriefcaseBusiness size={14} />All assets <ChevronDown size={13} /></button><button type="button" className="grid h-8 w-8 place-items-center rounded-lg border border-[#e2e8e1] bg-white text-[#5e6d68]" aria-label="Position display settings"><SlidersHorizontal size={14} /></button></>}
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-[#e6ebe5] bg-[#f8faf7] text-[10px] font-bold uppercase tracking-[0.12em] text-[#84918c]"><tr><th className="px-5 py-3.5">Asset</th><th className="px-5 py-3.5 text-right">Quantity</th><th className="px-5 py-3.5 text-right">Cost basis</th><th className="px-5 py-3.5 text-right">Last price</th><th className="px-5 py-3.5 text-right">Market value</th><th className="px-5 py-3.5 text-right">Unrealized P&amp;L</th></tr></thead>
            <tbody className="divide-y divide-[#edf0ec]">
              {dashboardSnapshot.positions.map((position) => {
                const positive = position.unrealizedPnl >= 0;
                return <motion.tr key={position.symbol} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }} className="group transition-colors hover:bg-[#f8faf7]"><td className="px-5 py-3.5"><div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#edf5ed] font-display text-xs font-bold text-[#227054]">{position.symbol.slice(0, 1)}</span><div><p className="font-display font-semibold text-[#24302d]">{position.symbol}</p><p className="mt-0.5 text-[11px] text-[#84918c]">US equity</p></div></div></td><td className="px-5 py-3.5 text-right font-medium text-[#53615d]">{position.quantity}</td><td className="px-5 py-3.5 text-right text-[#65736f]">{formatCurrency(position.averagePrice, 2)}</td><td className="px-5 py-3.5 text-right text-[#65736f]">{formatCurrency(position.currentPrice, 2)}</td><td className="px-5 py-3.5 text-right font-display font-semibold text-[#34413e]">{formatCurrency(position.marketValue, 2)}</td><td className={`px-5 py-3.5 text-right font-display font-semibold ${positive ? "text-[#16805d]" : "text-[#d34c5e]"}`}><span>{formatCurrency(position.unrealizedPnl, 2)}</span><span className="mt-0.5 block text-[11px] font-medium">{formatPercent(position.unrealizedPnlPercent)}</span></td></motion.tr>;
              })}
            </tbody>
          </table>
        </div>
      </DataTableFrame>
    </>
  );
}
