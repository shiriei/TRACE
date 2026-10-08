import React from 'react';
import { Trace } from '../../../types/trace';
import { CATEGORY_STYLES } from '../utils/markerIcons';
import { formatTimestamp } from '../../../utils/formatters';

interface TraceMemoryLogProps {
  traces: Trace[];
  selectedTraceId: string | null;
  onSelectTrace: (trace: Trace) => void;
}

export const TraceMemoryLog: React.FC<TraceMemoryLogProps> = ({
  traces,
  selectedTraceId,
  onSelectTrace,
}) => {
  return (
    <section className="memory-log-section" aria-labelledby="memory-log-heading">
      <div className="memory-log-header">
        <div className="memory-log-heading-group">
          <span className="memory-log-kicker">Field Notebook Archive</span>
          <h3 id="memory-log-heading" className="memory-log-title">
            Personal Trace Memory ({traces.length})
          </h3>
          <p className="memory-log-subtitle">
            &ldquo;I can return here months later and revisit what I actually experienced.&rdquo;
          </p>
        </div>
      </div>

      <div className="memory-log-grid">
        {traces.map((trace) => {
          const isSelected = trace.id === selectedTraceId;
          const style = CATEGORY_STYLES[trace.category] || CATEGORY_STYLES.Personal;
          const mediaCount = trace.media?.length || 0;

          return (
            <article
              key={trace.id}
              className={`memory-card ${isSelected ? 'memory-card--selected' : ''}`}
              onClick={() => onSelectTrace(trace)}
            >
              <div className="memory-card-top">
                <span
                  className="memory-category-tag"
                  style={{ color: style.primaryColor, backgroundColor: style.bgTint, borderColor: style.borderColor }}
                >
                  <span className="memory-category-dot" style={{ backgroundColor: style.primaryColor }} />
                  {trace.category}
                </span>
                <time className="memory-card-time" dateTime={trace.createdAt}>
                  {formatTimestamp(trace.createdAt)}
                </time>
              </div>

              <h4 className="memory-card-title">{trace.title}</h4>

              {trace.observation && (
                <div className="memory-card-noticed">
                  <span className="memory-prompt-label">What I noticed:</span>
                  <p className="memory-noticed-text">&ldquo;{trace.observation}&rdquo;</p>
                </div>
              )}

              {trace.userNotes && (
                <div className="memory-card-notes">
                  <span className="memory-prompt-label">My notes:</span>
                  <p className="memory-notes-text">{trace.userNotes}</p>
                </div>
              )}

              <div className="memory-card-media-status">
                <span className="media-status-pill">
                  {mediaCount === 0 ? 'No captures attached yet' : `${mediaCount} capture(s)`}
                </span>
              </div>

              <div className="memory-card-footer">
                <span className="memory-coords">
                  {trace.latitude.toFixed(4)}° N, {Math.abs(trace.longitude).toFixed(4)}° W
                </span>

                {trace.tags && trace.tags.length > 0 && (
                  <div className="memory-tags-list">
                    {trace.tags.slice(0, 3).map((tag) => (
                      <span key={tag} className="memory-tag">
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
};
