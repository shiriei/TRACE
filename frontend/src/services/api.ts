import { AIStatusResponse, HealthResponse, TraceAIResult } from '../types';

/**
 * TRACE API Configuration
 * Supports environment override via VITE_API_URL or defaults to relative '/health'
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const API_ENDPOINTS = {
  health: `${API_BASE_URL}/health`,
  healthV1: `${API_BASE_URL}/api/v1/health`,
  root: `${API_BASE_URL}/`,
  aiStatus: `${API_BASE_URL}/api/v1/ai/status`,
  aiInterpret: `${API_BASE_URL}/api/v1/ai/interpret-trace`,
  traces: `${API_BASE_URL}/api/v1/traces`,
} as const;

/**
 * Structured TRACE AI Client Error for user-facing failure states.
 */
export class TraceAIError extends Error {
  public readonly userTitle: string;
  public readonly userMessage: string;
  public readonly status?: number;

  constructor(userTitle: string, userMessage: string, status?: number) {
    super(`${userTitle} — ${userMessage}`);
    this.name = 'TraceAIError';
    this.userTitle = userTitle;
    this.userMessage = userMessage;
    this.status = status;
  }
}

/**
 * Fetch health status from the TRACE backend.
 */
export async function fetchHealthStatus(): Promise<HealthResponse> {
  const response = await fetch(API_ENDPOINTS.health, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Backend responded with HTTP status ${response.status} (${response.statusText})`);
  }

  return response.json();
}

/**
 * Probe local LM Studio AI service reachability via TRACE backend.
 */
export async function fetchAIStatus(): Promise<AIStatusResponse> {
  try {
    const response = await fetch(API_ENDPOINTS.aiStatus, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      return {
        available: false,
        provider: 'lm-studio',
        model: 'unknown',
      };
    }

    return response.json();
  } catch {
    return {
      available: false,
      provider: 'lm-studio',
      model: 'unknown',
    };
  }
}

/**
 * Send user observation to TRACE backend for local AI interpretation.
 * Gracefully maps errors to canonical user-friendly failure states.
 */
export async function interpretTraceObservation(observation: string): Promise<TraceAIResult> {
  let response: Response;

  try {
    response = await fetch(API_ENDPOINTS.aiInterpret, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ observation }),
    });
  } catch {
    // Network / backend unreachable
    throw new TraceAIError(
      'Local AI unavailable',
      'Start LM Studio to interpret this trace.',
      503
    );
  }

  if (response.ok) {
    return response.json();
  }

  // Handle specific backend error status codes
  if (response.status === 503) {
    throw new TraceAIError(
      'Local AI unavailable',
      'Start LM Studio to interpret this trace.',
      503
    );
  }

  if (response.status === 504) {
    throw new TraceAIError(
      'TRACE AI took too long to respond.',
      'Try again.',
      504
    );
  }

  // Status 502, 422, or other model parsing failure
  let errorDetail: { error?: string; message?: string } = {};
  try {
    const body = await response.json();
    if (body.detail) {
      errorDetail = body.detail;
    }
  } catch {
    // ignore json parse error
  }

  throw new TraceAIError(
    errorDetail.error || "TRACE couldn't interpret this observation.",
    errorDetail.message || 'Try describing what you noticed in a little more detail.',
    response.status
  );
}

/**
 * Persist a trace to the backend SQLite store.
 */
export async function createBackendTrace(payload: {
  observation: string;
  latitude?: number | null;
  longitude?: number | null;
  location_mode?: 'gps' | 'manual' | 'unplaced';
  category?: string;
  title?: string;
  summary?: string;
  tags?: string[];
  sensory_type?: string;
}): Promise<any> {
  const response = await fetch(API_ENDPOINTS.traces, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(
      typeof errorBody.detail === 'string'
        ? errorBody.detail
        : `Failed to create trace: ${response.status}`
    );
  }

  return response.json();
}

/**
 * Retrieve all persistent traces from backend.
 */
export async function fetchBackendTraces(): Promise<any[]> {
  const response = await fetch(API_ENDPOINTS.traces, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch traces: ${response.status}`);
  }

  return response.json();
}
