import React, { useState, useMemo } from 'react';
import { Alert } from '../types';
import AlertCard from './AlertCard';

interface AlertListProps {
  alerts: Alert[];
  isLoading?: boolean;
  onAlertClick?: (alert: Alert) => void;
  showFilters?: boolean;
}

const AlertList: React.FC<AlertListProps> = ({
  alerts,
  isLoading,
  onAlertClick,
  showFilters = true,
}) => {
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [filterType, setFilterType] = useState<string>('ALL');
  const [showAnomaliesOnly, setShowAnomaliesOnly] = useState(false);

  const filteredAlerts = alerts.filter((alert) => {
    if (filterSeverity !== 'ALL' && alert.severity !== filterSeverity) return false;
    if (filterType !== 'ALL' && alert.alert_type !== filterType) return false;
    if (showAnomaliesOnly && !alert.is_anomaly) return false;
    return true;
  });

  const sortedAlerts = [...filteredAlerts].sort(
    (a, b) => new Date(b.event_time).getTime() - new Date(a.event_time).getTime()
  );

  const alertsByDate = useMemo(() => {
    const groups: { date: string; alerts: Alert[] }[] = [];
    
    sortedAlerts.forEach((alert) => {
      const alertDate = new Date(alert.event_time).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
      
      const existingGroup = groups.find((g) => g.date === alertDate);
      if (existingGroup) {
        existingGroup.alerts.push(alert);
      } else {
        groups.push({ date: alertDate, alerts: [alert] });
      }
    });
    
    return groups;
  }, [sortedAlerts]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="relative">
          <div className="w-12 h-12 border-4 border-blue-500/20 rounded-full"></div>
          <div className="absolute top-0 w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <p className="mt-4 text-slate-400 text-sm">Loading alerts...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {showFilters && (
        <div className="flex flex-wrap items-center gap-4 p-4 bg-slate-900/50 rounded-xl border border-slate-800/50">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1.5 uppercase tracking-wider">Severity</label>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="input py-2 text-sm min-w-[140px]"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
          
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1.5 uppercase tracking-wider">Type</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="input py-2 text-sm min-w-[140px]"
            >
              <option value="ALL">All Types</option>
              <option value="EARTHQUAKE">🌋 Earthquake</option>
              <option value="STORM">⛈️ Storm</option>
              <option value="FLOOD">🌊 Flood</option>
              <option value="FIRE">🔥 Fire</option>
              <option value="GENERAL">⚠️ General</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2 pt-5">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                id="anomalies-only"
                checked={showAnomaliesOnly}
                onChange={(e) => setShowAnomaliesOnly(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
            <label htmlFor="anomalies-only" className="text-sm text-slate-300">
              Anomalies Only
            </label>
          </div>
          
          <div className="ml-auto pt-5">
            <div className="bg-slate-800/50 px-4 py-2 rounded-lg">
              <span className="text-sm text-slate-400">
                <span className="font-semibold text-white">{filteredAlerts.length}</span> of {alerts.length} alerts
              </span>
            </div>
          </div>
        </div>
      )}
      
      {sortedAlerts.length === 0 ? (
        <div className="text-center py-16 bg-slate-900/30 rounded-xl border border-slate-800/50">
          <div className="w-16 h-16 mx-auto mb-4 bg-slate-800 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-slate-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <p className="text-slate-400 font-medium">No alerts match your filters</p>
          <p className="text-sm text-slate-500 mt-1">Try adjusting your filter criteria</p>
        </div>
      ) : (
        <div className="space-y-6">
          {alertsByDate.map((group) => (
            <div key={group.date}>
              <div className="flex items-center gap-3 mb-3">
                <div className="h-px flex-1 bg-slate-800/50" />
                <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{group.date}</span>
                <div className="h-px flex-1 bg-slate-800/50" />
              </div>
              <div className="grid gap-4">
                {group.alerts.map((alert, index) => (
                  <div
                    key={alert.id}
                    className="animate-slide-up"
                    style={{ animationDelay: `${index * 0.05}s` }}
                  >
                    <AlertCard
                      alert={alert}
                      onClick={() => onAlertClick?.(alert)}
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertList;
