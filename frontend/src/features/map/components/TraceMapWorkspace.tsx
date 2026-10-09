import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { Trace, TraceCategory, TraceCategoryFilter, SensoryType, TraceAIResult } from '../../../types';
import { traceService } from '../../../services/traceService';
import { TraceMap, PlacementState } from './TraceMap';
import { formatTimestamp } from '../../../utils/formatters';
import { TRACE_ILLUSTRATIONS, CATEGORY_MEANINGS } from './TraceThumbnails';
import { TraceAIInterpreter } from '../../ai';
import { StickerGardenJourney, DailyRewardModal } from '../../stickers';
import { OwnedSticker, StickerPackDefinition } from '../../../types/sticker';
import { broadcastTraceSaved } from '../../../services/crossTabSync';

export interface TraceMapWorkspaceProps {
  activeTab?: 'map' | 'traces' | 'log' | 'stickers';
  onTabChange?: (tab: 'map' | 'traces' | 'log' | 'stickers') => void;
}

interface PendingTrace {
  observation: string;
  category?: TraceCategory;
  title?: string;
  summary?: string;
  tags?: string[];
  sensory_type?: SensoryType;
  photoFile?: File | null;
  audioFile?: File | null;
}


const CATEGORY_ICONS: Record<TraceCategory, string> = {
  Nature: '🌿',
  Sound: '🔊',
  Structure: '🏛',
  Mystery: '🔎',
  Personal: '💙',
};

const FIVE_TRACE_WAYS = [
  {
    key: 'nature',
    icon: '🌿',
    title: 'Nature',
    color: 'var(--nature)',
    description: 'Notice something living, growing, changing, or naturally occurring around you.',
    examples: ['plants', 'moss', 'flowers', 'birds', 'insects', 'natural patterns'],
  },
  {
    key: 'sound',
    icon: '🔊',
    title: 'Sound',
    color: 'var(--sound)',
    description: 'Listen for something unusual, beautiful, hidden, or easy to miss.',
    examples: ['bird calls', 'echoes', 'flowing water', 'machinery', 'unusual rhythms', 'overlapping sounds'],
  },
  {
    key: 'structure',
    icon: '🏛',
    title: 'Structure',
    color: 'var(--structure)',
    description: 'Discover something built, arranged, engineered, or hidden in the environment.',
    examples: ['old walls', 'bridges', 'drains', 'pipes', 'buildings', 'road patterns', 'infrastructure'],
  },
  {
    key: 'mystery',
    icon: '🔎',
    title: 'Mystery',
    color: 'var(--mystery)',
    description: 'Find something strange, unexplained, unexpected, or worth investigating.',
    examples: ['unexplained marks', 'strange objects', 'unusual patterns', 'something out of place', 'physical clues'],
  },
  {
    key: 'personal',
    icon: '💙',
    title: 'Personal',
    color: 'var(--personal)',
    description: 'Keep something that mattered to you — a moment, place, object, or memory.',
    examples: ['meaningful places', 'memorable moments', 'personal discoveries', 'things worth revisiting'],
  },
];

export const TraceMapWorkspace: React.FC<TraceMapWorkspaceProps> = ({
  activeTab,
  onTabChange,
}) => {
  const [allTraces, setAllTraces] = useState<Trace[]>([]);
  const [activeFilter, setActiveFilter] = useState<TraceCategoryFilter>('All');
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [categoryCounts, setCategoryCounts] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [recenterTrigger, setRecenterTrigger] = useState<number>(0);
  const [internalNavTab, setInternalNavTab] = useState<'map' | 'traces' | 'log' | 'stickers'>('map');
  const activeNavTab = activeTab ?? internalNavTab;

  const handleNavTabChange = (tab: 'map' | 'traces' | 'log' | 'stickers') => {
    if (onTabChange) {
      onTabChange(tab);
    } else {
      setInternalNavTab(tab);
    }
  };

  // Trace placement state
  const [pendingTrace, setPendingTrace] = useState<PendingTrace | null>(null);
  const [showPlacementModal, setShowPlacementModal] = useState<boolean>(false);
  const [placement, setPlacement] = useState<PlacementState | null>(null);
  const [uploadAlert, setUploadAlert] = useState<string | null>(null);
  const [isPlacingInProgress, setIsPlacingInProgress] = useState<boolean>(false);
  const isConfirmingRef = useRef<boolean>(false);
  const [interpreterKey, setInterpreterKey] = useState<number>(0);

  // Daily Reward / Milestone celebration modal state
  const [celebrationReward, setCelebrationReward] = useState<{
    awardedSticker?: OwnedSticker | null;
    streak: number;
    longestStreak: number;
    milestonesUnlocked: StickerPackDefinition[];
    isPoolExhausted?: boolean;
  } | null>(null);

  // Unified reward celebration handler for both unplaced and map-placed traces
  const handleRewardCelebration = useCallback((effectiveReward?: any) => {
    if (!effectiveReward) return;

    const hasDailySticker = Boolean(effectiveReward.daily_sticker_awarded);
    const hasMilestones = (effectiveReward.milestones_unlocked || []).length > 0;
    const isStreakExtension = Boolean(effectiveReward.streak_extended);

    // Open celebration if:
    // 1. A daily sticker is awarded, OR
    // 2. One or more milestone packs are unlocked, OR
    // 3. This qualifying trace extended the streak (including when starter pool is exhausted)
    if (hasDailySticker || hasMilestones || isStreakExtension) {
      setCelebrationReward({
        awardedSticker: effectiveReward.daily_sticker_awarded || null,
        streak: effectiveReward.streak_summary.current_streak,
        longestStreak: effectiveReward.streak_summary.longest_streak,
        milestonesUnlocked: effectiveReward.milestones_unlocked || [],
        isPoolExhausted: !hasDailySticker && isStreakExtension,
      });
    }
  }, []);

  // Delete trace state
  const [traceToDelete, setTraceToDelete] = useState<Trace | null>(null);
  const [isDeleteInProgress, setIsDeleteInProgress] = useState<boolean>(false);
  const isDeleteInProgressRef = useRef<boolean>(false);
  const [feedbackAlert, setFeedbackAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Load real React trace data
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [traces, counts] = await Promise.all([
          traceService.getAllTraces(),
          traceService.getCategoryCounts(),
        ]);
        setAllTraces(traces);
        setCategoryCounts(counts);
        if (traces.length > 0) {
          const firstPlaced = traces.find((t) => t.latitude != null && t.longitude != null);
          setSelectedTraceId(firstPlaced ? firstPlaced.id : traces[0].id);
        }
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  // Filter visible traces
  const visibleTraces = useMemo(() => {
    if (activeFilter === 'All') return allTraces;
    return allTraces.filter((t) => t.category === activeFilter);
  }, [allTraces, activeFilter]);

  const handleSelectTrace = useCallback((trace: Trace) => {
    setSelectedTraceId(trace.id);
  }, []);

  const handleFilterChange = useCallback((filter: TraceCategoryFilter) => {
    setActiveFilter(filter);
    setRecenterTrigger((prev) => prev + 1);
    if (selectedTraceId) {
      const trace = allTraces.find((t) => t.id === selectedTraceId);
      if (trace && filter !== 'All' && trace.category !== filter) {
        setSelectedTraceId(null);
      }
    }
  }, [allTraces, selectedTraceId]);

  const handleRecenter = useCallback(() => {
    setRecenterTrigger((prev) => prev + 1);
  }, []);

  // Trigger placement flow when user provides observation and optional attachments
  const handleStartPlacement = useCallback(
    (data: {
      observation: string;
      result?: TraceAIResult | null;
      photoFile?: File | null;
      audioFile?: File | null;
      selectedCategory?: TraceCategory | null;
    }) => {
      // Category Precedence Rule:
      // 1. Explicitly selected category takes highest precedence (data.selectedCategory).
      // 2. AI result category is fallback if available (data.result?.category).
      // 3. If active filter is a specific category (not 'All'), use that.
      // 4. Default to 'Personal'.
      const chosenCategory: TraceCategory =
        data.selectedCategory ||
        (data.result?.category as TraceCategory) ||
        (activeFilter !== 'All' ? activeFilter : 'Personal');

      setPendingTrace({
        observation: data.observation,
        category: chosenCategory,
        title: data.result?.title || data.observation.slice(0, 50),
        summary: data.result?.summary || data.observation,
        tags: data.result?.tags || [],
        sensory_type: data.result?.sensory_type || (data.audioFile ? 'auditory' : 'visual'),
        photoFile: data.photoFile || null,
        audioFile: data.audioFile || null,
      });
      setShowPlacementModal(true);
    },
    [activeFilter]
  );

  // Option 1: GPS Placement
  const handleSelectGps = useCallback(() => {
    setShowPlacementModal(false);

    if (!navigator.geolocation) {
      setPlacement({ mode: 'manual', position: [51.5074, -0.0915] });
      document.getElementById('map')?.scrollIntoView({ behavior: 'smooth' });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords: [number, number] = [pos.coords.latitude, pos.coords.longitude];
        setPlacement({ mode: 'gps', position: coords });
        document.getElementById('map')?.scrollIntoView({ behavior: 'smooth' });
      },
      (err) => {
        console.warn('Geolocation probe unavailable or denied:', err.message);
        setPlacement({ mode: 'manual', position: [51.5074, -0.0915] });
        document.getElementById('map')?.scrollIntoView({ behavior: 'smooth' });
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  }, []);

  // Option 2: Manual Placement
  const handleSelectManual = useCallback(() => {
    setShowPlacementModal(false);
    const initialCenter: [number, number] =
      visibleTraces.length > 0 && visibleTraces[0].latitude != null && visibleTraces[0].longitude != null
        ? [visibleTraces[0].latitude, visibleTraces[0].longitude]
        : [51.5074, -0.0915];
    setPlacement({ mode: 'manual', position: initialCenter });
    document.getElementById('map')?.scrollIntoView({ behavior: 'smooth' });
  }, [visibleTraces]);

  // Option 3 / Cancel: Save as Unplaced Trace
  const handleSaveUnplaced = useCallback(async () => {
    if (isConfirmingRef.current || !pendingTrace) return;
    isConfirmingRef.current = true;
    setIsPlacingInProgress(true);
    setShowPlacementModal(false);
    setPlacement(null);

    try {
      const { trace, uploadErrors, reward, backendSaved } = await traceService.addTraceWithAttachments(
        {
          observation: pendingTrace.observation,
          title: pendingTrace.title || pendingTrace.observation.slice(0, 50),
          description: pendingTrace.summary || pendingTrace.observation,
          category: pendingTrace.category || 'Personal',
          latitude: null,
          longitude: null,
          locationMode: 'unplaced',
          location_mode: 'unplaced',
          tags: pendingTrace.tags || [],
          sensory_type: pendingTrace.sensory_type,
          media: [],
        },
        pendingTrace.photoFile,
        pendingTrace.audioFile
      );

      if (uploadErrors.length > 0) {
        setUploadAlert(uploadErrors.join(' | '));
      }

      setAllTraces((prev) => [trace, ...prev.filter((t) => t.id !== trace.id)]);
      setSelectedTraceId(trace.id);
      const counts = await traceService.getCategoryCounts();
      setCategoryCounts(counts);
      setPendingTrace(null);
      setInterpreterKey((prev) => prev + 1);
      if (backendSaved) {
        broadcastTraceSaved();
      }

      // If backend confirmed a daily sticker or milestone reward or streak extension, trigger modal
      handleRewardCelebration(reward || (trace as any).reward);
    } catch (err: any) {
      setUploadAlert(`Failed to save trace: ${err.message || 'Unknown error'}. Please try again.`);
    } finally {
      isConfirmingRef.current = false;
      setIsPlacingInProgress(false);
    }
  }, [pendingTrace, handleRewardCelebration]);

  // Confirm placement from Map banner
  const handleConfirmPlacement = useCallback(async () => {
    if (isConfirmingRef.current || !placement || !pendingTrace) return;
    isConfirmingRef.current = true;
    setIsPlacingInProgress(true);

    try {
      const { trace, uploadErrors, reward, backendSaved } = await traceService.addTraceWithAttachments(
        {
          observation: pendingTrace.observation,
          title: pendingTrace.title || pendingTrace.observation.slice(0, 50),
          description: pendingTrace.summary || pendingTrace.observation,
          category: pendingTrace.category || 'Personal',
          latitude: placement.position[0],
          longitude: placement.position[1],
          locationMode: placement.mode,
          location_mode: placement.mode,
          tags: pendingTrace.tags || [],
          sensory_type: pendingTrace.sensory_type,
          media: [],
        },
        pendingTrace.photoFile,
        pendingTrace.audioFile
      );

      if (uploadErrors.length > 0) {
        setUploadAlert(uploadErrors.join(' | '));
      }

      setAllTraces((prev) => [trace, ...prev.filter((t) => t.id !== trace.id)]);
      setSelectedTraceId(trace.id);
      const counts = await traceService.getCategoryCounts();
      setCategoryCounts(counts);

      // On successful confirmation: exit placement mode, clear pending state, and reset creation form
      setPlacement(null);
      setPendingTrace(null);
      setInterpreterKey((prev) => prev + 1);
      if (backendSaved) {
        broadcastTraceSaved();
      }

      // If backend confirmed a daily sticker or milestone reward or streak extension, trigger modal
      handleRewardCelebration(reward || (trace as any).reward);
    } catch (err: any) {
      // If saving fails: retain pendingTrace and placement state so user can retry!
      setUploadAlert(`Failed to place trace: ${err.message || 'Unknown error'}. Please try again.`);
    } finally {
      isConfirmingRef.current = false;
      setIsPlacingInProgress(false);
    }
  }, [placement, pendingTrace, handleRewardCelebration]);

  const handleCancelPlacement = useCallback(() => {
    setPlacement(null);
  }, []);

  // Delete trace handlers
  const handleRequestDelete = useCallback((trace: Trace) => {
    setTraceToDelete(trace);
  }, []);

  const handleCancelDelete = useCallback(() => {
    if (isDeleteInProgressRef.current) return;
    setTraceToDelete(null);
  }, []);

  const handleConfirmDelete = useCallback(async () => {
    if (!traceToDelete || isDeleteInProgressRef.current) return;
    isDeleteInProgressRef.current = true;
    setIsDeleteInProgress(true);
    setFeedbackAlert(null);

    try {
      await traceService.deleteTrace(traceToDelete.id);
      setAllTraces((prev) => prev.filter((t) => t.id !== traceToDelete.id));
      if (selectedTraceId === traceToDelete.id) {
        setSelectedTraceId(null);
      }
      const counts = await traceService.getCategoryCounts();
      setCategoryCounts(counts);
      setTraceToDelete(null);
      setFeedbackAlert({
        type: 'success',
        message: 'Trace deleted successfully.',
      });
    } catch (err: any) {
      setFeedbackAlert({
        type: 'error',
        message: `Failed to delete trace: ${err.message || 'Unknown error'}. Please try again.`,
      });
    } finally {
      isDeleteInProgressRef.current = false;
      setIsDeleteInProgress(false);
    }
  }, [traceToDelete, selectedTraceId]);


  // Critters slide in on scroll
  useEffect(() => {
    const critters = document.querySelectorAll('.critter');
    if (!critters.length) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => e.target.classList.toggle('in', e.isIntersecting));
      },
      { threshold: 0.15 }
    );
    critters.forEach((c) => io.observe(c));
    return () => io.disconnect();
  }, []);

  // Drifting bee as user scrolls down the page
  useEffect(() => {
    const bee = document.getElementById('bee');
    if (!bee) return;
    function moveBee() {
      const h = document.documentElement.scrollHeight - window.innerHeight || 1;
      const p = window.scrollY / h;
      const x = window.innerWidth * (0.5 + 0.42 * Math.sin(p * Math.PI * 5));
      const y = 90 + p * (window.innerHeight - 190);
      if (bee) bee.style.transform = `translate(${x}px,${y}px)`;
    }
    window.addEventListener('scroll', moveBee, { passive: true });
    window.addEventListener('resize', moveBee);
    moveBee();
    return () => {
      window.removeEventListener('scroll', moveBee);
      window.removeEventListener('resize', moveBee);
    };
  }, []);

  return (
    <>
      {/* Reusable hand-drawn SVG symbols from original Trace · HTML */}
      <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden="true">
        <defs>
          <symbol id="bird" viewBox="0 0 80 70">
            <path
              d="M12 38c0-16 14-26 30-24 12 1 20 10 22 22 1 14-12 24-28 22C22 56 12 50 12 38z"
              fill="#d6457f"
              stroke="#2c4a3f"
              strokeWidth="2.5"
            />
            <path
              d="M40 30c10-2 18 4 20 14-8 4-20 2-24-6z"
              fill="#e8a33d"
              stroke="#2c4a3f"
              strokeWidth="2.5"
            />
            <path d="M12 38L2 34l8 10z" fill="#e8a33d" stroke="#2c4a3f" strokeWidth="2.5" />
            <path d="M60 36l-10-6 4 12z" fill="#fbf4de" stroke="#2c4a3f" strokeWidth="2" />
            <circle cx="26" cy="30" r="3" fill="#2c4a3f" />
            <path d="M34 60v8M44 60v8" stroke="#2c4a3f" strokeWidth="2.5" strokeLinecap="round" />
          </symbol>

          <symbol id="deer" viewBox="0 0 120 130">
            <path
              d="M30 20l-8-14M30 20l-18-6M30 20l6-14M46 20l8-14M46 20l18-6M46 20l-4-12"
              stroke="#8a56c9"
              strokeWidth="4"
              strokeLinecap="round"
              fill="none"
            />
            <path
              d="M38 38c-6 10-4 22 6 28l10 2 4-24z"
              fill="#e1b27d"
              stroke="#2c4a3f"
              strokeWidth="2.5"
            />
            <path
              d="M34 66c8 6 40 10 62 0 6-2 10 4 8 12-2 16-14 20-36 22-22-2-34-8-34-22z"
              fill="#e1b27d"
              stroke="#2c4a3f"
              strokeWidth="2.5"
            />
            <path d="M44 96v28M58 98v26M84 98v26M98 92v32" stroke="#2c4a3f" strokeWidth="4" strokeLinecap="round" />
            <circle cx="48" cy="48" r="2.6" fill="#2c4a3f" />
            <path d="M42 60q5 3 10 0" stroke="#2c4a3f" strokeWidth="2" fill="none" />
            <path d="M40 34l-4-8 8 4z" fill="#d6457f" />
          </symbol>

          <symbol id="hedge" viewBox="0 0 100 60">
            <path
              d="M8 46C6 24 24 6 52 8c26 2 42 18 40 38z"
              fill="#8c6a4a"
              stroke="#2c4a3f"
              strokeWidth="2.5"
            />
            <path
              d="M20 14l4 8M34 8l2 10M50 6v10M66 9l-2 10M80 16l-6 8M88 28l-8 4"
              stroke="#2c4a3f"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            <path
              d="M8 46c0-8 4-14 10-16 6 4 4 18-2 22z"
              fill="#f0d3a8"
              stroke="#2c4a3f"
              strokeWidth="2.5"
            />
            <circle cx="14" cy="42" r="2" fill="#2c4a3f" />
            <path d="M26 54v4M72 54v4" stroke="#2c4a3f" strokeWidth="3" strokeLinecap="round" />
          </symbol>

          <symbol id="fox" viewBox="0 0 120 80">
            <path
              d="M96 52c14-6 24-22 18-34-14 0-26 14-26 30z"
              fill="#e8873d"
              stroke="#2c4a3f"
              strokeWidth="2.5"
            />
            <path
              d="M110 22c0 6-2 10-6 14"
              stroke="#fbf4de"
              strokeWidth="5"
              fill="none"
              strokeLinecap="round"
            />
            <path
              d="M26 40c6-14 30-18 62-8 8 4 8 22 0 28H34c-8 0-12-10-8-20z"
              fill="#e8873d"
              stroke="#2c4a3f"
              strokeWidth="2.5"
            />
            <path
              d="M14 28l8-14 10 12 12-2 4 14-18 8z"
              fill="#e8873d"
              stroke="#2c4a3f"
              strokeWidth="2.5"
            />
            <circle cx="26" cy="32" r="2.4" fill="#2c4a3f" />
            <circle cx="12" cy="40" r="3" fill="#2c4a3f" />
            <path d="M40 62v14M80 62v14" stroke="#2c4a3f" strokeWidth="4" strokeLinecap="round" />
          </symbol>

          <symbol id="beesym" viewBox="0 0 50 40">
            <ellipse
              cx="18"
              cy="9"
              rx="8"
              ry="12"
              fill="#fff"
              fillOpacity=".8"
              stroke="#2c4a3f"
              strokeWidth="1.5"
              transform="rotate(-25 18 9)"
            />
            <ellipse
              cx="30"
              cy="9"
              rx="8"
              ry="12"
              fill="#fff"
              fillOpacity=".8"
              stroke="#2c4a3f"
              strokeWidth="1.5"
              transform="rotate(25 30 9)"
            />
            <ellipse cx="25" cy="26" rx="16" ry="10" fill="#f3c63f" stroke="#2c4a3f" strokeWidth="2" />
            <path d="M20 17v18M28 17v18" stroke="#2c4a3f" strokeWidth="4" />
            <circle cx="12" cy="24" r="1.6" fill="#2c4a3f" />
          </symbol>
        </defs>
      </svg>

      <main className="shell">
        {/* Left Navigation */}
        <nav className="paper" aria-label="Main">
          <a
            href="#traces"
            aria-current={activeNavTab === 'traces' ? 'page' : undefined}
            onClick={(e) => {
              e.preventDefault();
              handleNavTabChange('traces');
              document.getElementById('notes')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            <svg viewBox="0 0 24 24">
              <path d="M12 21s-7-6-7-11a7 7 0 0114 0c0 5-7 11-7 11z" />
              <circle cx="12" cy="10" r="2.5" />
            </svg>
            Traces
          </a>

          <a
            href="#map"
            aria-current={activeNavTab === 'map' ? 'page' : undefined}
            onClick={(e) => {
              e.preventDefault();
              handleNavTabChange('map');
              document.getElementById('map')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            <svg viewBox="0 0 24 24">
              <path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2z" />
              <path d="M9 4v14M15 6v14" />
            </svg>
            Map
          </a>

          <a
            href="#how"
            aria-current={activeNavTab === 'log' ? 'page' : undefined}
            onClick={(e) => {
              e.preventDefault();
              handleNavTabChange('log');
              document.getElementById('how')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            <svg viewBox="0 0 24 24">
              <path d="M4 5h7a1 1 0 011 1v13a3 3 0 00-3-2H4zM20 5h-7a1 1 0 00-1 1v13a3 3 0 013-2h5z" />
            </svg>
            Log
          </a>

          <a
            href="#stickers"
            aria-current={activeNavTab === 'stickers' ? 'page' : undefined}
            onClick={(e) => {
              e.preventDefault();
              handleNavTabChange('stickers');
            }}
          >
            <svg viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 2a3 3 0 0 0-3 3c0 1.66 1.34 3 3 3s3-1.34 3-3a3 3 0 0 0-3-3z" />
              <path d="M12 22a3 3 0 0 0 3-3c0-1.66-1.34-3-3-3s-3 1.34-3 3a3 3 0 0 0 3 3z" />
              <path d="M2 12a3 3 0 0 0 3 3c1.66 0 3-1.34 3-3s-1.34-3-3-3a3 3 0 0 0-3 3z" />
              <path d="M22 12a3 3 0 0 0-3-3c-1.66 0-3 1.34-3 3s1.34 3 3 3a3 3 0 0 0 3-3z" />
            </svg>
            Stickers
          </a>
        </nav>

        {activeNavTab === 'stickers' ? (
          <div className="shell-stickers-view">
            <StickerGardenJourney onBackToMap={() => handleNavTabChange('map')} />
          </div>
        ) : (
          <>
            {/* Center: Living Map Card */}
            <section className="paper mapcard" aria-label="Living map">
          {feedbackAlert && (
            <div
              className={`feedback-alert-banner feedback-alert--${feedbackAlert.type}`}
              role={feedbackAlert.type === 'error' ? 'alert' : 'status'}
            >
              <span>{feedbackAlert.message}</span>
              <button
                type="button"
                className="feedback-alert-close"
                onClick={() => setFeedbackAlert(null)}
                aria-label="Dismiss alert"
              >
                &times;
              </button>
            </div>
          )}

          {uploadAlert && (
            <div className="upload-alert-banner" role="alert">
              <span className="upload-alert-text">⚠️ {uploadAlert}</span>
              <button
                type="button"
                className="btn-close-alert"
                onClick={() => setUploadAlert(null)}
                aria-label="Dismiss alert"
              >
                &times;
              </button>
            </div>
          )}

          {/* Five Ways of Tracing Filter Chips */}
          <div className="chips" id="chips">
            <span className="chips-lenses-label" title="Five ways of noticing the physical world">
              Ways to trace:
            </span>

            <button
              type="button"
              className="chip"
              data-f="all"
              aria-pressed={activeFilter === 'All' ? 'true' : 'false'}
              onClick={() => handleFilterChange('All')}
              title="Show all recorded discoveries"
            >
              All <b id="nAll">{allTraces.length}</b>
            </button>

            <button
              type="button"
              className="chip"
              data-f="nature"
              style={{ '--c': 'var(--nature)' } as React.CSSProperties}
              aria-pressed={activeFilter === 'Nature' ? 'true' : 'false'}
              onClick={() => handleFilterChange('Nature')}
              title="🌿 Nature — Living, growing, or naturally occurring"
            >
              <i></i>🌿 Nature {categoryCounts['Nature'] || 0}
            </button>

            <button
              type="button"
              className="chip"
              data-f="sound"
              style={{ '--c': 'var(--sound)' } as React.CSSProperties}
              aria-pressed={activeFilter === 'Sound' ? 'true' : 'false'}
              onClick={() => handleFilterChange('Sound')}
              title="🔊 Sound — Discovered primarily through hearing"
            >
              <i></i>🔊 Sound {categoryCounts['Sound'] || 0}
            </button>

            <button
              type="button"
              className="chip"
              data-f="structure"
              style={{ '--c': 'var(--structure)' } as React.CSSProperties}
              aria-pressed={activeFilter === 'Structure' ? 'true' : 'false'}
              onClick={() => handleFilterChange('Structure')}
              title="🧱 Structure — Human-made objects, architecture, or patterns"
            >
              <i></i>🧱 Structure {categoryCounts['Structure'] || 0}
            </button>

            <button
              type="button"
              className="chip"
              data-f="mystery"
              style={{ '--c': 'var(--mystery)' } as React.CSSProperties}
              aria-pressed={activeFilter === 'Mystery' ? 'true' : 'false'}
              onClick={() => handleFilterChange('Mystery')}
              title="🔎 Mystery — Strange, unexplained, or worth investigating"
            >
              <i></i>🔎 Mystery {categoryCounts['Mystery'] || 0}
            </button>

            <button
              type="button"
              className="chip"
              data-f="personal"
              style={{ '--c': 'var(--personal)' } as React.CSSProperties}
              aria-pressed={activeFilter === 'Personal' ? 'true' : 'false'}
              onClick={() => handleFilterChange('Personal')}
              title="💙 Personal — Meaningful specifically to you"
            >
              <i></i>💙 Personal {categoryCounts['Personal'] || 0}
            </button>

            <span className="count" id="count">
              🌱 {visibleTraces.length} trace{visibleTraces.length === 1 ? '' : 's'}
            </span>
          </div>

          {/* Real Leaflet Map Mount inside .map */}
          <div className="map-mount-wrapper">
            <div className="map" id="map">
              {isLoading ? (
                <div
                  style={{
                    display: 'grid',
                    placeItems: 'center',
                    height: '560px',
                    color: 'var(--ink-soft)',
                    fontSize: '1.2rem',
                  }}
                >
                  Unfolding field map...
                </div>
              ) : (
                <TraceMap
                  traces={visibleTraces}
                  selectedTraceId={selectedTraceId}
                  onSelectTrace={handleSelectTrace}
                  recenterTrigger={recenterTrigger}
                  onRecenter={handleRecenter}
                  placement={placement}
                  onPlacementPositionChange={(pos) =>
                    setPlacement((prev) => (prev ? { ...prev, position: pos } : null))
                  }
                  onConfirmPlacement={handleConfirmPlacement}
                  onCancelPlacement={handleCancelPlacement}
                  isPlacingInProgress={isPlacingInProgress}
                  onDeleteTrace={handleRequestDelete}
                />
              )}
            </div>
          </div>
        </section>

        {/* Right: Field Notes Observation Cards */}
        <aside className="paper notes" aria-label="Field notes">
          <div className="notes-header">
            <h2>Field Notes</h2>
            <p className="notes-subtitle">Recorded observations from slow walks</p>
          </div>

          <div id="notes" className="notes-list">
            {visibleTraces.map((trace) => {
              const isSelected = trace.id === selectedTraceId;
              const catColor = `var(--${trace.category.toLowerCase()})`;
              const icon = CATEGORY_ICONS[trace.category] || '•';
              const meaning = CATEGORY_MEANINGS[trace.category] || 'Observation';
              const thumbnail = TRACE_ILLUSTRATIONS[trace.category] || null;

              return (
                <article
                  key={trace.id}
                  className={`note ${isSelected ? 'on' : ''}`}
                  onClick={() => handleSelectTrace(trace)}
                  tabIndex={0}
                  role="button"
                  aria-pressed={isSelected}
                >
                  {/* Category Header Badge */}
                  <div className="note-card-badge" style={{ color: catColor }}>
                    <span className="note-badge-icon">{icon}</span>
                    <span className="note-badge-category">{trace.category.toUpperCase()}</span>
                    <span className="note-badge-meaning">{meaning}</span>
                  </div>

                  {/* Main Row: Themed SVG Thumbnail + Title & Location */}
                  <div className="note-card-main">
                    <div className="note-thumb-wrapper" title={`${trace.category} field illustration`}>
                      {thumbnail}
                    </div>

                    <div className="note-card-content">
                      <h3 className="note-title">{trace.title}</h3>
                      {trace.latitude != null && trace.longitude != null ? (
                        <small className="note-meta-location">
                          📍 {trace.latitude.toFixed(4)}° N, {Math.abs(trace.longitude).toFixed(4)}° W
                          {trace.locationMode === 'gps' || trace.location_mode === 'gps' ? (
                            <span className="note-loc-tag"> &bull; Located by GPS</span>
                          ) : trace.locationMode === 'manual' || trace.location_mode === 'manual' ? (
                            <span className="note-loc-tag"> &bull; Placed by you</span>
                          ) : null}
                        </small>
                      ) : (
                        <small className="note-meta-location note-meta-unplaced">
                          📍 Unplaced discovery
                        </small>
                      )}
                      <small className="note-meta-date">{formatTimestamp(trace.createdAt)}</small>
                    </div>
                  </div>

                  {/* Observation Text: "Something noticed here" */}
                  {trace.observation && (
                    <div className="note-observation">
                      &ldquo;{trace.observation}&rdquo;
                    </div>
                  )}

                  {/* Tags */}
                  {trace.tags && trace.tags.length > 0 && (
                    <div className="tags">
                      {trace.tags.map((tag) => (
                        <span key={tag}>#{tag}</span>
                      ))}
                    </div>
                  )}

                  {/* Delete trace action */}
                  <div className="note-card-actions">
                    <button
                      type="button"
                      className="note-delete-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRequestDelete(trace);
                      }}
                      title="Delete trace"
                      aria-label={`Delete trace ${trace.title}`}
                    >
                      <svg
                        viewBox="0 0 24 24"
                        width="12"
                        height="12"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                      >
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                      <span>Delete trace</span>
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </aside>
          </>
        )}
      </main>

      {/* Slogan */}
      <p className="slogan">
        <span>Small things. Big stories.</span>
      </p>

      {/* Five ways to leave a trace */}
      <section className="row" id="how">
        <h2>Five ways to leave a trace</h2>
        <p>Notice the world through different lenses. Every small discovery can become a trace.</p>
        <div className="traceWaysGrid">
          {FIVE_TRACE_WAYS.map((way) => (
            <div
              key={way.key}
              className="traceWayCard"
              role="button"
              tabIndex={0}
              onClick={() => {
                setActiveFilter(way.title as TraceCategory);
                document.getElementById('ai-interpreter')?.scrollIntoView({ behavior: 'smooth' });
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setActiveFilter(way.title as TraceCategory);
                  document.getElementById('ai-interpreter')?.scrollIntoView({ behavior: 'smooth' });
                }
              }}
              style={{ cursor: 'pointer' }}
              title={`Focus on ${way.title} and create a trace`}
            >
              <div
                className="traceWayIcon"
                style={{ borderColor: way.color, color: way.color }}
              >
                <span className="traceWayEmoji" role="img" aria-label={way.title}>
                  {way.icon}
                </span>
              </div>
              <h3 className="traceWayTitle">{way.title}</h3>
              <p className="traceWayDesc">{way.description}</p>
              <div className="traceWayExamples">
                <span className="traceWayExamplesHeading">Examples include:</span>
                <div className="traceWayTags">
                  {way.examples.map((ex) => (
                    <span key={ex}>{ex}</span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="row" id="join">
        <h2>Your street has stories</h2>
        <p>Notice something small outside and let local Gemma 3 4B interpret it into a trace.</p>
        <TraceAIInterpreter
          key={interpreterKey}
          initialCategory={activeFilter !== 'All' ? activeFilter : null}
          onTraceReady={handleStartPlacement}
        />
      </section>

      {/* Whimsical Trace Placement Method Prompt */}
      {showPlacementModal && (
        <div className="field-placement-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="placement-modal-title">
          <div className="field-placement-modal">
            <button
              type="button"
              className="field-placement-modal-close"
              onClick={handleSaveUnplaced}
              aria-label="Close and keep unplaced"
            >
              &times;
            </button>
            <h2 id="placement-modal-title" className="field-placement-modal-title">Where did you find this trace?</h2>
            <p className="field-placement-modal-desc">
              Choose how you want to position this discovery on your living map.
            </p>

            {pendingTrace && (
              <div className="field-placement-trace-target">
                <span className="field-placement-target-label">Attaching to trace: </span>
                <strong>{pendingTrace.title || 'Field Observation'}</strong>
                {(pendingTrace.photoFile || pendingTrace.audioFile) && (
                  <div className="field-placement-attachments-preview">
                    {pendingTrace.photoFile && (
                      <span className="placement-attachment-badge">
                        📷 Photo: {pendingTrace.photoFile.name}
                      </span>
                    )}
                    {pendingTrace.audioFile && (
                      <span className="placement-attachment-badge">
                        🎙️ Audio: {pendingTrace.audioFile.name}
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="field-placement-modal-options">
              <button
                type="button"
                className="field-placement-option-btn"
                onClick={handleSelectGps}
              >
                <span className="field-placement-option-icon">📍</span>
                <div>
                  <strong className="field-placement-option-heading">Use my location</strong>
                  <span className="field-placement-option-sub">Detect current coordinates and adjust on map</span>
                </div>
              </button>

              <button
                type="button"
                className="field-placement-option-btn"
                onClick={handleSelectManual}
              >
                <span className="field-placement-option-icon">🗺</span>
                <div>
                  <strong className="field-placement-option-heading">Place it yourself</strong>
                  <span className="field-placement-option-sub">Choose where this discovery belongs on the map</span>
                </div>
              </button>
            </div>

            <div>
              <button
                type="button"
                className="field-placement-modal-skip"
                onClick={handleSaveUnplaced}
              >
                Save without placing right now
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Trace Confirmation Dialog */}
      {traceToDelete && (
        <div
          className="field-placement-modal-backdrop"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
        >
          <div className="field-placement-modal field-delete-modal">
            <button
              type="button"
              className="field-placement-modal-close"
              onClick={handleCancelDelete}
              disabled={isDeleteInProgress}
              aria-label="Keep trace"
            >
              &times;
            </button>
            <div className="field-delete-icon-badge" aria-hidden="true">
              🗑️
            </div>
            <h2 id="delete-dialog-title" className="field-placement-modal-title">
              Delete this trace?
            </h2>
            <p className="field-placement-modal-desc">
              This will permanently remove this discovery and its attached photos and audio.
            </p>

            <div className="field-delete-target-preview">
              <span className="field-delete-preview-title">{traceToDelete.title}</span>
              <span className="field-delete-preview-category">{traceToDelete.category} Discovery</span>
            </div>

            <div className="field-delete-modal-actions">
              <button
                type="button"
                className="cta field-delete-confirm-btn"
                onClick={handleConfirmDelete}
                disabled={isDeleteInProgress}
                aria-busy={isDeleteInProgress}
              >
                {isDeleteInProgress ? 'Deleting...' : 'Delete permanently'}
              </button>
              <button
                type="button"
                className="btn-secondary field-delete-cancel-btn"
                onClick={handleCancelDelete}
                disabled={isDeleteInProgress}
              >
                Keep trace
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Daily Reward Celebration Modal */}
      {celebrationReward && (
        <DailyRewardModal
          isOpen={!!celebrationReward}
          awardedSticker={celebrationReward.awardedSticker}
          streak={celebrationReward.streak}
          longestStreak={celebrationReward.longestStreak}
          milestonesUnlocked={celebrationReward.milestonesUnlocked}
          isPoolExhausted={celebrationReward.isPoolExhausted}
          onClose={() => setCelebrationReward(null)}
          onSeeCollection={() => {
            setCelebrationReward(null);
            handleNavTabChange('stickers');
            setTimeout(() => {
              const el = document.getElementById('my-collection');
              if (el) {
                el.scrollIntoView({ behavior: 'smooth' });
                el.focus?.();
              }
            }, 80);
          }}
        />
      )}

      {/* Critters in the margins that slide in on scroll */}
      <div className="critter l" style={{ top: '560px', '--w': '110px' } as React.CSSProperties}>
        <svg className="bob">
          <use href="#bird" width="100%" height="100%" />
        </svg>
      </div>

      <div className="critter r" style={{ top: '900px', '--w': '90px' } as React.CSSProperties}>
        <svg viewBox="0 0 100 60">
          <use href="#hedge" />
        </svg>
      </div>

      <div className="critter l" style={{ top: '1180px', '--w': '120px' } as React.CSSProperties}>
        <svg viewBox="0 0 120 80">
          <use href="#fox" />
        </svg>
      </div>

      <div className="critter r" style={{ top: '1500px', '--w': '100px' } as React.CSSProperties}>
        <svg viewBox="0 0 80 70" className="bob">
          <use href="#bird" />
        </svg>
      </div>

      <div className="critter l" style={{ top: '1700px', '--w': '110px' } as React.CSSProperties}>
        <svg viewBox="0 0 120 130">
          <use href="#deer" />
        </svg>
      </div>

      {/* Floating drifting bee */}
      <div className="bee" id="bee">
        <svg viewBox="0 0 50 40">
          <use href="#beesym" />
        </svg>
      </div>
    </>
  );
};
