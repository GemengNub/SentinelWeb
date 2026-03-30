import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import { useTranslation } from 'react-i18next';
import { useSettings, MapStyle } from '../context/SettingsContext';
import { useAppStore } from '../store';
import { changeLanguage, languages } from '../i18n';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  anchorRef: React.RefObject<HTMLDivElement>;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ isOpen, onClose, anchorRef }) => {
  const { settings, updateSettings, playAlertSound } = useSettings();
  const { t, i18n } = useTranslation();
  const [viewName, setViewName] = useState('');
  const { filters, savedViews, addSavedView, removeSavedView, applySavedView } = useAppStore();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (
        anchorRef.current && 
        !anchorRef.current.contains(target) &&
        !(document.getElementById('settings-panel')?.contains(target))
      ) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose, anchorRef]);

  if (!isOpen) return null;

  const Toggle: React.FC<{ enabled: boolean; onChange: (value: boolean) => void }> = ({ enabled, onChange }) => (
    <button
      onClick={() => onChange(!enabled)}
      className={`relative w-11 h-6 rounded-full transition-all duration-300 ${
        enabled ? 'bg-cyan-500 shadow-lg shadow-cyan-500/50' : 'bg-slate-700'
      }`}
    >
      <span
        className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all duration-300 shadow-md ${
          enabled ? 'left-6' : 'left-1'
        }`}
      />
    </button>
  );

  const testSound = () => {
    playAlertSound('CRITICAL');
  };

  const panelContent = (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-[99]" onClick={onClose} />
      
      {/* Panel */}
      <div
        id="settings-panel"
        className="fixed z-[100] w-80 rounded-2xl bg-slate-900/98 backdrop-blur-2xl border border-white/10 shadow-2xl shadow-black/50 animate-slide-down overflow-hidden"
        style={{
          top: anchorRef.current ? anchorRef.current.getBoundingClientRect().bottom + 8 : 80,
          right: anchorRef.current ? window.innerWidth - anchorRef.current.getBoundingClientRect().right : 20,
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-cyan-500/20 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h3 className="font-semibold text-white">Settings</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          >
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Settings List */}
        <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
          {/* Appearance Section */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Appearance</p>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                  <span className="text-sm text-slate-300">Dark Mode</span>
                </div>
                <Toggle 
                  enabled={settings.darkMode} 
                  onChange={(value) => updateSettings({ darkMode: value })} 
                />
              </div>

              <div>
                <div className="flex items-center gap-3 mb-2">
                  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                  </svg>
                  <span className="text-sm text-slate-300">Map Style</span>
                </div>
                <select
                  value={settings.mapStyle}
                  onChange={(e) => updateSettings({ mapStyle: e.target.value as MapStyle })}
                  className="w-full bg-slate-800/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                  <option value="satellite">Satellite</option>
                  <option value="terrain">Terrain</option>
                </select>
              </div>

              <div>
                <div className="flex items-center gap-3 mb-2">
                  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                  </svg>
                  <span className="text-sm text-slate-300">Language</span>
                </div>
                <select
                  value={i18n.language}
                  onChange={(e) => changeLanguage(e.target.value)}
                  className="w-full bg-slate-800/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                >
                  {languages.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Saved Views Section */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Saved Views</p>
            <div className="space-y-3">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={viewName}
                  onChange={(e) => setViewName(e.target.value)}
                  placeholder="View name..."
                  className="flex-1 bg-slate-800/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                />
                <button
                  onClick={() => {
                    if (viewName.trim()) {
                      addSavedView(viewName.trim(), filters);
                      setViewName('');
                    }
                  }}
                  className="px-3 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  Save
                </button>
              </div>
              {savedViews.length > 0 && (
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {savedViews.map((view) => (
                    <div key={view.id} className="flex items-center justify-between bg-slate-800/30 rounded-lg px-3 py-2">
                      <button
                        onClick={() => applySavedView(view.id)}
                        className="text-sm text-slate-300 hover:text-white transition-colors"
                      >
                        {view.name}
                      </button>
                      <button
                        onClick={() => removeSavedView(view.id)}
                        className="text-slate-500 hover:text-red-400 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Notifications Section */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Notifications</p>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  <span className="text-sm text-slate-300">Enable Notifications</span>
                </div>
                <Toggle 
                  enabled={settings.notifications} 
                  onChange={(value) => updateSettings({ notifications: value })} 
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15.536a5 5 0 001.414 1.414m2.828-9.9a9 9 0 0112.728 0" />
                  </svg>
                  <span className="text-sm text-slate-300">Sound Effects</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={testSound}
                    className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                    title="Test sound"
                  >
                    <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </button>
                  <Toggle 
                    enabled={settings.soundEnabled} 
                    onChange={(value) => updateSettings({ soundEnabled: value })} 
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Data Section */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Data</p>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span className="text-sm text-slate-300">Auto Refresh</span>
                </div>
                <Toggle 
                  enabled={settings.autoRefresh} 
                  onChange={(value) => updateSettings({ autoRefresh: value })} 
                />
              </div>

              {settings.autoRefresh && (
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">Refresh Interval</label>
                  <select
                    value={settings.refreshInterval}
                    onChange={(e) => updateSettings({ refreshInterval: Number(e.target.value) })}
                    className="w-full bg-slate-800/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                  >
                    <option value={10}>10 seconds</option>
                    <option value={30}>30 seconds</option>
                    <option value={60}>1 minute</option>
                    <option value={300}>5 minutes</option>
                  </select>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/10">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Sentinel v1.0.0</span>
            <button 
              onClick={() => {
                localStorage.removeItem('sentinel-settings');
                window.location.reload();
              }}
              className="text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              Reset to defaults
            </button>
          </div>
        </div>
      </div>
    </>
  );

  return ReactDOM.createPortal(panelContent, document.body);
};

export default SettingsPanel;
