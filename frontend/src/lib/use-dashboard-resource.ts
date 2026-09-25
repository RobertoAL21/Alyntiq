import { useEffect, useState } from "react";

export interface DashboardResource<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
}

export function useDashboardResource<T>(load: () => Promise<T>): DashboardResource<T> {
  const [state, setState] = useState<Omit<DashboardResource<T>, "reload">>({ data: null, error: null, loading: true });
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    load()
      .then((data) => active && setState({ data, error: null, loading: false }))
      .catch(() => active && setState({ data: null, error: "No se pudieron cargar los datos del dashboard.", loading: false }));
    return () => {
      active = false;
    };
  }, [load, reloadKey]);

  return { ...state, reload: () => setReloadKey((value) => value + 1) };
}
