import { Trace, TraceCategoryFilter } from '../types/trace';
import { DEMO_TRACES } from './demoTraces';
import { createBackendTrace, fetchBackendTraces } from './api';

/**
 * TRACE Data Service
 *
 * Coordinates persistent SQLite traces from TRACE backend and local demo observations.
 */
class TraceService {
  private traces: Trace[] = [...DEMO_TRACES];
  private isBackendLoaded = false;

  /**
   * Retrieve all recorded traces.
   */
  async getAllTraces(): Promise<Trace[]> {
    if (!this.isBackendLoaded) {
      try {
        const backendTraces = await fetchBackendTraces();
        if (Array.isArray(backendTraces)) {
          const mapped: Trace[] = backendTraces.map((b) => ({
            id: b.id,
            title: b.title,
            description: b.summary || b.observation,
            category: b.category,
            latitude: b.latitude,
            longitude: b.longitude,
            locationMode: b.location_mode,
            location_mode: b.location_mode,
            createdAt: b.created_at,
            observation: b.observation,
            summary: b.summary,
            tags: b.tags || [],
            sensory_type: b.sensory_type,
            confidence: b.confidence,
            photo_path: b.photo_path,
            audio_path: b.audio_path,
            media: [],
          }));

          // Merge: backend traces first, then demo traces not conflicting
          const existingIds = new Set(mapped.map((t) => t.id));
          const remainingDemo = this.traces.filter((t) => !existingIds.has(t.id));
          this.traces = [...mapped, ...remainingDemo];
          this.isBackendLoaded = true;
        }
      } catch {
        // Backend not currently available; use existing memory store
      }
    }
    return [...this.traces];
  }

  /**
   * Retrieve traces filtered by category.
   */
  async getTracesByCategory(filter: TraceCategoryFilter): Promise<Trace[]> {
    const all = await this.getAllTraces();
    if (filter === 'All') {
      return all;
    }
    return all.filter((t) => t.category === filter);
  }

  /**
   * Retrieve a single trace by ID.
   */
  async getTraceById(id: string): Promise<Trace | undefined> {
    const all = await this.getAllTraces();
    return all.find((t) => t.id === id);
  }

  /**
   * Calculate discovery counts per category.
   */
  async getCategoryCounts(): Promise<Record<string, number>> {
    const all = await this.getAllTraces();
    const counts: Record<string, number> = {
      All: all.length,
      Nature: 0,
      Sound: 0,
      Structure: 0,
      Mystery: 0,
      Personal: 0,
    };

    for (const trace of all) {
      counts[trace.category] = (counts[trace.category] || 0) + 1;
    }

    return counts;
  }

  /**
   * Add a new trace, persisting to backend SQLite when reachable.
   */
  async addTrace(newTrace: Omit<Trace, 'id' | 'createdAt'>): Promise<Trace> {
    const locationMode = newTrace.locationMode || newTrace.location_mode || (newTrace.latitude != null ? 'manual' : 'unplaced');

    try {
      const backendData = await createBackendTrace({
        observation: newTrace.observation || newTrace.title,
        latitude: newTrace.latitude,
        longitude: newTrace.longitude,
        location_mode: locationMode,
        category: newTrace.category,
        title: newTrace.title,
        summary: newTrace.summary || newTrace.description,
        tags: newTrace.tags,
        sensory_type: newTrace.sensory_type,
      });

      const trace: Trace = {
        ...newTrace,
        id: backendData.id,
        createdAt: backendData.created_at || new Date().toISOString(),
        locationMode: backendData.location_mode,
        location_mode: backendData.location_mode,
        latitude: backendData.latitude,
        longitude: backendData.longitude,
        title: backendData.title,
        category: backendData.category,
        observation: backendData.observation,
        summary: backendData.summary,
        tags: backendData.tags || [],
        sensory_type: backendData.sensory_type,
        confidence: backendData.confidence,
        media: newTrace.media || [],
      };

      this.traces = [trace, ...this.traces.filter((t) => t.id !== trace.id)];
      return trace;
    } catch {
      // Local fallback
      const trace: Trace = {
        ...newTrace,
        id: `trace-${Date.now()}`,
        createdAt: new Date().toISOString(),
        locationMode,
        location_mode: locationMode,
        media: newTrace.media || [],
      };
      this.traces = [trace, ...this.traces];
      return trace;
    }
  }
}

export const traceService = new TraceService();
