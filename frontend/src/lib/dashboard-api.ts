import type {
  ExperimentRun,
  MarketSnapshot,
  Overview,
  StrategyDeployment,
  StrategyDeploymentCreateInput,
  TradingDecision,
} from "../types/dashboard";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`/api/dashboard/${path}`);
  if (!response.ok) {
    throw new Error(`Dashboard request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export function loadOverview(): Promise<Overview> {
  return request<Overview>("overview");
}

export function loadMarket(symbol = "AAPL"): Promise<MarketSnapshot> {
  return request<MarketSnapshot>(`market?symbol=${encodeURIComponent(symbol)}`);
}

export async function loadModels(): Promise<ExperimentRun[]> {
  return (await request<{ runs: ExperimentRun[] }>("models")).runs;
}

export async function loadTrades(): Promise<TradingDecision[]> {
  return (await request<{ decisions: TradingDecision[] }>("trades")).decisions;
}

export async function loadStrategyDeployments(): Promise<StrategyDeployment[]> {
  return (await request<{ deployments: StrategyDeployment[] }>("deployments")).deployments;
}

export async function createStrategyDeployment(
  input: StrategyDeploymentCreateInput,
  controlToken: string,
): Promise<void> {
  await controlRequest("", "POST", controlToken, {
    ...input,
    order_quantity: Number(input.order_quantity),
    risk_limits: {
      ...input.risk_limits,
      max_trades_per_day: Number(input.risk_limits.max_trades_per_day),
    },
  });
}

export async function validateStrategyDeployment(id: string, controlToken: string): Promise<void> {
  await controlRequest(`/${id}/validate`, "POST", controlToken);
}

export async function armStrategyDeployment(id: string, controlToken: string): Promise<void> {
  await controlRequest(`/${id}/arm`, "POST", controlToken);
}

export async function disarmStrategyDeployment(id: string, controlToken: string): Promise<void> {
  await controlRequest(`/${id}/disarm`, "POST", controlToken);
}

async function controlRequest(
  path: string,
  method: "POST",
  controlToken: string,
  body?: object,
): Promise<void> {
  const response = await fetch(`/api/control/strategy-deployments${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-Alyntiq-Control-Token": controlToken,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Deployment control request failed (${response.status})`);
  }
}
