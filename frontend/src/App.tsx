import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useWebSocket } from './hooks/useWebSocket';
import { useSettings } from './context/SettingsContext';
import { useAppStore } from './store';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import NotificationBanner from './components/NotificationBanner';
import AlertDetailModal from './components/AlertDetailModal';
import Dashboard from './pages/Dashboard';
import AlertsPage from './pages/AlertsPage';
import MapPage from './pages/MapPage';
import StatsPage from './pages/StatsPage';

function App() {
  const { isConnected, lastAlert } = useWebSocket();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { settings } = useSettings();
  const { selectedAlert, setSelectedAlert } = useAppStore();

  // Apply light/dark mode class to body
  useEffect(() => {
    if (settings.darkMode) {
      document.body.classList.remove('light-mode');
    } else {
      document.body.classList.add('light-mode');
    }
  }, [settings.darkMode]);

  return (
    <div className={`min-h-screen flex flex-col relative ${settings.darkMode ? 'bg-slate-950' : 'bg-slate-50'}`}>
      {/* Grid Background */}
      <div className={`fixed inset-0 grid-background pointer-events-none z-0 ${settings.darkMode ? '' : 'light-mode-bg'}`} />
      
      {/* Radial gradient overlay */}
      <div className={`fixed inset-0 bg-gradient-radial pointer-events-none z-0 ${settings.darkMode ? 'from-cyan-500/5' : 'from-cyan-500/10'} via-transparent to-transparent`} />
      
      <Header 
        isConnected={isConnected} 
        onMenuToggle={() => setMobileMenuOpen(!mobileMenuOpen)}
        mobileMenuOpen={mobileMenuOpen}
      />
      
      <NotificationBanner alert={lastAlert} />
      
      <div className="flex-1 flex relative z-10">
        {/* Mobile Overlay */}
        {mobileMenuOpen && (
          <div 
            className={`fixed inset-0 backdrop-blur-sm z-20 lg:hidden ${settings.darkMode ? 'bg-black/60' : 'bg-black/30'}`}
            onClick={() => setMobileMenuOpen(false)}
          />
        )}
        
        {/* Sidebar - Fixed on mobile, Sticky on desktop */}
        <div className={`
          fixed lg:sticky top-0 lg:top-[73px] inset-y-0 left-0 z-30 
          transform transition-all duration-300 ease-in-out 
          lg:translate-x-0 lg:shrink-0 lg:h-[calc(100vh-73px)]
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
          ${sidebarCollapsed ? 'w-20' : 'w-72'}
        `}>
          <Sidebar 
            onClose={() => setMobileMenuOpen(false)} 
            collapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
        </div>
        
        {/* Main Content */}
        <main className={`flex-1 p-4 md:p-6 lg:p-8 overflow-auto min-h-[calc(100vh-180px)] ${settings.darkMode ? 'text-slate-100' : 'text-slate-900'}`}>
          <div className="max-w-7xl mx-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="/map" element={<MapPage />} />
              <Route path="/stats" element={<StatsPage />} />
            </Routes>
          </div>
        </main>
      </div>
      
      {/* Footer */}
      <footer className={`backdrop-blur-xl border-t px-4 py-4 md:px-6 relative z-10 ${settings.darkMode ? 'bg-slate-900/80 border-white/5 text-slate-500' : 'bg-white/80 border-slate-200 text-slate-500'}`}>
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between text-sm">
          <p>Sentinel v1.0.0 - Real-time Crisis Intelligence Platform</p>
          <p className="mt-2 md:mt-0">© 2026 Disaster Intelligence</p>
        </div>
      </footer>

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <AlertDetailModal
          alert={selectedAlert}
          onClose={() => setSelectedAlert(null)}
        />
      )}
    </div>
  );
}

export default App;
