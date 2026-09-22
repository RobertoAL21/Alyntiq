export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Overview {
  latest_market_bar_at: string | null;
  market_bar_count: number;
  symbol_count: number;
  experiment_count: number;
  decision_count: number;
  positions_available: boolean;
  strategy_results_available: boolean;
}

export interface MarketCandle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketSnapshot {
  symbol: string;
  source: string;
  timeframe: string;
  candles: MarketCandle[];
}

export interface ExperimentRun {
  id: string;
  name: string;
  model_version: string | null;
  started_at: string;
  accuracy: number | null;
  precision: number | null;
  roc_auc: number | null;
  registry_state: string | null;
}

export interface TradingDecision {
  id: string;
  timestamp: string;
  symbol: string;
  signal: string;
  risk_decision: string;
  executed: boolean;
  price: number | null;
  quantity: number | null;
  model_version: string | null;
  confidence: number | null;
  reason: string;
}
