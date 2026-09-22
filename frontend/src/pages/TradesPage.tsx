import { DashboardDataState } from "../components/DashboardDataState";
import { DataTableFrame } from "../components/DataTableFrame";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { loadTrades } from "../lib/dashboard-api";
import { formatCurrency, formatDateTime, formatPercent } from "../lib/format";
import { useDashboardResource } from "../lib/use-dashboard-resource";

export function TradesPage() {
  const { data: decisions, error, loading } = useDashboardResource(loadTrades);
  return (
    <>
      <PageHeader eyebrow="Execution history" title="Trading decisions" description="Read-only audit records. This dashboard has no controls that submit orders." />
      <DashboardDataState loading={loading} error={error} empty={decisions !== null && decisions.length === 0} emptyMessage="No hay decisiones de trading auditadas en la base de datos." />
      {decisions && decisions.length > 0 ? <DataTableFrame title="Decision ledger" description="Persisted audit facts; an unexecuted decision is not represented as a trade fill."><div className="overflow-x-auto"><table className="w-full min-w-[860px] text-left text-sm"><thead className="border-b border-[#e6ebe5] bg-[#f8faf7] text-[10px] font-bold uppercase tracking-[0.12em] text-[#84918c]"><tr><th className="px-5 py-3.5">Recorded at</th><th className="px-5 py-3.5">Asset</th><th className="px-5 py-3.5">Signal</th><th className="px-5 py-3.5">Risk decision</th><th className="px-5 py-3.5 text-right">Execution</th><th className="px-5 py-3.5">Model</th><th className="px-5 py-3.5 text-right">Confidence</th></tr></thead><tbody className="divide-y divide-[#edf0ec]">{decisions.map((decision) => <tr key={decision.id} className="transition-colors hover:bg-[#f8faf7]"><td className="px-5 py-3.5 text-xs font-medium text-[#52615d]">{formatDateTime(decision.timestamp)}</td><td className="px-5 py-3.5 font-display font-semibold text-[#24302d]">{decision.symbol}</td><td className="px-5 py-3.5"><StatusBadge tone={decision.signal === "buy" ? "positive" : decision.signal === "sell" ? "negative" : "neutral"}>{decision.signal}</StatusBadge></td><td className="px-5 py-3.5"><StatusBadge tone={decision.risk_decision === "approved" ? "positive" : "neutral"}>{decision.risk_decision}</StatusBadge></td><td className="px-5 py-3.5 text-right text-[#53615d]">{decision.executed && decision.price !== null && decision.quantity !== null ? `${decision.quantity} · ${formatCurrency(decision.price, 2)}` : "Not executed"}</td><td className="px-5 py-3.5 text-[#65736f]">{decision.model_version ?? "No model lineage"}</td><td className="px-5 py-3.5 text-right font-display font-semibold text-[#255e4d]">{decision.confidence === null ? "—" : formatPercent(decision.confidence)}</td></tr>)}</tbody></table></div></DataTableFrame> : null}
    </>
  );
}
