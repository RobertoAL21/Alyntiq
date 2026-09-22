import { ChartNoAxesCombined } from "lucide-react";

import { DashboardDataState } from "../components/DashboardDataState";
import { MarketChart } from "../components/MarketChart";
import { PageHeader } from "../components/PageHeader";
import { Panel } from "../components/Panel";
import { loadMarket } from "../lib/dashboard-api";
import { useDashboardResource } from "../lib/use-dashboard-resource";

export function MarketPage() {
  const { data, error, loading } = useDashboardResource(loadMarket);
  const candles = data?.candles.map((candle) => ({ ...candle, time: candle.timestamp.slice(0, 10) })) ?? [];

  return (
    <>
      <PageHeader eyebrow="Market data" title={data ? `${data.symbol} market view` : "Market view"} description="Stored historical OHLCV bars from the selected source; this view does not fetch a live quote." />
      <DashboardDataState loading={loading} error={error} empty={data !== null && candles.length === 0} emptyMessage="No hay barras almacenadas para AAPL con la fuente y timeframe seleccionados." />
      {data && candles.length > 0 ? <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <Panel className="p-5"><div className="mb-5 flex items-center justify-between"><div><h2 className="font-display font-semibold text-[#24302d]">Price and volume</h2><p className="mt-1 text-sm text-[#7b8884]">{data.timeframe} · {data.source} · {candles.length} stored bars</p></div><ChartNoAxesCombined className="text-[#24745c]" size={18} /></div><MarketChart data={candles} symbol={data.symbol} /></Panel>
        <Panel className="p-5"><h2 className="font-display font-semibold text-[#24302d]">Signal desk</h2><p className="mt-3 text-sm leading-6 text-[#778480]">No point-in-time model-prediction history is persisted yet, so the dashboard cannot truthfully display trading signals.</p></Panel>
      </section> : null}
    </>
  );
}
