import React from 'react';
import { Trace } from '../../../types/trace';
import { CATEGORY_STYLES } from '../utils/markerIcons';
import { formatTimestamp } from '../../../utils/formatters';
import { TraceMediaGallery } from './TraceMediaGallery';

interface TraceDetailCardProps {
  trace: Trace;
  onClose?: () => void;
  isCompact?: boolean;
  onDelete?: (trace: Trace) => void;
}

export const TraceDetailCard: React.FC<TraceDetailCardProps> = ({
  trace,
  onClose,
  isCompact = false,
  onDelete,
}) => {
  const categoryStyle = CATEGORY_STYLES[trace.category] || CATEGORY_STYLES.Personal;

  return (
    <article
      className={`field-note-card ${isCompact ? 'field-note-card--compact' : ''}`}
      aria-labelledby={`note-title-${trace.id}`}
    >
      {/* Decorative notebook stamp top bar */}
      <header className="field-note-header">
        <div className="field-note-badge" style={{ color: categoryStyle.primaryColor, borderColor: categoryStyle.borderColor }}>
          <span className="field-note-badge-dot" style={{ backgroundColor: categoryStyle.primaryColor }} />
          <span>{trace.category} Discovery</span>
        </div>
        <div className="field-note-header-right">
          <time className="field-note-date" dateTime={trace.createdAt}>
            {formatTimestamp(trace.createdAt)}
          </time>
          {onClose && (
            <button
              type="button"
              className="field-note-close-btn"
              onClick={onClose}
              aria-label="Close field note"
            >
              &times;
            </button>
          )}
        </div>
      </header>

      {/* Scrollable description & activity detail area */}
      <div
        className="field-note-scrollable-body"
        onWheel={(e) => e.stopPropagation()}
        onTouchMove={(e) => e.stopPropagation()}
      >
        {/* Observation Headline */}
        <div className="field-note-title-group">
          <h3 id={`note-title-${trace.id}`} className="field-note-title">
            {trace.title}
          </h3>
          <p className="field-note-description">{trace.description}</p>
        </div>

        {/* "What I noticed..." field observation */}
        {trace.observation && (
          <section className="field-note-section">
            <h4 className="field-note-section-heading">What I noticed</h4>
            <div className="field-note-observation-box">
              &ldquo;{trace.observation}&rdquo;
            </div>
          </section>
        )}

        {/* "My notes..." personal reflections */}
        {trace.userNotes && (
          <section className="field-note-section">
            <h4 className="field-note-section-heading">My field notes</h4>
            <p className="field-note-user-reflections">{trace.userNotes}</p>
          </section>
        )}

        {/* Media Captures Section (Photo / Audio / Voice / Video) */}
        {trace.media && trace.media.length > 0 && (
          <section className="field-note-section">
            <h4 className="field-note-section-heading">Captures</h4>
            <TraceMediaGallery media={trace.media} />
          </section>
        )}
      </div>

      {/* Location information and field tags footer */}
      <footer className="field-note-footer">
        <div className="field-note-coords">
          <svg className="field-note-coords-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
          </svg>
          {trace.latitude != null && trace.longitude != null ? (
            <span>
              {trace.latitude.toFixed(4)}° N, {Math.abs(trace.longitude).toFixed(4)}° W
              {trace.locationMode === 'gps' || trace.location_mode === 'gps' ? (
                <em className="field-note-loc-tag" style={{ fontStyle: 'normal', marginLeft: '0.4rem', opacity: 0.85 }}>
                  &bull; Located by GPS
                </em>
              ) : trace.locationMode === 'manual' || trace.location_mode === 'manual' ? (
                <em className="field-note-loc-tag" style={{ fontStyle: 'normal', marginLeft: '0.4rem', opacity: 0.85 }}>
                  &bull; Placed by you
                </em>
              ) : null}
            </span>
          ) : (
            <span style={{ fontStyle: 'italic', opacity: 0.85 }}>
              Unplaced discovery
            </span>
          )}
        </div>

        {trace.tags && trace.tags.length > 0 && (
          <ul className="field-note-tags" aria-label="Field tags">
            {trace.tags.map((tag) => (
              <li key={tag} className="field-note-tag">
                #{tag}
              </li>
            ))}
          </ul>
        )}

        {onDelete && (
          <div className="field-note-actions">
            <button
              type="button"
              className="field-note-delete-btn"
              onClick={() => onDelete(trace)}
              title="Delete trace"
            >
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
              <span>Delete trace</span>
            </button>
          </div>
        )}
      </footer>
    </article>
  );
};
