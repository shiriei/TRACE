import { Trace, TraceCategoryFilter, TraceMediaItem } from '../types/trace';
import { DEMO_TRACES } from './demoTraces';
import {
  createBackendTrace,
  fetchBackendTraces,
  fetchTraceAttachments,
  getAttachmentContentUrl,
  uploadTraceAttachment,
  deleteBackendTrace,
} from './api';

/**
 * TRACE Data Service
 *
 * Coordinates persistent SQLite traces and media storage from TRACE backend.
 */
class TraceService {
  private traces: Trace[] = [...DEMO_TRACES];
  private isBackendLoaded = false;

  /**
   * Retrieve all recorded traces with media attachments.
   */
  async getAllTraces(): Promise<Trace[]> {
    if (!this.isBackendLoaded) {
      try {
        const backendTraces = await fetchBackendTraces();
        if (Array.isArray(backendTraces)) {
          if (backendTraces.length > 0) {
            // Load persistent traces and their media attachments
            const mapped: Trace[] = await Promise.all(
              backendTraces.map(async (b) => {
                let media: TraceMediaItem[] = [];
                try {
                  const atts = await fetchTraceAttachments(b.id);
                  if (Array.isArray(atts)) {
                    media = atts.map((att) => ({
                      id: att.id,
                      type: att.media_type,
                      uri: getAttachmentContentUrl(b.id, att.id),
                      filename: att.original_filename || att.stored_filename,
                      createdAt: att.created_at,
                      mimeType: att.mime_type,
                      fileSizeBytes: att.file_size_bytes,
                    }));
                  }
                } catch {
                  media = [];
                }

                return {
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
                  media,
                };
              })
            );
            this.traces = mapped;
          } else {
            // New database without traces: seed with demo observations
            this.traces = [...DEMO_TRACES];
          }
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
   * Add a new trace, persisting to backend SQLite and uploading attachments.
   */
  async addTraceWithAttachments(
    newTrace: Omit<Trace, 'id' | 'createdAt'>,
    photoFile?: File | null,
    audioFile?: File | null
  ): Promise<{ trace: Trace; uploadErrors: string[] }> {
    const locationMode =
      newTrace.locationMode ||
      newTrace.location_mode ||
      (newTrace.latitude != null ? 'manual' : 'unplaced');
    const uploadErrors: string[] = [];

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

      const mediaItems: TraceMediaItem[] = [];

      // 1. Upload photo attachment if selected
      if (photoFile) {
        try {
          const photoAtt = await uploadTraceAttachment(backendData.id, photoFile);
          mediaItems.push({
            id: photoAtt.id,
            type: 'photo',
            uri: getAttachmentContentUrl(backendData.id, photoAtt.id),
            filename: photoAtt.original_filename || photoAtt.stored_filename,
            createdAt: photoAtt.created_at,
            mimeType: photoAtt.mime_type,
            fileSizeBytes: photoAtt.file_size_bytes,
          });
        } catch (err: any) {
          uploadErrors.push(
            `Photo upload failed: ${err.message || 'Could not save photo attachment.'}`
          );
        }
      }

      // 2. Upload audio attachment if selected
      if (audioFile) {
        try {
          const audioAtt = await uploadTraceAttachment(backendData.id, audioFile);
          mediaItems.push({
            id: audioAtt.id,
            type: 'audio',
            uri: getAttachmentContentUrl(backendData.id, audioAtt.id),
            filename: audioAtt.original_filename || audioAtt.stored_filename,
            createdAt: audioAtt.created_at,
            mimeType: audioAtt.mime_type,
            fileSizeBytes: audioAtt.file_size_bytes,
          });
        } catch (err: any) {
          uploadErrors.push(
            `Audio upload failed: ${err.message || 'Could not save audio attachment.'}`
          );
        }
      }

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
        media: mediaItems,
      };

      this.traces = [trace, ...this.traces.filter((t) => t.id !== trace.id)];
      return { trace, uploadErrors };
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
      return { trace, uploadErrors: ['Backend unavailable; saved in local memory.'] };
    }
  }

  /**
   * Add a new trace without attachments (backward compatibility).
   */
  async addTrace(newTrace: Omit<Trace, 'id' | 'createdAt'>): Promise<Trace> {
    const res = await this.addTraceWithAttachments(newTrace);
    return res.trace;
  }

  /**
   * Permanently delete a trace by ID from persistent storage and local state.
   */
  async deleteTrace(id: string): Promise<void> {
    if (!id.startsWith('demo-')) {
      await deleteBackendTrace(id);
    }
    this.traces = this.traces.filter((t) => t.id !== id);
  }
}

export const traceService = new TraceService();

