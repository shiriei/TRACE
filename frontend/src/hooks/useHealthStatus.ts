import { useState, useEffect, useCallback } from 'react';
import { ConnectionState } from '../types';
import { fetchHealthStatus } from '../services/api';

export function useHealthStatus() {
  const [state, setState] = useState<ConnectionState>({
    isConnected: false,
    isLoading: true,
    data: null,
    error: null,
    lastChecked: null,
  });

  const checkStatus = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const data = await fetchHealthStatus();
      setState({
        isConnected: data.status === 'healthy',
        isLoading: false,
        data,
        error: null,
        lastChecked: new Date(),
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unable to connect to TRACE backend';
      setState({
        isConnected: false,
        isLoading: false,
        data: null,
        error: message,
        lastChecked: new Date(),
      });
    }
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  return { ...state, refetch: checkStatus };
}
