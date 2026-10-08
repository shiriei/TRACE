import React from 'react';
import { TraceCategoryFilter, TRACE_CATEGORIES, TraceCategory } from '../../../types/trace';

interface MapFilterBarProps {
  activeFilter: TraceCategoryFilter;
  onFilterChange: (filter: TraceCategoryFilter) => void;
  categoryCounts: Record<string, number>;
  totalCount: number;
}

const CATEGORY_ICONS: Record<TraceCategory, string> = {
  Nature: '🌱',
  Sound: '〰️',
  Structure: '🏛️',
  Mystery: '❓',
  Personal: '👤',
};

export const MapFilterBar: React.FC<MapFilterBarProps> = ({
  activeFilter,
  onFilterChange,
  categoryCounts,
  totalCount,
}) => {
  return (
    <nav className="reference-filter-bar" aria-label="Category filter">
      <div className="reference-filter-chips">
        <button
          type="button"
          className={`filter-chip ${activeFilter === 'All' ? 'filter-chip--active' : ''}`}
          onClick={() => onFilterChange('All')}
          aria-pressed={activeFilter === 'All'}
        >
          <span className="chip-icon">🍃</span>
          <span className="chip-label">All</span>
          <span className="chip-count">{totalCount}</span>
        </button>

        {TRACE_CATEGORIES.map((category) => {
          const isActive = activeFilter === category;
          const count = categoryCounts[category] || 0;
          const icon = CATEGORY_ICONS[category];

          return (
            <button
              key={category}
              type="button"
              className={`filter-chip ${isActive ? 'filter-chip--active' : ''}`}
              onClick={() => onFilterChange(category)}
              aria-pressed={isActive}
            >
              <span className="chip-icon">{icon}</span>
              <span className="chip-label">{category}</span>
              <span className="chip-count">{count}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
