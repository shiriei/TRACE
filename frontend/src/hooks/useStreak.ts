import { useState, useEffect, useCallback } from 'react';
import { StreakSummaryResponse } from '../types';
import { stickerService } from '../services/stickerService';
import { initCrossTabSync } from '../services/crossTabSync';

export interface UseStreakState {
  streakSummary: StreakSummaryResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useStreak(): UseStreakState {
  const [streakSummary, setStreakSummary] = useState<StreakSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStreak = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const summary = await stickerService.getStreakSummary();
      setStreakSummary(summary);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch streak';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStreak();

    // Ensure cross-tab sync channel is initialized for this hook consumer
    const cleanupSync = initCrossTabSync();

    const handleTraceSaved = () => {
      fetchStreak();
    };
    window.addEventListener('trace:saved', handleTraceSaved);
    return () => {
      window.removeEventListener('trace:saved', handleTraceSaved);
      cleanupSync();
    };
  }, [fetchStreak]);

  return { streakSummary, isLoading, error, refetch: fetchStreak };
}
