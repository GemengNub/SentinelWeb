import React from 'react';
import { Link } from 'react-router-dom';
import { useSettings } from '../context/SettingsContext';

interface HeaderProps {
  isConnected: boolean;
  onMenuToggle: () => void;
  mobileMenuOpen: boolean;
}

const Header: React.FC<HeaderProps> = ({ isConnected, onMenuToggle, mobileMenuOpen }) => {
  const { settings } = useSettings();



  const headerBg = settings.darkMode ? 'bg-slate-900/80 border-white/5' : 'bg-white/80 border-slate-200';
  const textPrimary = settings.darkMode ? 'text-white' : 'text-slate-900';
  const textSecondary = settings.darkMode ? 'text-slate-300' : 'text-slate-600';
  const textMuted = settings.darkMode ? 'text-slate-500' : 'text-slate-400';
  const textAccent = settings.darkMode ? 'text-cyan-400/70' : 'text-cyan-600/70';
  const hoverBg = settings.darkMode ? 'hover:bg-white/10' : 'hover:bg-slate-100';
  const iconHover = settings.darkMode ? 'group-hover:text-cyan-400' : 'group-hover:text-cyan-600';
  const iconColor = settings.darkMode ? 'text-slate-400' : 'text-slate-500';
  const statusBg = settings.darkMode ? 'bg-slate-800/50 border-white/5' : 'bg-slate-100 border-slate-200';

  return (
    <header className={`${headerBg} backdrop-blur-xl border-b sticky top-0 z-50 transition-colors duration-300`}>
      <div className="px-4 py-4 md:px-6">
        <div className="flex items-center justify-between">
          {/* Left side - Menu button and Logo */}
          <div className="flex items-center gap-4">
            {/* Mobile menu button */}
            <button
              onClick={onMenuToggle}
              className="lg:hidden p-2 rounded-xl hover:bg-white/10 transition-all duration-300"
              aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            >
              <svg
                className="w-6 h-6 text-slate-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                {mobileMenuOpen ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                )}
              </svg>
            </button>

            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 group">
              <div className="relative">
                <div className="w-11 h-11 bg-gradient-to-br from-cyan-400 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/30 transition-all duration-300 group-hover:shadow-cyan-500/50 group-hover:scale-105">
                  {/* Radar/sentinel icon */}
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                    />
                  </svg>
                </div>
                {/* Pulse indicator */}
                <div className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-cyan-400 rounded-full border-2 border-slate-900">
                  <div className="absolute inset-0 w-3.5 h-3.5 bg-cyan-400 rounded-full animate-ping opacity-50" />
                </div>
              </div>
              <div className="hidden sm:block">
                <h1 className="text-xl font-bold text-white tracking-tight">Sentinel</h1>
                <p className="text-xs text-cyan-400/70">Real-time Intelligence</p>
              </div>
            </Link>
          </div>

          {/* Right side - Status */}
          <div className="flex items-center gap-4">
            {/* Time display - hidden on mobile */}
            <div className="hidden md:block text-right">
              <p className="text-sm font-medium text-slate-300">
                {new Date().toLocaleDateString('en-US', {
                  weekday: 'short',
                  month: 'short',
                  day: 'numeric'
                })}
              </p>
              <p className="text-xs text-cyan-400/70">
                {new Date().toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
