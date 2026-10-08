import React from 'react';
import { HealthResponse } from '../types';
import { formatTimestamp } from '../utils/formatters';

interface StatusPanelProps {
  isConnected: boolean;
  isLoading: boolean;
  data: HealthResponse | null;
  error: string | null;
  lastChecked: Date | null;
  onRefresh: () => void;
}

export const StatusPanel: React.FC<StatusPanelProps> = ({
  isConnected,
  isLoading,
  data,
  error,
  lastChecked,
  onRefresh,
}) => {
  return (
    <div className="content-card">
      <div className="card-title-row">
        <h2 className="card-title">Backend Service</h2>
        <span className={`card-badge ${isConnected ? 'active' : ''}`}>
          {isLoading ? 'CHECKING' : isConnected ? 'HEALTHY' : 'UNREACHABLE'}
        </span>
      </div>

      <div className="detail-list">
        <div className="detail-row">
          <span className="detail-label">Service</span>
          <span className="detail-value">{data?.project ?? 'TRACE Backend'}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Version</span>
          <span className="detail-value">{data?.version ?? '—'}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Environment</span>
          <span className="detail-value">{data?.environment ?? '—'}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Server Timestamp</span>
          <span className="detail-value">{formatTimestamp(data?.timestamp)}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Last Client Probe</span>
          <span className="detail-value">{lastChecked ? lastChecked.toLocaleTimeString() : '—'}</span>
        </div>
      </div>

      {error && (
        <div className="detail-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      <button
        type="button"
        className="btn-secondary"
        onClick={onRefresh}
        disabled={isLoading}
      >
        <span>{isLoading ? 'Checking...' : 'Check Connection'}</span>
      </button>
    </div>
  );
};
