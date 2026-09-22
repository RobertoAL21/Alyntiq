import { ChartNoAxesCombined } from "lucide-react";

import { PageHeader } from "../components/PageHeader";
import { Panel } from "../components/Panel";

export function StrategiesPage() {
  return (
    <>
      <PageHeader eyebrow="Research" title="Strategies" description="Comparable strategy results require a persisted research run with its explicit assumptions." />
      <Panel className="p-7 text-center">
        <ChartNoAxesCombined className="mx-auto text-[#7c8985]" size={28} />
        <h2 className="font-display mt-4 font-semibold text-[#24302d]">No persisted strategy leaderboard</h2>
        <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-[#778480]">The baseline strategy command returns a valid historical result, but the current architecture does not store that output. The dashboard will not recreate a backtest or substitute demonstration metrics.</p>
      </Panel>
    </>
  );
}
