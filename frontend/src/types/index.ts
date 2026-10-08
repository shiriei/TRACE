/**
 * Backend Health Status Contract
 */
export interface HealthResponse {
  status: string;
  project: string;
  version: string;
  timestamp: string;
  environment: string;
}

/**
 * Frontend Connection State
 */
export interface ConnectionState {
  isConnected: boolean;
  isLoading: boolean;
  data: HealthResponse | null;
  error: string | null;
  lastChecked: Date | null;
}

/**
 * Placeholder Navigation Sections (Phase 0 Foundation)
 */
export type ActiveTab = 'overview' | 'map' | 'capture' | 'missions' | 'insights' | 'history';

export interface PlannedModule {
  id: ActiveTab;
  title: string;
  tagline: string;
  phase: string;
  description: string;
}
