import { afterEach, describe, expect, it, vi } from "vitest";

import { loadMarket, loadModels, loadOverview, loadTrades } from "./dashboard-api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("dashboard API client", () => {
  it("loads typed persisted dashboard responses", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ market_bar_count: 2, symbol_count: 1 }))
      .mockResolvedValueOnce(response({ symbol: "AAPL", source: "alpaca:iex:raw", timeframe: "1D", candles: [] }))
      .mockResolvedValueOnce(response({ runs: [] }))
      .mockResolvedValueOnce(response({ decisions: [] }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(loadOverview()).resolves.toMatchObject({ market_bar_count: 2, symbol_count: 1 });
    await expect(loadMarket()).resolves.toMatchObject({ symbol: "AAPL", candles: [] });
    await expect(loadModels()).resolves.toEqual([]);
    await expect(loadTrades()).resolves.toEqual([]);
    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/dashboard/overview");
  });

  it("surfaces a failed API response instead of returning presentation data", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));

    await expect(loadOverview()).rejects.toThrow("Dashboard request failed (503)");
  });
});

function response(body: object) {
  return { ok: true, json: async () => body };
}
