export type TradeSide = "BUY" | "SELL";

export interface PortfolioPoint {
  time: string;
  value: number;
  benchmark: number;
}

export interface Position {
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnl: number;
  unrealizedPnlPercent: number;
}

export interface Trade {
  timestamp: string;
  symbol: string;
  side: TradeSide;
  quantity: number;
  price: number;
  model: string;
  confidence: number;
}

export interface Strategy {
  name: string;
  status: "Active" | "Research";
  sharpeRatio: number;
  totalReturn: number;
  maxDrawdown: number;
}

export interface Model {
  name: string;
  version: string;
  auc: number;
  precision: number;
  trainingDate: string;
  status: "Candidate" | "Validated";
}

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketSignal {
  timestamp: string;
  name: string;
  direction: "Bullish" | "Bearish" | "Neutral";
  confidence: number;
}

export interface DashboardSnapshot {
  asOf: string;
  portfolioValue: number;
  dailyPnl: number;
  totalPnl: number;
  cash: number;
  exposure: number;
  benchmarkReturn: number;
  portfolioHistory: PortfolioPoint[];
  positions: Position[];
  trades: Trade[];
  strategies: Strategy[];
  models: Model[];
  candles: Candle[];
  signals: MarketSignal[];
}
