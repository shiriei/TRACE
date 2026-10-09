import React from 'react';

interface StreakIndicatorProps {
  currentStreak: number | null;
  isLoading: boolean;
  error?: string | null;
  todayQualified?: boolean;
  onClick?: () => void;
}

export const StreakIndicator: React.FC<StreakIndicatorProps> = ({
  currentStreak,
  isLoading,
  error,
  todayQualified = false,
  onClick,
}) => {
  // Label and tooltip
  const getTooltip = () => {
    if (isLoading) return 'Loading exploration streak...';
    if (error) return 'Streak unavailable';
    if (currentStreak === 0) {
      return '0-day exploration streak • Record a trace today to start your streak!';
    }
    const dayWord = currentStreak === 1 ? 'day' : 'days';
    if (todayQualified) {
      return `${currentStreak}-${dayWord} exploration streak • Today's trace logged!`;
    }
    return `${currentStreak}-${dayWord} exploration streak • Pending today's trace`;
  };

  const getAriaLabel = () => {
    if (isLoading) return 'Loading exploration streak';
    if (error) return 'Exploration streak unavailable';
    return `${currentStreak ?? 0}-day exploration streak`;
  };

  const isDormant = !currentStreak || currentStreak === 0;

  return (
    <button
      type="button"
      className={`header-streak-pill ${todayQualified ? 'header-streak-pill--qualified' : ''} ${
        isLoading ? 'header-streak-pill--loading' : ''
      }`}
      onClick={onClick}
      title={getTooltip()}
      aria-label={getAriaLabel()}
      disabled={isLoading}
    >
      <div className={`header-streak-badge ${isDormant ? 'header-streak-badge--dormant' : ''}`}>
        <svg
          className={`streak-flame-icon ${
            !isDormant ? 'streak-flame-icon--active' : 'streak-flame-icon--dormant'
          }`}
          viewBox="0 0 24 24"
          fill={!isDormant ? 'url(#headerStreakFlameGrad)' : 'url(#headerStreakFlameDormantGrad)'}
          stroke={!isDormant ? '#e8590c' : '#b09b82'}
          strokeWidth="1.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <defs>
            <linearGradient
              id="headerStreakFlameGrad"
              x1="12"
              y1="2"
              x2="12"
              y2="22"
              gradientUnits="userSpaceOnUse"
            >
              <stop stopColor="#ff922b" />
              <stop offset="1" stopColor="#e8590c" />
            </linearGradient>
            <linearGradient
              id="headerStreakFlameDormantGrad"
              x1="12"
              y1="2"
              x2="12"
              y2="22"
              gradientUnits="userSpaceOnUse"
            >
              <stop stopColor="#e6dac8" />
              <stop offset="1" stopColor="#c7b69f" />
            </linearGradient>
          </defs>
          <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />
        </svg>
      </div>

      <span className="header-streak-count">
        {isLoading ? '...' : (currentStreak ?? 0)}
      </span>
    </button>
  );
};
