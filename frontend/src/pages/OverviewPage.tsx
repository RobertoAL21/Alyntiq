import {
  Activity,
  BrainCircuit,
  Database,
  ListOrdered,
  Sparkles,
} from "lucide-react";

import { AmbientShader } from "../components/AmbientShader";
import { DashboardDataState } from "../components/DashboardDataState";
import { MarketOrbit } from "../components/MarketOrbit";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { Panel } from "../components/Panel";
import { StatusBadge } from "../components/StatusBadge";
import { loadOverview } from "../lib/dashboard-api";
import { formatDateTime } from "../lib/format";
import { useDashboardResource } from "../lib/use-dashboard-resource";

export function OverviewPage() {
  const { data, error, loading } = useDashboardResource(loadOverview);

  return (
    <>
      <PageHeader
        eyebrow="Research workspace"
        title="Good afternoon, Riaam."
        description="A visual view of the research data stored locally. This dashboard is read-only and never submits orders."
      >
        {data?.latest_market_bar_at ? <p className="rounded-full border border-[#dce4dc] bg-white px-3 py-1.5 text-xs text-[#687672]">Latest market bar · {formatDateTime(data.latest_market_bar_at)} UTC</p> : null}
      </PageHeader>
      <DashboardDataState loading={loading} error={error} empty={data === null} emptyMessage="No hay datos disponibles todavía." />
      {data ? <>
        <section className="relative mb-5 min-h-[355px] overflow-hidden rounded-[1.5rem] border border-white bg-[#f8faf7] px-5 py-7 shadow-[0_18px_45px_rgba(32,63,50,0.08)] sm:px-8 sm:py-9">
          <AmbientShader />
          <div className="relative grid h-full gap-2 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
            <div className="relative z-[2] max-w-md">
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#cfe4d4] bg-white/80 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-[#24745c]"><Sparkles size={13} />Research snapshot</div>
              <p className="text-sm text-[#6e7d78]">Stored market observations</p>
              <p className="font-display mt-1 text-4xl font-semibold tracking-[-0.055em] text-[#172724] sm:text-5xl">{data.market_bar_count.toLocaleString()}</p>
              <div className="mt-5 flex flex-wrap gap-2">
                <div className="rounded-xl border border-white bg-white/80 px-3.5 py-2.5 shadow-sm backdrop-blur"><p className="text-[9px] font-bold uppercase tracking-[0.12em] text-[#83918c]">Coverage</p><p className="font-display mt-1 text-sm font-semibold text-[#2f423d]">{data.symbol_count} stored symbols</p></div>
                <div className="rounded-xl border border-white bg-white/80 px-3.5 py-2.5 shadow-sm backdrop-blur"><p className="text-[9px] font-bold uppercase tracking-[0.12em] text-[#83918c]">Experiments</p><p className="font-display mt-1 text-sm font-semibold text-[#16755b]">{data.experiment_count} tracked runs</p></div>
              </div>
            </div>
            <div className="relative -mb-8 -mr-10 -mt-4 min-h-[300px] sm:-mr-2 lg:-mb-14 lg:-mr-12 lg:-mt-10"><MarketOrbit /></div>
          </div>
        </section>
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Market bars" value={data.market_bar_count.toLocaleString()} detail="Persisted OHLCV observations" icon={<Database size={18} />} />
          <MetricCard label="Symbols" value={data.symbol_count.toString()} detail="Symbols with stored market data" icon={<Activity size={18} />} />
          <MetricCard label="Experiment runs" value={data.experiment_count.toString()} detail="Runs recorded by local MLflow" icon={<BrainCircuit size={18} />} />
          <MetricCard label="Audit decisions" value={data.decision_count.toString()} detail="Persisted trading-decision records" icon={<ListOrdered size={18} />} />
        </section>
        <section className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
          <Panel className="p-5">
            <div className="mb-5 flex items-start justify-between gap-4"><div><h2 className="font-display font-semibold text-[#24302d]">Research coverage</h2><p className="mt-1 text-sm text-[#7b8884]">Only persisted facts are shown; unavailable workflows are not simulated.</p></div><span className="rounded-xl bg-[#edf4f0] p-2.5 text-[#257257]"><Database size={18} /></span></div>
            <div className="grid gap-3 sm:grid-cols-3"><div className="rounded-xl border border-[#e8ede7] bg-[#fbfcfa] p-4"><p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#84918c]">Market data</p><p className="font-display mt-2 text-2xl font-semibold text-[#24302d]">{data.market_bar_count.toLocaleString()}</p><p className="mt-1 text-xs text-[#778480]">bars retained locally</p></div><div className="rounded-xl border border-[#e8ede7] bg-[#fbfcfa] p-4"><p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#84918c]">MLflow</p><p className="font-display mt-2 text-2xl font-semibold text-[#24302d]">{data.experiment_count}</p><p className="mt-1 text-xs text-[#778480]">recorded model runs</p></div><div className="rounded-xl border border-[#e8ede7] bg-[#fbfcfa] p-4"><p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#84918c]">Audit</p><p className="font-display mt-2 text-2xl font-semibold text-[#24302d]">{data.decision_count}</p><p className="mt-1 text-xs text-[#778480]">trading decisions</p></div></div>
          </Panel>
          <Panel className="p-5"><h2 className="font-display font-semibold text-[#24302d]">Research state</h2><p className="mt-1 text-sm text-[#7b8884]">Data boundaries are explicit.</p><dl className="mt-6 space-y-5"><div className="flex items-center justify-between gap-3"><dt className="text-sm text-[#74817d]">Trading environment</dt><dd><StatusBadge tone="warning">Paper only</StatusBadge></dd></div><div className="flex items-center justify-between gap-3"><dt className="text-sm text-[#74817d]">Position snapshots</dt><dd><StatusBadge tone="neutral">Not persisted</StatusBadge></dd></div><div className="flex items-center justify-between gap-3"><dt className="text-sm text-[#74817d]">Strategy runs</dt><dd><StatusBadge tone="neutral">Not persisted</StatusBadge></dd></div><div className="flex items-center justify-between gap-3"><dt className="text-sm text-[#74817d]">Order controls</dt><dd><StatusBadge tone="neutral">Disabled</StatusBadge></dd></div></dl></Panel>
        </section>
      </> : null}
    </>
  );
}
