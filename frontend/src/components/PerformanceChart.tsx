import { ColorType, LineSeries, createChart } from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { PortfolioPoint } from "../types/dashboard";

interface PerformanceChartProps {
  data: PortfolioPoint[];
}

export function PerformanceChart({ data }: PerformanceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      height: 300,
      width: container.clientWidth,
      layout: { background: { type: ColorType.Solid, color: "#ffffff" }, textColor: "#85918d", fontFamily: "DM Sans, sans-serif" },
      grid: { vertLines: { color: "#f4f6f3" }, horzLines: { color: "#eef1ed" } },
      rightPriceScale: { borderColor: "#e6ebe5" },
      timeScale: { borderColor: "#e6ebe5" },
    });
    const portfolio = chart.addSeries(LineSeries, { color: "#16755b", lineWidth: 3, title: "Portfolio" });
    const benchmark = chart.addSeries(LineSeries, { color: "#9aa6a0", lineWidth: 2, lineStyle: 2, title: "Benchmark" });
    portfolio.setData(data.map(({ time, value }) => ({ time, value })));
    benchmark.setData(data.map(({ time, benchmark: value }) => ({ time, value })));
    chart.timeScale().fitContent();

    const observer = new ResizeObserver(([entry]) => chart.applyOptions({ width: entry.contentRect.width }));
    observer.observe(container);
    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [data]);

  return <div ref={containerRef} aria-label="Portfolio and benchmark performance chart" />;
}
