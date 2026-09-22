import type { ExperimentRun, MarketSnapshot, Overview, TradingDecision } from "../types/dashboard";

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
