import { afterEach, describe, expect, it, vi } from "vitest";

import {
  armStrategyDeployment,
  createStrategyDeployment,
  loadMarket,
  loadModels,
  loadOverview,
  loadStrategyDeployments,
  loadTrades,
} from "./dashboard-api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("dashboard API client", () => {
  it("loads typed persisted dashboard responses", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ market_bar_count: 2, symbol_count: 1 }))
      .mockResolvedValueOnce(response({ symbol: "AAPL", source: "alpaca:iex:raw", timeframe: "1D", candles: [] }))
      .mockResolvedValueOnce(response({ runs: [] }))
      .mockResolvedValueOnce(response({ decisions: [] }))
      .mockResolvedValueOnce(response({ deployments: [] }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(loadOverview()).resolves.toMatchObject({ market_bar_count: 2, symbol_count: 1 });
    await expect(loadMarket()).resolves.toMatchObject({ symbol: "AAPL", candles: [] });
    await expect(loadModels()).resolves.toEqual([]);
    await expect(loadTrades()).resolves.toEqual([]);
    await expect(loadStrategyDeployments()).resolves.toEqual([]);
    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/dashboard/overview");
  });

  it("sends deployment mutations only with the operator control token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({}));
    vi.stubGlobal("fetch", fetchMock);

    await createStrategyDeployment({
      name: "AAPL research",
      model_version: "reviewed-v1",
      strategy_version: "ml-strategy-v1",
      feature_version: "features-v1",
      target_version: "targets-v1",
      source: "alpaca:iex:raw",
      timeframe: "1D",
      symbols: ["AAPL"],
      buy_threshold: "0.6",
      sell_threshold: "0.4",
      order_quantity: "10",
      risk_limits: {
        maximum_position_size_pct: "0.1",
        maximum_portfolio_exposure: "0.4",
        maximum_daily_loss_pct: "0.03",
        maximum_drawdown_pct: "0.1",
        stop_loss_pct: "0.04",
        take_profit_pct: "0.08",
        max_trades_per_day: "4",
        minimum_cash_reserve: "1000",
      },
    }, "local-control");
    await armStrategyDeployment("deployment-1", "local-control");

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/control/strategy-deployments", expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ "X-Alyntiq-Control-Token": "local-control" }),
    }));
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/control/strategy-deployments/deployment-1/arm", expect.objectContaining({ method: "POST" }));
  });

  it("surfaces a failed API response instead of returning presentation data", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));

    await expect(loadOverview()).rejects.toThrow("Dashboard request failed (503)");
  });
});

function response(body: object) {
  return { ok: true, json: async () => body };
}
