import { ChartNoAxesCombined, ChevronDown, Radar } from "lucide-react";
import { motion } from "motion/react";

import { MarketChart } from "../components/MarketChart";
import { PageHeader } from "../components/PageHeader";
import { Panel } from "../components/Panel";
import { StatusBadge } from "../components/StatusBadge";
import { dashboardSnapshot } from "../data/dashboard-demo";
import { formatDateTime, formatPercent } from "../lib/format";

const signalTone = { Bullish: "positive", Bearish: "negative", Neutral: "neutral" } as const;

export function MarketPage() {
  return (
    <>
      <PageHeader eyebrow="Market intelligence" title="AAPL market view" description="Daily candlesticks, volume, and model-signal presentation from the dashboard sample." />
      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Panel className="p-5"><div className="mb-5 flex items-center justify-between"><div><div className="flex items-center gap-2"><h2 className="font-display font-semibold text-[#24302d]">Price and volume</h2><span className="h-1.5 w-1.5 rounded-full bg-[#42a877] shadow-[0_0_0_4px_rgba(66,168,119,0.12)]" /></div><p className="mt-1 text-sm text-[#7b8884]">Daily OHLCV · AAPL research view</p></div><button type="button" className="inline-flex items-center gap-2 rounded-lg border border-[#e2e8e1] bg-white px-3 py-2 text-xs font-medium text-[#5e6d68]"><ChartNoAxesCombined size={14} />1D <ChevronDown size={13} /></button></div><MarketChart data={dashboardSnapshot.candles} /></Panel>
        <Panel className="overflow-hidden"><header className="border-b border-[#e8ede7] bg-white/70 px-5 py-4"><div className="flex items-center justify-between gap-3"><div><h2 className="font-display font-semibold text-[#24302d]">Signal desk</h2><p className="mt-1 text-xs text-[#7b8884]">Model output, never an execution instruction.</p></div><span className="grid h-8 w-8 place-items-center rounded-lg bg-[#edf5ed] text-[#24745c]"><Radar size={16} /></span></div></header><div className="divide-y divide-[#edf0ec]">{dashboardSnapshot.signals.map((signal, index) => <motion.article key={`${signal.timestamp}-${signal.name}`} initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.22, delay: index * 0.06 }} className="group px-5 py-4 transition-colors hover:bg-[#f8faf7]"><div className="flex items-start justify-between gap-3"><div className="flex min-w-0 gap-3"><span className={`mt-0.5 h-2.5 w-2.5 shrink-0 rounded-full ${signal.direction === "Bullish" ? "bg-[#42a877] shadow-[0_0_0_4px_rgba(66,168,119,0.12)]" : signal.direction === "Bearish" ? "bg-[#df6978] shadow-[0_0_0_4px_rgba(223,105,120,0.12)]" : "bg-[#9ca8a3]"}`} /><div><p className="font-display text-sm font-semibold text-[#2b3734]">{signal.name}</p><p className="mt-1 text-[11px] text-[#83908c]">{formatDateTime(signal.timestamp)} UTC</p></div></div><StatusBadge tone={signalTone[signal.direction]}>{signal.direction}</StatusBadge></div><div className="mt-3 flex items-center justify-between gap-3"><span className="text-[11px] font-medium text-[#7c8985]">Confidence</span><span className="flex items-center gap-2"><i className="block h-1.5 w-16 overflow-hidden rounded-full bg-[#e8eeea]"><i className={`block h-full rounded-full ${signal.direction === "Bearish" ? "bg-[#df6978]" : "bg-[#53ad7d]"}`} style={{ width: `${signal.confidence * 100}%` }} /></i><strong className="font-display text-xs text-[#33413d]">{formatPercent(signal.confidence)}</strong></span></div></motion.article>)}</div></Panel>
      </section>
    </>
  );
}
