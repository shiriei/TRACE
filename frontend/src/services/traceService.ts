import { Trace, TraceCategoryFilter } from '../types/trace';
import { DEMO_TRACES } from './demoTraces';

/**
 * TRACE Data Service (Phase 1 In-Memory / Local Layer)
 *
 * Keeps the data layer decoupled from map and presentation components.
 * Phase 3+ will replace this in-memory collection with backend SQLite persistence
 * without requiring rewrites to the map or marker components.
 */

class TraceService {
  private traces: Trace[] = [...DEMO_TRACES];

  /**
   * Retrieve all recorded traces.
   */
  async getAllTraces(): Promise<Trace[]> {
    return [...this.traces];
  }

  /**
   * Retrieve traces filtered by category.
   */
  async getTracesByCategory(filter: TraceCategoryFilter): Promise<Trace[]> {
    if (filter === 'All') {
      return [...this.traces];
    }
    return this.traces.filter((t) => t.category === filter);
  }

  /**
   * Retrieve a single trace by ID.
   */
  async getTraceById(id: string): Promise<Trace | undefined> {
    return this.traces.find((t) => t.id === id);
  }

  /**
   * Calculate discovery counts per category.
   */
  async getCategoryCounts(): Promise<Record<string, number>> {
    const counts: Record<string, number> = {
      All: this.traces.length,
      Nature: 0,
      Sound: 0,
      Structure: 0,
      Mystery: 0,
      Personal: 0,
    };

    for (const trace of this.traces) {
      counts[trace.category] = (counts[trace.category] || 0) + 1;
    }

    return counts;
  }

  /**
   * Add a new trace to the local in-memory store.
   */
  async addTrace(newTrace: Omit<Trace, 'id' | 'createdAt'>): Promise<Trace> {
    const trace: Trace = {
      ...newTrace,
      media: newTrace.media || [],
      id: `trace-${Date.now()}`,
      createdAt: new Date().toISOString(),
    };
    this.traces.push(trace);
    return trace;
  }
}

export const traceService = new TraceService();
