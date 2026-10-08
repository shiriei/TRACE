import React from 'react';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { Dashboard } from './pages/Dashboard';
import { useHealthStatus } from './hooks/useHealthStatus';

export const App: React.FC = () => {
  const { isConnected, isLoading } = useHealthStatus();

  return (
    <div className="app-shell">
      <Header isConnected={isConnected} isLoading={isLoading} />
      <main>
        <Dashboard />
      </main>
      <Footer />
    </div>
  );
};

export default App;
