import React, { useEffect } from 'react';
import ReactDOM from 'react-dom';
import { useAlerts } from '../services/api';
import { formatDistanceToNow } from 'date-fns';

interface NotificationPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const NotificationPanel: React.FC<NotificationPanelProps> = ({ isOpen, onClose }) => {
  const { data } = useAlerts({ pageSize: 10 });

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (
        !document.getElementById('notification-panel')?.contains(target)
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
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const notifications = data?.alerts?.slice(0, 5) || [];

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'border-l-red-500 bg-red-500/5';
      case 'HIGH': return 'border-l-orange-500 bg-orange-500/5';
      case 'MEDIUM': return 'border-l-amber-500 bg-amber-500/5';
      default: return 'border-l-emerald-500 bg-emerald-500/5';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return '🔴';
      case 'HIGH': return '🟠';
      case 'MEDIUM': return '🟡';
      default: return '🟢';
    }
  };

  const panelContent = (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-[99] bg-black/50 backdrop-blur-sm" onClick={onClose} />
      
      {/* Panel */}
      <div
        id="notification-panel"
        className="fixed z-[100] left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md rounded-2xl bg-slate-900/98 backdrop-blur-2xl border border-white/10 shadow-2xl shadow-black/50 overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
            <h3 className="font-semibold text-white">Notifications</h3>
            <span className="badge-cyan text-xs">{notifications.length}</span>
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

        {/* Notifications List */}
        <div className="max-h-80 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="p-8 text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-slate-800/50 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <p className="text-slate-400 text-sm">No new notifications</p>
            </div>
          ) : (
            <div className="p-2">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-3 rounded-xl mb-2 border-l-4 ${getSeverityColor(notification.severity)} hover:bg-white/5 transition-colors cursor-pointer`}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-lg">{getSeverityIcon(notification.severity)}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{notification.title}</p>
                      <p className="text-xs text-slate-400 mt-0.5">{notification.location_name || 'Unknown'}</p>
                      <p className="text-xs text-slate-500 mt-1">
                        {formatDistanceToNow(new Date(notification.event_time), { addSuffix: true })}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-white/10">
          <button className="w-full py-2.5 text-sm text-cyan-400 hover:text-cyan-300 font-medium rounded-xl hover:bg-cyan-500/10 transition-colors">
            View all notifications
          </button>
        </div>
      </div>
    </>
  );

  return ReactDOM.createPortal(panelContent, document.body);
};

export default NotificationPanel;
