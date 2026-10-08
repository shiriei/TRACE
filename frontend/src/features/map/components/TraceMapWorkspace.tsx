import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Trace, TraceCategory, TraceCategoryFilter, SensoryType, TraceAIResult } from '../../../types';
import { traceService } from '../../../services/traceService';
import { TraceMap, PlacementState } from './TraceMap';
import { formatTimestamp } from '../../../utils/formatters';
import { TRACE_ILLUSTRATIONS, CATEGORY_MEANINGS } from './TraceThumbnails';
import { TraceAIInterpreter } from '../../ai';

interface PendingTrace {
  observation: string;
  category?: TraceCategory;
  title?: string;
  summary?: string;
  tags?: string[];
  sensory_type?: SensoryType;
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

export const TraceMapWorkspace: React.FC = () => {
  const [allTraces, setAllTraces] = useState<Trace[]>([]);
  const [activeFilter, setActiveFilter] = useState<TraceCategoryFilter>('All');
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [categoryCounts, setCategoryCounts] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [recenterTrigger, setRecenterTrigger] = useState<number>(0);
  const [activeNavTab, setActiveNavTab] = useState<'map' | 'traces' | 'log' | 'settings'>('map');

  // Trace placement state
  const [pendingTrace, setPendingTrace] = useState<PendingTrace | null>(null);
  const [showPlacementModal, setShowPlacementModal] = useState<boolean>(false);
  const [placement, setPlacement] = useState<PlacementState | null>(null);

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
          setSelectedTraceId(traces[0].id);
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

  // Trigger placement flow when user provides observation
  const handleStartPlacement = useCallback((data: { observation: string; result?: TraceAIResult | null }) => {
    setPendingTrace({
      observation: data.observation,
      category: data.result?.category || 'Personal',
      title: data.result?.title || data.observation.slice(0, 50),
      summary: data.result?.summary || data.observation,
      tags: data.result?.tags || [],
      sensory_type: data.result?.sensory_type || 'visual',
    });
    setShowPlacementModal(true);
  }, []);

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
    setShowPlacementModal(false);
    setPlacement(null);
    if (!pendingTrace) return;

    const trace = await traceService.addTrace({
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
    });

    setAllTraces((prev) => [trace, ...prev.filter((t) => t.id !== trace.id)]);
    setSelectedTraceId(trace.id);
    const counts = await traceService.getCategoryCounts();
    setCategoryCounts(counts);
    setPendingTrace(null);
  }, [pendingTrace]);

  // Confirm placement from Map banner
  const handleConfirmPlacement = useCallback(async () => {
    if (!placement || !pendingTrace) return;

    const trace = await traceService.addTrace({
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
    });

    setAllTraces((prev) => [trace, ...prev.filter((t) => t.id !== trace.id)]);
    setSelectedTraceId(trace.id);
    const counts = await traceService.getCategoryCounts();
    setCategoryCounts(counts);

    setPlacement(null);
    setPendingTrace(null);
  }, [placement, pendingTrace]);

  const handleCancelPlacement = useCallback(() => {
    handleSaveUnplaced();
  }, [handleSaveUnplaced]);

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
            onClick={(e) => {
              e.preventDefault();
              setActiveNavTab('traces');
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
              setActiveNavTab('map');
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
            onClick={(e) => {
              e.preventDefault();
              setActiveNavTab('log');
              document.getElementById('how')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            <svg viewBox="0 0 24 24">
              <path d="M4 5h7a1 1 0 011 1v13a3 3 0 00-3-2H4zM20 5h-7a1 1 0 00-1 1v13a3 3 0 013-2h5z" />
            </svg>
            Log
          </a>

          <a
            href="#join"
            onClick={(e) => {
              e.preventDefault();
              setActiveNavTab('settings');
              document.getElementById('join')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            <svg viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
            </svg>
            Settings
          </a>
        </nav>

        {/* Center: Living Map Card */}
        <section className="paper mapcard" aria-label="Living map">
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
                </article>
              );
            })}
          </div>
        </aside>
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
            <div key={way.key} className="traceWayCard">
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
        <TraceAIInterpreter onTraceReady={handleStartPlacement} />
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
