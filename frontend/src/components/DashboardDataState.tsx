import { Panel } from "./Panel";

interface DashboardDataStateProps {
  error: string | null;
  loading: boolean;
  empty: boolean;
  emptyMessage: string;
}

export function DashboardDataState({ error, loading, empty, emptyMessage }: DashboardDataStateProps) {
  if (loading) {
    return <Panel className="p-6 text-sm text-[#778480]">Cargando datos almacenados…</Panel>;
  }
  if (error) {
    return <Panel className="p-6 text-sm text-[#c43f55]">{error}</Panel>;
  }
  if (empty) {
    return <Panel className="p-6 text-sm text-[#778480]">{emptyMessage}</Panel>;
  }
  return null;
}
