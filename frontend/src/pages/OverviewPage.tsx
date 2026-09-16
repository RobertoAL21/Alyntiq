import { Activity, ArrowUpRight, Banknote, CircleDollarSign, Sparkles, WalletCards } from "lucide-react";

import { AmbientShader } from "../components/AmbientShader";
import { MetricCard } from "../components/MetricCard";
import { MarketOrbit } from "../components/MarketOrbit";
import { Panel } from "../components/Panel";
import { PageHeader } from "../components/PageHeader";
import { PerformanceChart } from "../components/PerformanceChart";
import { StatusBadge } from "../components/StatusBadge";
import { dashboardSnapshot } from "../data/dashboard-demo";
import { formatCurrency, formatDateTime, formatPercent } from "../lib/format";

export function OverviewPage() {
  const snapshot = dashboardSnapshot;
  const portfolioReturn = snapshot.totalPnl / (snapshot.portfolioValue - snapshot.totalPnl);

  return (
    <>
      <PageHeader eyebrow="Portfolio workspace" title="Good afternoon, Riaam." description="A calm view of your research portfolio. Values are a presentation sample until read-only APIs are available.">
        <p className="rounded-full border border-[#dce4dc] bg-white px-3 py-1.5 text-xs text-[#687672]">As of {formatDateTime(snapshot.asOf)} UTC</p>
      </PageHeader>
      <section className="relative mb-5 min-h-[355px] overflow-hidden rounded-[1.5rem] border border-white bg-[#f8faf7] px-5 py-7 shadow-[0_18px_45px_rgba(32,63,50,0.08)] sm:px-8 sm:py-9">
        <AmbientShader />
        <div className="relative grid h-full gap-2 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <div className="relative z-[2] max-w-md">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#cfe4d4] bg-white/80 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-[#24745c]"><Sparkles size={13} />Research snapshot</div>
            <p className="text-sm text-[#6e7d78]">Total portfolio value</p>
            <p className="font-display mt-1 text-4xl font-semibold tracking-[-0.055em] text-[#172724] sm:text-5xl">{formatCurrency(snapshot.portfolioValue, 2)}</p>
            <div className="mt-5 flex flex-wrap gap-2">
              <div className="rounded-xl border border-white bg-white/80 px-3.5 py-2.5 shadow-sm backdrop-blur"><p className="text-[9px] font-bold uppercase tracking-[0.12em] text-[#83918c]">Total return</p><p className="mt-1 flex items-center gap-1 font-display text-sm font-semibold text-[#16755b]"><ArrowUpRight size={15} />{formatPercent(portfolioReturn)}</p></div>
              <div className="rounded-xl border border-white bg-white/80 px-3.5 py-2.5 shadow-sm backdrop-blur"><p className="text-[9px] font-bold uppercase tracking-[0.12em] text-[#83918c]">Risk status</p><p className="font-display mt-1 text-sm font-semibold text-[#2f423d]">Within limits</p></div>
            </div>
          </div>
          <div className="relative -mb-8 -mr-10 -mt-4 min-h-[300px] sm:-mr-2 lg:-mb-14 lg:-mr-12 lg:-mt-10"><MarketOrbit /></div>
        </div>
      </section>
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Portfolio value" value={formatCurrency(snapshot.portfolioValue, 2)} detail={`${formatPercent(portfolioReturn)} total return`} positive icon={<WalletCards size={18} />} />
        <MetricCard label="Daily PnL" value={formatCurrency(snapshot.dailyPnl, 2)} detail={formatPercent(snapshot.dailyPnl / snapshot.portfolioValue)} positive={snapshot.dailyPnl >= 0} icon={<Activity size={18} />} />
        <MetricCard label="Available cash" value={formatCurrency(snapshot.cash, 2)} detail={`${formatPercent(1 - snapshot.exposure)} unallocated`} icon={<Banknote size={18} />} />
        <MetricCard label="Market exposure" value={formatPercent(snapshot.exposure)} detail="Long exposure" positive icon={<CircleDollarSign size={18} />} />
      </section>
      <section className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <Panel className="p-5">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <h2 className="font-display font-semibold text-[#24302d]">Portfolio performance</h2>
              <p className="mt-1 text-sm text-[#7b8884]">Portfolio value compared with the benchmark index.</p>
            </div>
            <div className="hidden items-center gap-3 text-xs text-[#7b8884] sm:flex"><span className="flex items-center gap-1.5"><i className="h-2 w-2 rounded-full bg-[#16755b]" />Portfolio</span><span className="flex items-center gap-1.5"><i className="h-2 w-2 rounded-full bg-[#9aa6a0]" />Benchmark</span></div>
          </div>
          <PerformanceChart data={snapshot.portfolioHistory} />
        </Panel>
        <Panel className="p-5">
          <h2 className="font-display font-semibold text-[#24302d]">Research state</h2>
          <p className="mt-1 text-sm text-[#7b8884]">This frontend is presentation-only.</p>
          <dl className="mt-6 space-y-5">
            <div className="flex items-center justify-between gap-3"><dt className="text-sm text-[#74817d]">Trading environment</dt><dd><StatusBadge tone="warning">Paper only</StatusBadge></dd></div>
            <div className="flex items-center justify-between gap-3"><dt className="text-sm text-[#74817d]">Benchmark return</dt><dd className="font-display text-sm font-semibold text-[#24302d]">{formatPercent(snapshot.benchmarkReturn)}</dd></div>
            <div className="flex items-center justify-between gap-3"><dt className="text-sm text-[#74817d]">Open positions</dt><dd className="font-display text-sm font-semibold text-[#24302d]">{snapshot.positions.length}</dd></div>
            <div className="flex items-center justify-between gap-3"><dt className="text-sm text-[#74817d]">Approved order flow</dt><dd><StatusBadge tone="neutral">Not connected</StatusBadge></dd></div>
          </dl>
        </Panel>
      </section>
    </>
  );
}
