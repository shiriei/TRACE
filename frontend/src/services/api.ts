import { HealthResponse } from '../types';

/**
 * TRACE API Configuration
 * Supports environment override via VITE_API_URL or defaults to relative '/health'
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const API_ENDPOINTS = {
  health: `${API_BASE_URL}/health`,
  healthV1: `${API_BASE_URL}/api/v1/health`,
  root: `${API_BASE_URL}/`,
} as const;

/**
 * Fetch health status from the TRACE backend.
 */
export async function fetchHealthStatus(): Promise<HealthResponse> {
  const response = await fetch(API_ENDPOINTS.health, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Backend responded with HTTP status ${response.status} (${response.statusText})`);
  }

  return response.json();
}
