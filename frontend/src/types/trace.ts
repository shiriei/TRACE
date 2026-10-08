/**
 * TRACE — Domain Data Model (Phase 1 Revision)
 *
 * Core concept:
 * "This is not where the world is. This is where YOU noticed something."
 *
 * Designed as a whimsical, lasting personal exploration memory.
 */

export type TraceCategory = 'Nature' | 'Sound' | 'Structure' | 'Mystery' | 'Personal';

export const TRACE_CATEGORIES: readonly TraceCategory[] = [
  'Nature',
  'Sound',
  'Structure',
  'Mystery',
  'Personal',
] as const;

export type TraceCategoryFilter = 'All' | TraceCategory;

export interface GeoLocation {
  latitude: number;
  longitude: number;
}

/**
 * Supported media capture types for future field recordings.
 */
export type MediaType = 'photo' | 'video' | 'audio' | 'voice' | 'other';

/**
 * Base properties shared across all field media captures.
 */
export interface BaseMediaItem {
  id: string;
  type: MediaType;
  uri: string; // Local reference / file URI / object URL
  filename: string;
  createdAt: string; // ISO 8601
  caption?: string;
  mimeType?: string;
  fileSizeBytes?: number;
}

export interface PhotoMediaItem extends BaseMediaItem {
  type: 'photo';
  thumbnailUri?: string;
  width?: number;
  height?: number;
}

export interface VideoMediaItem extends BaseMediaItem {
  type: 'video';
  duration?: number; // In seconds
  thumbnailUri?: string;
  resolution?: string;
}

export interface AudioMediaItem extends BaseMediaItem {
  type: 'audio';
  duration?: number; // In seconds
  sampleRateHz?: number;
}

export interface VoiceMediaItem extends BaseMediaItem {
  type: 'voice';
  duration?: number; // In seconds
  transcriptDraft?: string;
}

export interface GenericMediaItem extends BaseMediaItem {
  type: 'other';
  notes?: string;
}

/**
 * Discriminated union of all possible field media captures.
 */
export type TraceMediaItem =
  | PhotoMediaItem
  | VideoMediaItem
  | AudioMediaItem
  | VoiceMediaItem
  | GenericMediaItem;

export type LocationMode = 'gps' | 'manual' | 'unplaced';

/**
 * A recorded Trace — an enduring observation of curiosity in the physical world.
 */
export interface Trace {
  id: string;
  title: string;
  description: string;
  category: TraceCategory;
  latitude?: number | null;
  longitude?: number | null;
  locationMode?: LocationMode;
  location_mode?: LocationMode;
  createdAt: string; // ISO 8601 string
  created_at?: string;
  observation?: string; // "What I noticed"
  userNotes?: string; // "My notes & field reflections"
  summary?: string;
  tags?: string[];
  sensory_type?: SensoryType;
  confidence?: number;
  photo_path?: string | null;
  audio_path?: string | null;
  media?: TraceMediaItem[]; // Future-proof capture array (empty in Phase 1 demo data)

  /**
   * Extensible slot for Phase 2+ Local AI-generated metadata.
   */
  aiMetadata?: {
    thematicClass?: string;
    sensoryTraits?: string[];
    confidence?: number;
    frontierHints?: string[];
  };
}

export interface TraceCreatePayload {
  observation: string;
  latitude?: number | null;
  longitude?: number | null;
  location_mode?: LocationMode;
  category?: TraceCategory;
  title?: string;
  summary?: string;
  tags?: string[];
  sensory_type?: SensoryType;
}

/**
 * Phase 2 — Local AI Foundation Domain Types
 */
export type SensoryType =
  | 'visual'
  | 'auditory'
  | 'environmental'
  | 'textual'
  | 'personal'
  | 'mixed';

export interface TraceAIResult {
  category: TraceCategory;
  title: string;
  summary: string;
  tags: string[];
  sensory_type: SensoryType;
  confidence: number;
}

export interface AIStatusResponse {
  available: boolean;
  provider: string;
  model: string;
}

export interface AIErrorDetail {
  error: string;
  message: string;
}

