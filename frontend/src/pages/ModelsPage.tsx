import { BrainCircuit, ChevronDown, CircleCheckBig } from "lucide-react";
import { motion } from "motion/react";

import { DataTableFrame } from "../components/DataTableFrame";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { dashboardSnapshot } from "../data/dashboard-demo";
import { formatDate, formatPercent } from "../lib/format";

export function ModelsPage() {
  return (
    <>
      <PageHeader eyebrow="Machine learning" title="Models" description="Version and validation metric summaries for the model candidates in the dashboard snapshot." />
      <DataTableFrame title="Model registry" description="Candidate and validated model versions for research review." meta={<span className="hidden rounded-full bg-[#edf6ef] px-2.5 py-1 text-[10px] font-bold text-[#207258] sm:inline-flex"><CircleCheckBig size={11} className="mr-1" />2 validated</span>} actions={<button type="button" className="inline-flex items-center gap-2 rounded-lg border border-[#e2e8e1] bg-white px-3 py-2 text-xs font-medium text-[#5e6d68]"><BrainCircuit size={14} />All models <ChevronDown size={13} /></button>}><div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b border-[#e6ebe5] bg-[#f8faf7] text-[10px] font-bold uppercase tracking-[0.12em] text-[#84918c]"><tr><th className="px-5 py-3.5">Model</th><th className="px-5 py-3.5">Review state</th><th className="px-5 py-3.5 text-right">AUC</th><th className="px-5 py-3.5 text-right">Precision</th><th className="px-5 py-3.5">Training date</th><th className="px-5 py-3.5 text-right">Validation profile</th></tr></thead><tbody className="divide-y divide-[#edf0ec]">{dashboardSnapshot.models.map((model, index) => <motion.tr key={`${model.name}-${model.version}`} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22, delay: index * 0.04 }} className="group transition-colors hover:bg-[#f8faf7]"><td className="px-5 py-3.5"><div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#edf4f0] text-[#257257]"><BrainCircuit size={17} /></span><div><p className="font-display font-semibold text-[#24302d]">{model.name}</p><p className="mt-0.5 text-[11px] text-[#87938f]">{model.version}</p></div></div></td><td className="px-5 py-3.5"><StatusBadge tone={model.status === "Validated" ? "positive" : "warning"}>{model.status}</StatusBadge></td><td className="px-5 py-3.5 text-right"><span className="font-display font-semibold text-[#34413e]">{model.auc.toFixed(3)}</span></td><td className="px-5 py-3.5 text-right"><span className="font-display font-semibold text-[#34413e]">{formatPercent(model.precision)}</span></td><td className="px-5 py-3.5 text-[#61706b]">{formatDate(model.trainingDate)}</td><td className="px-5 py-3.5 text-right"><span className="inline-flex w-24 items-center gap-2"><i className="block h-1.5 flex-1 overflow-hidden rounded-full bg-[#e8eeea]"><i className="block h-full rounded-full bg-[#53ad7d]" style={{ width: `${model.auc * 100}%` }} /></i><span className="text-[11px] font-medium text-[#687670]">stable</span></span></td></motion.tr>)}</tbody></table></div></DataTableFrame>
    </>
  );
}
