import { type FormEvent, useState } from "react";
import { BrainCircuit, ShieldCheck } from "lucide-react";

import { DashboardDataState } from "../components/DashboardDataState";
import { DataTableFrame } from "../components/DataTableFrame";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import {
  armStrategyDeployment,
  createStrategyDeployment,
  disarmStrategyDeployment,
  loadModels,
  loadStrategyDeployments,
  validateStrategyDeployment,
} from "../lib/dashboard-api";
import { formatDateTime, formatPercent } from "../lib/format";
import { useDashboardResource } from "../lib/use-dashboard-resource";
import type {
  StrategyDeployment,
  StrategyDeploymentCreateInput,
  StrategyDeploymentState,
} from "../types/dashboard";

const inputClass =
  "w-full rounded-xl border border-[#dce5de] bg-white px-3 py-2 text-sm text-[#34413e] outline-none transition focus:border-[#4a9f6b] focus:ring-2 focus:ring-[#9ad5ad]/30";

const initialDeployment: StrategyDeploymentCreateInput = {
  name: "",
  model_version: "",
  strategy_version: "",
  feature_version: "",
  target_version: "",
  source: "",
  timeframe: "",
  symbols: [],
  buy_threshold: "",
  sell_threshold: "",
  order_quantity: "",
  risk_limits: {
    maximum_position_size_pct: "",
    maximum_portfolio_exposure: "",
    maximum_daily_loss_pct: "",
    maximum_drawdown_pct: "",
    stop_loss_pct: "",
    take_profit_pct: "",
    max_trades_per_day: "",
    minimum_cash_reserve: "",
  },
};

const riskFields = [
  ["maximum_position_size_pct", "Max position size (0–1)", "number"],
  ["maximum_portfolio_exposure", "Max portfolio exposure (0–1)", "number"],
  ["maximum_daily_loss_pct", "Max daily loss (0–1)", "number"],
  ["maximum_drawdown_pct", "Max drawdown (0–1)", "number"],
  ["stop_loss_pct", "Stop loss (0–1)", "number"],
  ["take_profit_pct", "Take profit (0–1)", "number"],
  ["max_trades_per_day", "Max trades per day", "number"],
  ["minimum_cash_reserve", "Minimum cash reserve", "number"],
] as const;

export function ModelsPage() {
  const { data: runs, error, loading } = useDashboardResource(loadModels);
  const deployments = useDashboardResource(loadStrategyDeployments);
  const [controlToken, setControlToken] = useState("");
  const [form, setForm] = useState(initialDeployment);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [pending, setPending] = useState<string | null>(null);
  const controlsEnabled = controlToken.trim().length > 0 && pending === null;

  async function submitDeployment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending("create");
    setFeedback(null);
    try {
      await createStrategyDeployment(form, controlToken);
      setForm(initialDeployment);
      setFeedback("Deployment saved as draft. Validate it before arming it.");
      deployments.reload();
    } catch (reason) {
      setFeedback(messageFor(reason));
    } finally {
      setPending(null);
    }
  }

  async function transition(id: string, action: "validate" | "arm" | "disarm") {
    setPending(`${action}:${id}`);
    setFeedback(null);
    try {
      if (action === "validate") await validateStrategyDeployment(id, controlToken);
      if (action === "arm") await armStrategyDeployment(id, controlToken);
      if (action === "disarm") await disarmStrategyDeployment(id, controlToken);
      setFeedback(`Deployment ${action === "arm" ? "armed" : `${action}d`} safely. No worker or order was started.`);
      deployments.reload();
    } catch (reason) {
      setFeedback(messageFor(reason));
    } finally {
      setPending(null);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Machine learning"
        title="Experiment runs"
        description="MLflow evidence, registry state, and paper-deployment preparation. Arming is configuration only; it never starts trading."
      />
      <DashboardDataState
        loading={loading}
        error={error}
        empty={runs !== null && runs.length === 0}
        emptyMessage="No hay ejecuciones de modelos en el experimento MLflow local."
      />
      {runs && runs.length > 0 ? <ModelExperiments runs={runs} /> : null}

      <section className="mt-7 overflow-hidden rounded-2xl border border-[#dfe8e0] bg-[#fbfdfb] shadow-[0_12px_35px_rgba(35,70,53,0.05)]">
        <header className="border-b border-[#e2ebe3] bg-white px-5 py-5 sm:flex sm:items-start sm:justify-between">
          <div className="flex gap-3">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#e8f5ec] text-[#267352]"><ShieldCheck size={19} /></span>
            <div>
              <h2 className="font-display text-base font-semibold text-[#24302d]">Paper deployment control</h2>
              <p className="mt-1 max-w-2xl text-sm text-[#61706b]">A deployment pins reviewed configuration. It can be armed only after backend checks; armed does not run a worker, infer, or send an Alpaca order.</p>
            </div>
          </div>
          <StatusBadge tone="warning">Paper only</StatusBadge>
        </header>
        <div className="grid gap-6 p-5 lg:grid-cols-[minmax(0,1fr)_minmax(300px,0.8fr)]">
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-[#53635e]" htmlFor="control-token">Local control token</label>
            <input id="control-token" className={inputClass} type="password" autoComplete="off" value={controlToken} onChange={(event) => setControlToken(event.target.value)} placeholder="Paste DASHBOARD_CONTROL_TOKEN" />
            <p className="mt-2 text-xs leading-5 text-[#74817d]">Held only in this page&apos;s memory and sent only to mutation endpoints. Leave it blank to keep controls disabled.</p>
            {feedback ? <p role="status" className="mt-3 rounded-xl bg-[#edf5ee] px-3 py-2 text-sm text-[#3f6650]">{feedback}</p> : null}
            <form className="mt-5 grid gap-3" onSubmit={submitDeployment}>
              <p className="text-sm font-semibold text-[#30403b]">Create a paper deployment draft</p>
              <div className="grid gap-3 sm:grid-cols-2">
                <TextInput label="Deployment name" value={form.name} onChange={(value) => setForm({ ...form, name: value })} />
                <TextInput label="Model version" value={form.model_version} onChange={(value) => setForm({ ...form, model_version: value })} />
                <TextInput label="Strategy version" value={form.strategy_version} onChange={(value) => setForm({ ...form, strategy_version: value })} />
                <TextInput label="Feature version" value={form.feature_version} onChange={(value) => setForm({ ...form, feature_version: value })} />
                <TextInput label="Target version" value={form.target_version} onChange={(value) => setForm({ ...form, target_version: value })} />
                <TextInput label="Market source" value={form.source} onChange={(value) => setForm({ ...form, source: value })} />
                <TextInput label="Timeframe" value={form.timeframe} onChange={(value) => setForm({ ...form, timeframe: value })} />
                <TextInput label="Symbols (comma-separated)" value={form.symbols.join(", ")} onChange={(value) => setForm({ ...form, symbols: value.split(",").map((symbol) => symbol.trim()).filter(Boolean) })} />
                <TextInput label="Buy threshold (0–1)" type="number" value={form.buy_threshold} onChange={(value) => setForm({ ...form, buy_threshold: value })} />
                <TextInput label="Sell threshold (0–1)" type="number" value={form.sell_threshold} onChange={(value) => setForm({ ...form, sell_threshold: value })} />
                <TextInput label="Proposed order quantity" type="number" value={form.order_quantity} onChange={(value) => setForm({ ...form, order_quantity: value })} />
              </div>
              <fieldset className="rounded-xl border border-[#e1e9e2] p-3">
                <legend className="px-1 text-xs font-semibold text-[#53635e]">Required risk limits</legend>
                <div className="grid gap-3 sm:grid-cols-2">
                  {riskFields.map(([field, label, type]) => <TextInput key={field} label={label} type={type} value={form.risk_limits[field]} onChange={(value) => setForm({ ...form, risk_limits: { ...form.risk_limits, [field]: value } })} />)}
                </div>
              </fieldset>
              <button className="rounded-xl bg-[#287656] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#1f6347] disabled:cursor-not-allowed disabled:bg-[#9ab5a4]" type="submit" disabled={!controlsEnabled}>{pending === "create" ? "Saving…" : "Save draft"}</button>
            </form>
          </div>
          <DeploymentList deployments={deployments.data} loading={deployments.loading} controlEnabled={controlsEnabled} pending={pending} onTransition={transition} />
        </div>
      </section>
    </>
  );
}

function ModelExperiments({ runs }: { runs: import("../types/dashboard").ExperimentRun[] }) {
  return <DataTableFrame title="Model experiments" description="Read-only MLflow results; registry state is shown only when the version is registered."><div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b border-[#e6ebe5] bg-[#f8faf7] text-[10px] font-bold uppercase tracking-[0.12em] text-[#84918c]"><tr><th className="px-5 py-3.5">Model</th><th className="px-5 py-3.5">Registry state</th><th className="px-5 py-3.5 text-right">ROC-AUC</th><th className="px-5 py-3.5 text-right">Precision</th><th className="px-5 py-3.5">Recorded at</th></tr></thead><tbody className="divide-y divide-[#edf0ec]">{runs.map((run) => <tr key={run.id} className="transition-colors hover:bg-[#f8faf7]"><td className="px-5 py-3.5"><div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#edf4f0] text-[#257257]"><BrainCircuit size={17} /></span><div><p className="font-display font-semibold text-[#24302d]">{run.name}</p><p className="mt-0.5 text-[11px] text-[#87938f]">{run.model_version ?? "No version recorded"}</p></div></div></td><td className="px-5 py-3.5"><StatusBadge tone={run.registry_state === "production" ? "positive" : "neutral"}>{run.registry_state ?? "Unregistered"}</StatusBadge></td><td className="px-5 py-3.5 text-right font-display font-semibold text-[#34413e]">{run.roc_auc?.toFixed(3) ?? "—"}</td><td className="px-5 py-3.5 text-right font-display font-semibold text-[#34413e]">{run.precision === null ? "—" : formatPercent(run.precision)}</td><td className="px-5 py-3.5 text-[#61706b]">{formatDateTime(run.started_at)}</td></tr>)}</tbody></table></div></DataTableFrame>;
}

function TextInput({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return <label className="block text-xs font-semibold text-[#53635e]">{label}<input required className={`mt-1.5 ${inputClass}`} type={type} min={type === "number" ? "0" : undefined} step={type === "number" ? "any" : undefined} value={value} onChange={(event) => onChange(event.target.value)} /></label>;
}

function DeploymentList({ deployments, loading, controlEnabled, pending, onTransition }: { deployments: StrategyDeployment[] | null; loading: boolean; controlEnabled: boolean; pending: string | null; onTransition: (id: string, action: "validate" | "arm" | "disarm") => Promise<void> }) {
  return <div className="rounded-xl border border-[#e1e9e2] bg-white p-4"><h3 className="font-display text-sm font-semibold text-[#30403b]">Persisted deployments</h3><p className="mt-1 text-xs leading-5 text-[#74817d]">Only backend-persisted states are listed.</p>{loading ? <p className="mt-4 text-sm text-[#74817d]">Loading deployments…</p> : null}{!loading && deployments?.length === 0 ? <p className="mt-4 rounded-xl bg-[#f6f8f6] p-3 text-sm text-[#74817d]">No deployment drafts yet.</p> : null}<div className="mt-4 space-y-3">{deployments?.map((deployment) => <article key={deployment.id} className="rounded-xl border border-[#e8ede8] p-3"><div className="flex items-start justify-between gap-2"><div><p className="font-medium text-[#30403b]">{deployment.name}</p><p className="mt-1 text-xs text-[#74817d]">{deployment.model_version} · {deployment.symbols.join(", ")}</p></div><StatusBadge tone={stateTone(deployment.state)}>{deployment.state}</StatusBadge></div><p className="mt-2 text-xs text-[#87938f]">Updated {formatDateTime(deployment.updated_at)}</p><div className="mt-3">{deployment.state === "draft" ? <ActionButton disabled={!controlEnabled || pending === `validate:${deployment.id}`} onClick={() => onTransition(deployment.id, "validate")}>Validate</ActionButton> : null}{deployment.state === "validated" ? <ActionButton disabled={!controlEnabled || pending === `arm:${deployment.id}`} onClick={() => onTransition(deployment.id, "arm")}>Arm configuration</ActionButton> : null}{deployment.state === "armed" ? <ActionButton disabled={!controlEnabled || pending === `disarm:${deployment.id}`} onClick={() => onTransition(deployment.id, "disarm")}>Disarm</ActionButton> : null}</div></article>)}</div></div>;
}

function ActionButton({ children, disabled, onClick }: { children: string; disabled: boolean; onClick: () => void }) {
  return <button type="button" className="rounded-lg border border-[#b9d8c1] px-3 py-1.5 text-xs font-semibold text-[#267352] hover:bg-[#eff8f1] disabled:cursor-not-allowed disabled:border-[#dfe8e0] disabled:text-[#9aaba1]" disabled={disabled} onClick={onClick}>{children}</button>;
}

function stateTone(state: StrategyDeploymentState): "neutral" | "warning" | "positive" {
  if (state === "armed") return "positive";
  if (state === "validated") return "warning";
  return "neutral";
}

function messageFor(reason: unknown): string {
  return reason instanceof Error ? reason.message : "No se pudo actualizar el deployment.";
}
