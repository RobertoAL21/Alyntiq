import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { dashboardSnapshot } from "../data/dashboard-demo";
import { formatCurrency, formatDateTime, formatPercent } from "../lib/format";

export function TradesPage() {
  return (
    <>
      <PageHeader eyebrow="Execution history" title="Trades" description="An audit-oriented view of sample execution records. No controls submit trades from this dashboard." />
      <DataTableFrame title="Execution ledger" description="Audit-ready sample records. No order controls are connected." meta={<span className="hidden rounded-full bg-[#f0f2ef] px-2.5 py-1 text-[10px] font-bold text-[#66736f] sm:inline-flex">Today</span>} actions={<><button type="button" className="inline-flex items-center gap-2 rounded-lg border border-[#e2e8e1] bg-white px-3 py-2 text-xs font-medium text-[#5e6d68]"><ReceiptText size={14} />All executions <ChevronDown size={13} /></button><button type="button" className="grid h-8 w-8 place-items-center rounded-lg border border-[#e2e8e1] bg-white text-[#5e6d68]" aria-label="Filter trade records"><ListFilter size={14} /></button></>}><div className="overflow-x-auto"><table className="w-full min-w-[820px] text-left text-sm"><thead className="border-b border-[#e6ebe5] bg-[#f8faf7] text-[10px] font-bold uppercase tracking-[0.12em] text-[#84918c]"><tr><th className="px-5 py-3.5">Recorded at</th><th className="px-5 py-3.5">Asset</th><th className="px-5 py-3.5">Side</th><th className="px-5 py-3.5 text-right">Quantity</th><th className="px-5 py-3.5 text-right">Execution price</th><th className="px-5 py-3.5">Source model</th><th className="px-5 py-3.5 text-right">Signal confidence</th></tr></thead><tbody className="divide-y divide-[#edf0ec]">{dashboardSnapshot.trades.map((trade) => <motion.tr key={`${trade.timestamp}-${trade.symbol}`} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }} className="group transition-colors hover:bg-[#f8faf7]"><td className="px-5 py-3.5"><p className="text-xs font-medium text-[#52615d]">{formatDateTime(trade.timestamp)}</p><p className="mt-0.5 text-[10px] text-[#909b97]">UTC</p></td><td className="px-5 py-3.5 font-display font-semibold text-[#24302d]">{trade.symbol}</td><td className="px-5 py-3.5"><StatusBadge tone={trade.side === "BUY" ? "positive" : "negative"}>{trade.side}</StatusBadge></td><td className="px-5 py-3.5 text-right font-medium text-[#53615d]">{trade.quantity}</td><td className="px-5 py-3.5 text-right font-display font-semibold text-[#34413e]">{formatCurrency(trade.price, 2)}</td><td className="px-5 py-3.5"><span className="rounded-lg bg-[#f0f4f0] px-2.5 py-1.5 text-xs font-medium text-[#566661]">{trade.model}</span></td><td className="px-5 py-3.5 text-right"><span className="font-display font-semibold text-[#255e4d]">{formatPercent(trade.confidence)}</span><span className="mt-1 ml-auto block h-1 w-16 overflow-hidden rounded-full bg-[#e8eeea]"><i className="block h-full rounded-full bg-[#53ad7d]" style={{ width: `${trade.confidence * 100}%` }} /></span></td></motion.tr>)}</tbody></table></div></DataTableFrame>
    </>
  );
}
import { ChevronDown, ListFilter, ReceiptText } from "lucide-react";
import { motion } from "motion/react";

import { DataTableFrame } from "../components/DataTableFrame";
