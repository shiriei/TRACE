import React from 'react';
import { useStreak } from '../hooks/useStreak';
import { StreakIndicator } from './StreakIndicator';

interface HeaderProps {
  activeView: 'map' | 'overview';
  onViewChange: (view: 'map' | 'overview') => void;
  onOpenStickers?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeView,
  onViewChange,
  onOpenStickers,
}) => {
  const { streakSummary, isLoading: isStreakLoading, error: streakError } = useStreak();

  return (
    <header>
      <div
        className="brand"
        onClick={() => onViewChange('map')}
        role="button"
        tabIndex={0}
        style={{ cursor: 'pointer' }}
      >
        <h1>TRACE</h1>
        <p>Go outside. Notice more. Leave a trace.</p>
      </div>
      <div className="switch" role="group" aria-label="View">
        <button
          type="button"
          aria-pressed={activeView === 'map' ? 'true' : 'false'}
          onClick={() => onViewChange('map')}
        >
          Living Map
        </button>
        <button
          type="button"
          aria-pressed={activeView === 'overview' ? 'true' : 'false'}
          onClick={() => onViewChange('overview')}
        >
          System Overview
        </button>
      </div>
      <div className="header-actions">
        <StreakIndicator
          currentStreak={streakSummary ? streakSummary.current_streak : (isStreakLoading ? null : 0)}
          isLoading={isStreakLoading}
          error={streakError}
          todayQualified={streakSummary?.today_qualified ?? false}
          onClick={onOpenStickers}
        />
      </div>
    </header>
  );
};
