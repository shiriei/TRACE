import React from 'react';

interface HeaderProps {
  isConnected: boolean;
  isLoading: boolean;
  activeView: 'map' | 'overview';
  onViewChange: (view: 'map' | 'overview') => void;
}

export const Header: React.FC<HeaderProps> = ({
  isConnected,
  isLoading,
  activeView,
  onViewChange,
}) => {
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
      <button
        type="button"
        className="avatar"
        aria-label="Your profile"
        title={isLoading ? 'Checking backend...' : isConnected ? 'Local backend connected' : 'Backend offline'}
      >
        <svg
          width="26"
          height="26"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#2c4a3f"
          strokeWidth="1.8"
          strokeLinecap="round"
        >
          <circle cx="12" cy="8" r="4" />
          <path d="M4 21c1-5 5-7 8-7s7 2 8 7" />
        </svg>
      </button>
    </header>
  );
};
