import { useEffect, useState } from "react";

export interface DashboardResource<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

export function useDashboardResource<T>(load: () => Promise<T>): DashboardResource<T> {
  const [state, setState] = useState<DashboardResource<T>>({ data: null, error: null, loading: true });

  useEffect(() => {
    let active = true;
    load()
      .then((data) => active && setState({ data, error: null, loading: false }))
      .catch(() => active && setState({ data: null, error: "No se pudieron cargar los datos del dashboard.", loading: false }));
    return () => {
      active = false;
    };
  }, [load]);

  return state;
}
