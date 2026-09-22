import { BriefcaseBusiness } from "lucide-react";

import { PageHeader } from "../components/PageHeader";
import { Panel } from "../components/Panel";

export function PositionsPage() {
  return (
    <>
      <PageHeader eyebrow="Portfolio" title="Positions" description="Read-only portfolio data is shown only when an authoritative position snapshot is persisted." />
      <Panel className="p-7 text-center">
        <BriefcaseBusiness className="mx-auto text-[#7c8985]" size={28} />
        <h2 className="font-display mt-4 font-semibold text-[#24302d]">No persisted position snapshot</h2>
        <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-[#778480]">The portfolio ledger is an in-memory accounting component and the dashboard does not poll the broker. Showing the old sample positions would be misleading.</p>
      </Panel>
    </>
  );
}
