import React from 'react';
import { Link } from 'react-router-dom';
import { useAlerts, useAlertStats, useActiveAlerts } from '../services/api';
import { useAppStore } from '../store';
import AlertList from '../components/AlertList';
import MapView from '../components/MapView';

const Dashboard: React.FC = () => {
  const { data: alertsData, isLoading: alertsLoading } = useAlerts({ pageSize: 5, isActive: true });
  const { data: stats, isLoading: statsLoading } = useAlertStats();
  const { data: activeAlerts } = useActiveAlerts();
  const { setSelectedAlert } = useAppStore();

  const totalAlerts = stats?.total_alerts || 0;
  const activeCount = stats?.active_alerts || 0;
  const recent24h = stats?.recent_24h || 0;
  const anomaliesDetected = stats?.anomalies_detected || 0;

  const activePercent = totalAlerts > 0 ? Math.round((activeCount / totalAlerts) * 100) : 0;
  const recentPercent = totalAlerts > 0 ? Math.round((recent24h / totalAlerts) * 100) : 0;
  const anomalyPercent = totalAlerts > 0 ? Math.round((anomaliesDetected / totalAlerts) * 100) : 0;

  const statsCards = [
    {
      label: 'Total Alerts',
      value: totalAlerts,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      color: 'cyan',
      trend: `${activePercent}% active`,
      trendUp: true,
    },
    {
      label: 'Active Alerts',
      value: activeCount,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      ),
      color: 'amber',
      trend: `of ${totalAlerts} total`,
      trendUp: true,
    },
    {
      label: 'Last 24 Hours',
      value: recent24h,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'teal',
      trend: `${recentPercent}% of total`,
      trendUp: true,
    },
    {
      label: 'Anomalies Detected',
      value: anomaliesDetected,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      color: 'rose',
      trend: `${anomalyPercent}% of total`,
      trendUp: true,
    },
  ];

  const colorClasses: Record<string, string> = {
    cyan: 'from-cyan-500/20 to-cyan-600/10 border-cyan-500/30',
    amber: 'from-amber-500/20 to-amber-600/10 border-amber-500/30',
    teal: 'from-teal-500/20 to-teal-600/10 border-teal-500/30',
    rose: 'from-rose-500/20 to-rose-600/10 border-rose-500/30',
  };

  const iconColors: Record<string, string> = {
    cyan: 'text-cyan-400 bg-cyan-500/20',
    amber: 'text-amber-400 bg-amber-500/20',
    teal: 'text-teal-400 bg-teal-500/20',
    rose: 'text-rose-400 bg-rose-500/20',
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-1">Real-time disaster monitoring overview</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-400 bg-slate-900/50 px-4 py-2 rounded-lg border border-slate-800/50">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Updated: {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        {statsCards.map((stat, index) => (
          <div
            key={stat.label}
            className={`stat-card bg-gradient-to-br ${colorClasses[stat.color]} animate-slide-up`}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`p-3 rounded-xl ${iconColors[stat.color]}`}>
                {stat.icon}
              </div>
              <div className={`flex items-center gap-1 text-sm font-medium ${
                stat.trendUp ? 'text-emerald-400' : 'text-red-400'
              }`}>
                <svg className={`w-4 h-4 ${!stat.trendUp && 'rotate-180'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                </svg>
                {stat.trend}
              </div>
            </div>
            <div>
              {statsLoading ? (
                <div className="h-8 w-16 bg-slate-800 rounded animate-pulse mb-1" />
              ) : (
                <p className="text-3xl font-bold text-white">{stat.value}</p>
              )}
              <p className="text-sm text-slate-400 mt-1">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Recent Alerts */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white">Recent Alerts</h2>
              <p className="text-sm text-slate-400 mt-1">Latest disaster alerts</p>
            </div>
            <Link
              to="/alerts"
              className="text-sm text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 transition-colors"
            >
              View all
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
          <AlertList
            alerts={(alertsData?.alerts || []).slice(0, 3)}
            isLoading={alertsLoading}
            onAlertClick={setSelectedAlert}
            showFilters={false}
          />
        </div>

        {/* Map View */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white">Live Map</h2>
              <p className="text-sm text-slate-400 mt-1">Active disaster locations</p>
            </div>
            <Link
              to="/map"
              className="text-sm text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 transition-colors"
            >
              Full map
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </Link>
          </div>
          <div className="h-[300px] md:h-[400px] rounded-lg overflow-hidden">
            <MapView
              alerts={activeAlerts || []}
              zoom={2}
              onAlertClick={setSelectedAlert}
            />
          </div>
        </div>
      </div>

      {/* Stats by Category */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alerts by Severity */}
        {stats?.alerts_by_severity && (
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-6">Alerts by Severity</h2>
            <div className="space-y-4">
              {Object.entries(stats.alerts_by_severity).map(([severity, count]) => {
                const total = Object.values(stats.alerts_by_severity).reduce((a, b) => a + b, 0);
                const percentage = total > 0 ? (count / total) * 100 : 0;
                
                return (
                  <div key={severity} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            severity === 'CRITICAL'
                              ? 'bg-red-500'
                              : severity === 'HIGH'
                              ? 'bg-orange-500'
                              : severity === 'MEDIUM'
                              ? 'bg-amber-500'
                              : 'bg-emerald-500'
                          }`}
                        />
                        <span className="text-sm font-medium text-slate-300">{severity}</span>
                      </div>
                      <span className="text-sm font-semibold text-white">{count}</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          severity === 'CRITICAL'
                            ? 'bg-gradient-to-r from-red-600 to-red-500'
                            : severity === 'HIGH'
                            ? 'bg-gradient-to-r from-orange-600 to-orange-500'
                            : severity === 'MEDIUM'
                            ? 'bg-gradient-to-r from-amber-600 to-amber-500'
                            : 'bg-gradient-to-r from-emerald-600 to-emerald-500'
                        }`}
                        style={{ width: `${Math.min(100, percentage)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Alerts by Type */}
        {stats?.alerts_by_type && (
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-6">Alerts by Type</h2>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(stats.alerts_by_type).map(([type, count]) => (
                <div
                  key={type}
                  className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/30 hover:border-slate-600/50 transition-colors"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-slate-700/50 rounded-lg flex items-center justify-center text-xl">
                      {type === 'EARTHQUAKE'
                        ? '🌋'
                        : type === 'STORM'
                        ? '⛈️'
                        : type === 'FLOOD'
                        ? '🌊'
                        : '🔥'}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">{type}</p>
                      <p className="text-xs text-slate-500">Total events</p>
                    </div>
                  </div>
                  <p className="text-2xl font-bold text-white">{count}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
