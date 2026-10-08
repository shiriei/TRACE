import React from 'react';

export const FoundationOverview: React.FC = () => {
  return (
    <div className="content-card">
      <div className="card-title-row">
        <h2 className="card-title">Architecture Foundation</h2>
        <span className="card-badge">VERIFIED</span>
      </div>

      <div className="bullet-list">
        <div className="bullet-item">
          <span className="bullet-marker">&bull;</span>
          <div className="bullet-text">
            <strong>Decoupled Architecture:</strong>{' '}
            <span>FastAPI backend orchestrates logic while React + Vite provides a responsive interface.</span>
          </div>
        </div>

        <div className="bullet-item">
          <span className="bullet-marker">&bull;</span>
          <div className="bullet-text">
            <strong>Zero Cloud AI Dependency:</strong>{' '}
            <span>Engineered for future local inference via LM Studio & Gemma without external data leakage.</span>
          </div>
        </div>

        <div className="bullet-item">
          <span className="bullet-marker">&bull;</span>
          <div className="bullet-text">
            <strong>Sovereign Privacy:</strong>{' '}
            <span>Exploration trails, notes, and coordinates remain on your local hardware.</span>
          </div>
        </div>

        <div className="bullet-item">
          <span className="bullet-marker">&bull;</span>
          <div className="bullet-text">
            <strong>Clean Boundaries:</strong>{' '}
            <span>No fake AI responses or mock databases in this foundation phase.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
