import { BrainCircuit } from "lucide-react";

import { DashboardDataState } from "../components/DashboardDataState";
import { DataTableFrame } from "../components/DataTableFrame";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { loadModels } from "../lib/dashboard-api";
import { formatDateTime, formatPercent } from "../lib/format";
import { useDashboardResource } from "../lib/use-dashboard-resource";

export function ModelsPage() {
  const { data: runs, error, loading } = useDashboardResource(loadModels);
  return (
    <>
      <PageHeader eyebrow="Machine learning" title="Experiment runs" description="Metrics recorded by local MLflow. Metrics without a holdout value are shown exactly as unavailable." />
      <DashboardDataState loading={loading} error={error} empty={runs !== null && runs.length === 0} emptyMessage="No hay ejecuciones de modelos en el experimento MLflow local." />
      {runs && runs.length > 0 ? <DataTableFrame title="Model experiments" description="Read-only MLflow results; registry state is shown only when the version is registered."><div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b border-[#e6ebe5] bg-[#f8faf7] text-[10px] font-bold uppercase tracking-[0.12em] text-[#84918c]"><tr><th className="px-5 py-3.5">Model</th><th className="px-5 py-3.5">Registry state</th><th className="px-5 py-3.5 text-right">ROC-AUC</th><th className="px-5 py-3.5 text-right">Precision</th><th className="px-5 py-3.5">Recorded at</th></tr></thead><tbody className="divide-y divide-[#edf0ec]">{runs.map((run) => <tr key={run.id} className="transition-colors hover:bg-[#f8faf7]"><td className="px-5 py-3.5"><div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#edf4f0] text-[#257257]"><BrainCircuit size={17} /></span><div><p className="font-display font-semibold text-[#24302d]">{run.name}</p><p className="mt-0.5 text-[11px] text-[#87938f]">{run.model_version ?? "No version recorded"}</p></div></div></td><td className="px-5 py-3.5"><StatusBadge tone={run.registry_state === "production" ? "positive" : "neutral"}>{run.registry_state ?? "Unregistered"}</StatusBadge></td><td className="px-5 py-3.5 text-right font-display font-semibold text-[#34413e]">{run.roc_auc?.toFixed(3) ?? "—"}</td><td className="px-5 py-3.5 text-right font-display font-semibold text-[#34413e]">{run.precision === null ? "—" : formatPercent(run.precision)}</td><td className="px-5 py-3.5 text-[#61706b]">{formatDateTime(run.started_at)}</td></tr>)}</tbody></table></div></DataTableFrame> : null}
    </>
  );
}
