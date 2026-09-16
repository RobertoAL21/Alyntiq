import { CandlestickSeries, ColorType, HistogramSeries, createChart } from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { Candle } from "../types/dashboard";

interface MarketChartProps {
  data: Candle[];
}

export function MarketChart({ data }: MarketChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      height: 410,
      width: container.clientWidth,
      layout: { background: { type: ColorType.Solid, color: "#ffffff" }, textColor: "#85918d", fontFamily: "DM Sans, sans-serif" },
      grid: { vertLines: { color: "#f4f6f3" }, horzLines: { color: "#eef1ed" } },
      rightPriceScale: { borderColor: "#e6ebe5" },
      timeScale: { borderColor: "#e6ebe5" },
    });
    const candles = chart.addSeries(CandlestickSeries, {
      upColor: "#259c70",
      downColor: "#de6674",
      borderVisible: false,
      wickUpColor: "#259c70",
      wickDownColor: "#de6674",
    });
    const volume = chart.addSeries(HistogramSeries, { priceFormat: { type: "volume" }, priceScaleId: "volume" });
    chart.priceScale("volume").applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
    candles.setData(data.map(({ time, open, high, low, close }) => ({ time, open, high, low, close })));
    volume.setData(data.map(({ time, open, close, volume: value }) => ({ time, value, color: close >= open ? "#8bd4b0" : "#f1abb3" })));
    chart.timeScale().fitContent();

    const observer = new ResizeObserver(([entry]) => chart.applyOptions({ width: entry.contentRect.width }));
    observer.observe(container);
    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [data]);

  return <div ref={containerRef} aria-label="AAPL candlestick and volume chart" />;
}
