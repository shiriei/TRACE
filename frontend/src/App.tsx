import React, { useState } from 'react';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { Dashboard } from './pages/Dashboard';
import { TraceMapWorkspace } from './features/map';
import { useHealthStatus } from './hooks/useHealthStatus';

export const App: React.FC = () => {
  const { isConnected, isLoading } = useHealthStatus();
  const [activeView, setActiveView] = useState<'map' | 'overview'>('map');

  return (
    <div className="page" id="page">
      <Header
        isConnected={isConnected}
        isLoading={isLoading}
        activeView={activeView}
        onViewChange={setActiveView}
      />
      {activeView === 'map' ? (
        <TraceMapWorkspace />
      ) : (
        <Dashboard onNavigateToMap={() => setActiveView('map')} />
      )}
      <Footer />
    </div>
  );
};

export default App;
