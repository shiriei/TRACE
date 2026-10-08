import React from 'react';
import { useHealthStatus } from '../hooks/useHealthStatus';
import { StatusPanel } from '../components/StatusPanel';
import { FoundationOverview } from '../components/FoundationOverview';
import { ModulePlaceholders } from '../components/ModulePlaceholders';

export const Dashboard: React.FC = () => {
  const { isConnected, isLoading, data, error, lastChecked, refetch } = useHealthStatus();

  return (
    <div className="main-content">
      <section className="hero-section">
        <div className="hero-tagline">Physical Exploration System</div>
        <h1 className="hero-headline">Go outside. Notice more. Leave a trace.</h1>
        <p className="hero-description">
          TRACE is a local-first exploration system that turns the things you discover outside
          into a living personal map, and uses those discoveries to influence what you should discover next.
        </p>
        <div className="concept-callout">
          &ldquo;The world is the interface. The screen should start and end the experience, not become the experience.&rdquo;
        </div>
      </section>

      <div className="dashboard-columns">
        <StatusPanel
          isConnected={isConnected}
          isLoading={isLoading}
          data={data}
          error={error}
          lastChecked={lastChecked}
          onRefresh={refetch}
        />
        <FoundationOverview />
      </div>

      <ModulePlaceholders />
    </div>
  );
};
