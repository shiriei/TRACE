import React from 'react';

interface UnexploredIndicatorProps {
  totalTraces: number;
}

export const UnexploredIndicator: React.FC<UnexploredIndicatorProps> = ({ totalTraces }) => {
  return (
    <div className="storybook-frontier-badge" title="Upcoming Phase 4 exploration frontiers">
      <div className="storybook-compass-glyph" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
          <circle cx="12" cy="12" r="10" stroke="#78716c" strokeDasharray="3 2" />
          <polygon points="12 4 14.5 12 12 20 9.5 12 12 4" fill="#a8a29e" fillOpacity="0.4" stroke="#57534e" />
        </svg>
      </div>
      <div className="frontier-narrative">
        <span className="frontier-narrative-title">Living Perimeter</span>
        <span className="frontier-narrative-desc">
          {totalTraces > 0
            ? `${totalTraces} traces saved &bull; The world beyond awaits`
            : 'No traces yet &bull; Step outside to begin'}
        </span>
      </div>
    </div>
  );
};
