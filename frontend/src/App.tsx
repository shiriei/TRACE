import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { Dashboard } from './pages/Dashboard';
import { TraceMapWorkspace } from './features/map';
import { initCrossTabSync } from './services/crossTabSync';

export const App: React.FC = () => {
  const [activeView, setActiveView] = useState<'map' | 'overview'>('map');
  const [workspaceTab, setWorkspaceTab] = useState<'map' | 'traces' | 'log' | 'stickers'>('map');

  // Synchronize streak and sticker collection across open tabs
  useEffect(() => {
    return initCrossTabSync();
  }, []);

  const handleOpenStickers = () => {
    setActiveView('map');
    setWorkspaceTab('stickers');
  };

  return (
    <div className="page" id="page">
      <Header
        activeView={activeView}
        onViewChange={setActiveView}
        onOpenStickers={handleOpenStickers}
      />
      {activeView === 'map' ? (
        <TraceMapWorkspace
          activeTab={workspaceTab}
          onTabChange={setWorkspaceTab}
        />
      ) : (
        <Dashboard
          onNavigateToMap={() => {
            setActiveView('map');
            setWorkspaceTab('map');
          }}
        />
      )}
      <Footer />
    </div>
  );
};

export default App;
