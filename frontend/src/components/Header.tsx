import React from 'react';

interface HeaderProps {
  isConnected: boolean;
  isLoading: boolean;
}

export const Header: React.FC<HeaderProps> = ({ isConnected, isLoading }) => {
  return (
    <header className="site-header">
      <div className="header-container">
        <div className="brand">
          <svg className="brand-icon" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <circle cx="16" cy="16" r="13" stroke="#38bdf8" strokeWidth="1.75" />
            <circle cx="16" cy="16" r="4.5" fill="#38bdf8" />
            <path d="M16 3v3M16 26v3M3 16h3M26 16h3" stroke="#38bdf8" strokeWidth="1.75" strokeLinecap="round" />
          </svg>
          <span className="brand-name">TRACE</span>
          <span className="brand-phase-tag">Phase 0 Foundation</span>
        </div>

        <div className="header-status">
          <span
            className={`status-indicator-dot ${
              isLoading ? 'loading' : isConnected ? 'connected' : 'disconnected'
            }`}
          />
          <span>
            {isLoading ? 'Checking backend...' : isConnected ? 'Backend Connected' : 'Backend Offline'}
          </span>
        </div>
      </div>
    </header>
  );
};
