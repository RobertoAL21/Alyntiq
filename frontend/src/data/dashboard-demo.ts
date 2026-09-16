import type { DashboardSnapshot } from "../types/dashboard";

/**
 * Presentational sample only. It is intentionally separate from backend data
 * until read-only dashboard API endpoints are introduced in a later phase.
 */
export const dashboardSnapshot: DashboardSnapshot = {
  asOf: "2026-09-15T14:30:00Z",
  portfolioValue: 125430.72,
  dailyPnl: 842.16,
  totalPnl: 25430.72,
  cash: 35210.5,
  exposure: 0.7193,
  benchmarkReturn: 0.1684,
  portfolioHistory: [
    { time: "2026-09-01", value: 118400, benchmark: 100000 },
    { time: "2026-09-03", value: 119280, benchmark: 100620 },
    { time: "2026-09-05", value: 120140, benchmark: 101350 },
    { time: "2026-09-08", value: 119760, benchmark: 101180 },
    { time: "2026-09-10", value: 122380, benchmark: 102420 },
    { time: "2026-09-12", value: 124588, benchmark: 103230 },
    { time: "2026-09-15", value: 125430.72, benchmark: 103760 },
  ],
  positions: [
    { symbol: "AAPL", quantity: 110, averagePrice: 196.12, currentPrice: 212.48, marketValue: 23372.8, unrealizedPnl: 1799.6, unrealizedPnlPercent: 0.0834 },
    { symbol: "MSFT", quantity: 48, averagePrice: 421.18, currentPrice: 438.91, marketValue: 21067.68, unrealizedPnl: 851.04, unrealizedPnlPercent: 0.0421 },
    { symbol: "NVDA", quantity: 132, averagePrice: 129.22, currentPrice: 126.35, marketValue: 16678.2, unrealizedPnl: -378.84, unrealizedPnlPercent: -0.0222 },
    { symbol: "SPY", quantity: 68, averagePrice: 564.9, currentPrice: 577.36, marketValue: 39260.48, unrealizedPnl: 847.28, unrealizedPnlPercent: 0.0221 },
  ],
  trades: [
    { timestamp: "2026-09-15T14:20:00Z", symbol: "AAPL", side: "BUY", quantity: 15, price: 212.1, model: "XGBoost v3.2", confidence: 0.78 },
    { timestamp: "2026-09-15T13:55:00Z", symbol: "NVDA", side: "SELL", quantity: 20, price: 126.88, model: "LightGBM v2.4", confidence: 0.71 },
    { timestamp: "2026-09-15T13:30:00Z", symbol: "MSFT", side: "BUY", quantity: 8, price: 438.24, model: "XGBoost v3.2", confidence: 0.74 },
    { timestamp: "2026-09-15T12:45:00Z", symbol: "SPY", side: "BUY", quantity: 12, price: 576.81, model: "Ensemble v1.1", confidence: 0.69 },
  ],
  strategies: [
    { name: "ML Threshold", status: "Active", sharpeRatio: 1.42, totalReturn: 0.2543, maxDrawdown: -0.082 },
    { name: "Momentum Baseline", status: "Research", sharpeRatio: 1.09, totalReturn: 0.187, maxDrawdown: -0.104 },
    { name: "Mean Reversion", status: "Research", sharpeRatio: 0.88, totalReturn: 0.122, maxDrawdown: -0.136 },
  ],
  models: [
    { name: "XGBoost", version: "v3.2", auc: 0.682, precision: 0.641, trainingDate: "2026-09-12", status: "Validated" },
    { name: "LightGBM", version: "v2.4", auc: 0.671, precision: 0.628, trainingDate: "2026-09-12", status: "Validated" },
    { name: "Random Forest", version: "v1.8", auc: 0.642, precision: 0.603, trainingDate: "2026-09-08", status: "Candidate" },
  ],
  candles: [
    { time: "2026-09-04", open: 204.2, high: 206.4, low: 203.8, close: 205.75, volume: 46200000 },
    { time: "2026-09-05", open: 205.5, high: 208.12, low: 204.6, close: 207.28, volume: 51400000 },
    { time: "2026-09-08", open: 207.1, high: 208.05, low: 205.4, close: 206.1, volume: 47600000 },
    { time: "2026-09-09", open: 206.35, high: 209.2, low: 205.96, close: 208.78, volume: 49300000 },
    { time: "2026-09-10", open: 208.5, high: 210.18, low: 207.82, close: 209.44, volume: 43500000 },
    { time: "2026-09-11", open: 209.88, high: 211.54, low: 208.76, close: 210.12, volume: 40200000 },
    { time: "2026-09-12", open: 210.1, high: 213.1, low: 209.45, close: 212.76, volume: 58800000 },
    { time: "2026-09-15", open: 212.36, high: 213.08, low: 210.52, close: 212.48, volume: 36100000 },
  ],
  signals: [
    { timestamp: "2026-09-15T14:15:00Z", name: "XGBoost v3.2", direction: "Bullish", confidence: 0.78 },
    { timestamp: "2026-09-15T13:45:00Z", name: "Momentum filter", direction: "Neutral", confidence: 0.54 },
    { timestamp: "2026-09-15T13:30:00Z", name: "LightGBM v2.4", direction: "Bearish", confidence: 0.71 },
  ],
};
