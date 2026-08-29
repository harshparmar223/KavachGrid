// KAVACHGRID 3.0 — API Hook. Phase 12.
import { useState, useEffect, useCallback } from 'react';

export function useApi<T>(fetcher: () => Promise<T>, deps: any[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<any>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetcher();
      setData(response);
      setError(null);
    } catch (err) {
      setError(err);
      console.error('API Error:', err);
    } finally {
      setLoading(false);
    }
  }, deps);

  useEffect(() => {
    execute();
  }, [execute]);

  return { data, loading, error, mutate: execute };
}
