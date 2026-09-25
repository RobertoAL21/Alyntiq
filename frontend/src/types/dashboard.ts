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

export type StrategyDeploymentState = "draft" | "validated" | "armed";

export interface StrategyDeployment {
  id: string;
  name: string;
  state: StrategyDeploymentState;
  model_version: string;
  strategy_version: string;
  symbols: string[];
  created_at: string;
  updated_at: string;
  latest_preflight_outcome: "ready" | "blocked" | null;
  latest_preflight_reason: string | null;
  latest_preflight_at: string | null;
}

export interface RiskLimitsInput {
  maximum_position_size_pct: string;
  maximum_portfolio_exposure: string;
  maximum_daily_loss_pct: string;
  maximum_drawdown_pct: string;
  stop_loss_pct: string;
  take_profit_pct: string;
  max_trades_per_day: string;
  minimum_cash_reserve: string;
}

export interface StrategyDeploymentCreateInput {
  name: string;
  model_version: string;
  strategy_version: string;
  feature_version: string;
  target_version: string;
  source: string;
  timeframe: string;
  symbols: string[];
  buy_threshold: string;
  sell_threshold: string;
  order_quantity: string;
  risk_limits: RiskLimitsInput;
}
