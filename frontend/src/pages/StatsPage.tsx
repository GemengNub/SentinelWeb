import React, { useState, useMemo, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useMetrics, useHourlyMetrics, useSeverityTrend } from '../services/api';
import axios from 'axios';
import config from '../config';

const exportReportToCSV = async (days: number) => {
  try {
    const response = await axios.get(`${config.apiBaseUrl}/metrics/severity-trend`, {
      params: { days },
    });
    
    const data = response.data?.daily_trend || [];
    const headers = ['Date', 'Critical', 'High', 'Medium', 'Low', 'Total'];
    const rows = data.map((day: Record<string, unknown>) => [
      day.date,
      day.critical,
      day.high,
      day.medium,
      day.low,
      day.total,
    ]);
    
    const csvContent = [headers, ...rows].map((row) => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `sentinel-report-${days}days-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  } catch (e) {
    console.error('Export failed', e);
  }
};

const SimpleBarChart: React.FC<{
  data: { label: string; value: number; color: string }[];
  maxValue?: number;
}> = ({ data, maxValue }) => {
  const max = maxValue || Math.max(...data.map((d) => d.value), 1);
  
  return (
    <div className="space-y-3">
      {data.map((item, index) => (
        <div key={index} className="group">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-slate-400">{item.label}</span>
            <span className="text-xs text-slate-300">{item.value}</span>
          </div>
          <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${(item.value / max) * 100}%`,
                backgroundColor: item.color,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

const SimpleLineChart: React.FC<{
  data: { time: string; value: number }[];
  color?: string;
}> = ({ data, color = '#06b6d4' }) => {
  if (!data.length) return null;
  
  const max = Math.max(...data.map((d) => d.value), 1);
  const min = Math.min(...data.map((d) => d.value), 0);
  const range = max - min || 1;
  
  const points = data
    .map((d, i) => {
      const x = (i / (data.length - 1)) * 100;
      const y = 100 - ((d.value - min) / range) * 100;
      return `${x},${y}`;
    })
    .join(' ');
  
  return (
    <div className="h-32 relative">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="2"
          points={points}
          vectorEffect="non-scaling-stroke"
        />
        {data.map((d, i) => {
          const x = (i / (data.length - 1)) * 100;
          const y = 100 - ((d.value - min) / range) * 100;
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r="2"
              fill={color}
              vectorEffect="non-scaling-stroke"
            />
          );
        })}
      </svg>
      <div className="flex justify-between mt-2 text-xs text-slate-500">
        <span>{data[0]?.time}</span>
        <span>{data[data.length - 1]?.time}</span>
      </div>
    </div>
  );
};

const HourlyBarChart: React.FC<{
  data: { hour: string; total: number; critical: number; high: number; medium: number; low: number }[];
}> = ({ data }) => {
  if (!data.length) return null;
  
  const max = Math.max(...data.map((d) => d.total), 1);
  
  const severityColors: Record<string, string> = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#eab308',
    low: '#22c55e',
  };
  
  return (
    <div className="space-y-2">
      <div className="flex items-end gap-1 h-40">
        {data.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center group">
            <div className="w-full flex flex-col-reverse rounded-t-sm overflow-hidden" style={{ height: `${(item.total / max) * 100}%` }}>
              {item.critical > 0 && (
                <div
                  className="w-full transition-all group-hover:opacity-80"
                  style={{ height: `${(item.critical / item.total) * 100}%`, backgroundColor: severityColors.critical }}
                  title={`Critical: ${item.critical}`}
                />
              )}
              {item.high > 0 && (
                <div
                  className="w-full transition-all group-hover:opacity-80"
                  style={{ height: `${(item.high / item.total) * 100}%`, backgroundColor: severityColors.high }}
                  title={`High: ${item.high}`}
                />
              )}
              {item.medium > 0 && (
                <div
                  className="w-full transition-all group-hover:opacity-80"
                  style={{ height: `${(item.medium / item.total) * 100}%`, backgroundColor: severityColors.medium }}
                  title={`Medium: ${item.medium}`}
                />
              )}
              {item.low > 0 && (
                <div
                  className="w-full transition-all group-hover:opacity-80"
                  style={{ height: `${(item.low / item.total) * 100}%`, backgroundColor: severityColors.low }}
                  title={`Low: ${item.low}`}
                />
              )}
            </div>
            <span className="text-[8px] text-slate-500 mt-1 truncate w-full text-center">
              {item.hour}
            </span>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-center gap-4 pt-2 border-t border-slate-800">
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-500" />
          <span className="text-xs text-slate-400">Critical</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-orange-500" />
          <span className="text-xs text-slate-400">High</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-amber-500" />
          <span className="text-xs text-slate-400">Medium</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="text-xs text-slate-400">Low</span>
        </div>
      </div>
    </div>
  );
};

const StatsPage: React.FC = () => {
  const { t } = useTranslation();
  const [timeWindow, setTimeWindow] = useState(24);
  const [slaThreshold, setSlaThreshold] = useState(15);
  const { data: metrics, isLoading: metricsLoading } = useMetrics(timeWindow);
  const { data: hourlyData } = useHourlyMetrics(timeWindow);
  const { data: trendData } = useSeverityTrend(7);
  const [slaData, setSlaData] = useState<{
    avgResponseTime: number;
    slaCompliance: number;
    acknowledgedAlerts: number;
    totalAlerts: number;
  } | null>(null);

  useEffect(() => {
    const fetchSlaData = async () => {
      try {
        const response = await fetch(`/api/v1/metrics/sla?hours=${timeWindow}&threshold_minutes=${slaThreshold}`);
        if (response.ok) {
          const data = await response.json();
          setSlaData({
            avgResponseTime: data.avg_response_time_minutes || 0,
            slaCompliance: data.sla_compliance_percent || 0,
            acknowledgedAlerts: data.acknowledged_alerts || 0,
            totalAlerts: data.total_alerts || 0,
          });
        }
      } catch (e) {
        console.error('Failed to fetch SLA data', e);
      }
    };
    fetchSlaData();
  }, [timeWindow, slaThreshold]);

  const severityData = useMemo(() => {
    if (!metrics?.alerts?.by_severity) return [];
    const colors: Record<string, string> = {
      CRITICAL: '#ef4444',
      HIGH: '#f97316',
      MEDIUM: '#eab308',
      LOW: '#22c55e',
    };
    return Object.entries(metrics.alerts.by_severity).map(([severity, count]) => ({
      label: severity,
      value: count as number,
      color: colors[severity] || '#6b7280',
    }));
  }, [metrics]);

  const typeData = useMemo(() => {
    if (!metrics?.alerts?.by_type) return [];
    const colors: Record<string, string> = {
      EARTHQUAKE: '#8b5cf6',
      STORM: '#3b82f6',
      FLOOD: '#06b6d4',
      FIRE: '#f97316',
      GENERAL: '#6b7280',
    };
    return Object.entries(metrics.alerts.by_type).map(([type, count]) => ({
      label: type,
      value: count as number,
      color: colors[type] || '#6b7280',
    }));
  }, [metrics]);

  const hourlyChartData = useMemo(() => {
    if (!hourlyData?.hourly) return [];
    return hourlyData.hourly.slice(-12).map((h: Record<string, unknown>) => ({
      time: `${h.hour}:00`,
      value: h.total as number,
    }));
  }, [hourlyData]);

  const hourlyBarData = useMemo(() => {
    if (!hourlyData?.hourly) return [];
    return hourlyData.hourly.slice(-24).map((h: Record<string, unknown>) => ({
      hour: String(h.hour).padStart(2, '0') + ':00',
      total: h.total as number,
      critical: h.critical as number || 0,
      high: h.high as number || 0,
      medium: h.medium as number || 0,
      low: h.low as number || 0,
    }));
  }, [hourlyData]);

  const responseTimes = useMemo(() => {
    if (slaData) {
      return {
        avgResponse: slaData.avgResponseTime,
        withinSla: slaData.slaCompliance,
        totalAlerts: slaData.totalAlerts,
        acknowledged: slaData.acknowledgedAlerts,
      };
    }
    return {
      avgResponse: 0,
      withinSla: 0,
      totalAlerts: metrics?.alerts?.total || 0,
      acknowledged: 0,
    };
  }, [slaData, metrics]);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white">{t('stats.title')}</h1>
          <p className="text-slate-400 mt-1">{t('stats.subtitle')}</p>
        </div>
        
        <div className="flex items-center gap-3">
          <select
            value={timeWindow}
            onChange={(e) => setTimeWindow(Number(e.target.value))}
            className="input min-w-[160px]"
          >
            <option value={1}>Last Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={12}>Last 12 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={48}>Last 48 Hours</option>
            <option value={168}>Last 7 Days</option>
          </select>
          
          <button
            onClick={() => exportReportToCSV(7)}
            className="btn btn-secondary flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {t('stats.exportReport')}
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        <div className="stat-card bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/20">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 bg-blue-500/20 rounded-xl">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <span className="text-sm font-medium text-blue-300">Total Alerts</span>
          </div>
          <p className="text-3xl font-bold text-white">
            {metricsLoading ? (
              <span className="inline-block w-16 h-8 bg-slate-800 rounded animate-pulse" />
            ) : (
              metrics?.alerts?.total || 0
            )}
          </p>
        </div>

        <div className="stat-card bg-gradient-to-br from-purple-500/10 to-purple-600/5 border border-purple-500/20">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 bg-purple-500/20 rounded-xl">
              <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
              </svg>
            </div>
            <span className="text-sm font-medium text-purple-300">Total Events</span>
          </div>
          <p className="text-3xl font-bold text-white">
            {metricsLoading ? (
              <span className="inline-block w-16 h-8 bg-slate-800 rounded animate-pulse" />
            ) : (
              metrics?.events?.total || 0
            )}
          </p>
        </div>

        <div className="stat-card bg-gradient-to-br from-red-500/10 to-red-600/5 border border-red-500/20">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 bg-red-500/20 rounded-xl">
              <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <span className="text-sm font-medium text-red-300">Anomalies Detected</span>
          </div>
          <p className="text-3xl font-bold text-white">
            {metricsLoading ? (
              <span className="inline-block w-16 h-8 bg-slate-800 rounded animate-pulse" />
            ) : (
              metrics?.anomalies?.detected || 0
            )}
          </p>
        </div>

        <div className="stat-card bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border border-emerald-500/20">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 bg-emerald-500/20 rounded-xl">
              <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <span className="text-sm font-medium text-emerald-300">Predictions Made</span>
          </div>
          <p className="text-3xl font-bold text-white">
            {metricsLoading ? (
              <span className="inline-block w-16 h-8 bg-slate-800 rounded animate-pulse" />
            ) : (
              metrics?.predictions?.total || 0
            )}
          </p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alerts by Severity */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-6">{t('stats.severityTrend')}</h2>
          <SimpleBarChart data={severityData} />
        </div>

        {/* Alerts by Type */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-6">{t('stats.typeDistribution')}</h2>
          <SimpleBarChart data={typeData} />
        </div>

        {/* Hourly Trend */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-6">{t('stats.hourlyDistribution')}</h2>
          {hourlyBarData.length > 0 ? (
            <HourlyBarChart data={hourlyBarData} />
          ) : (
            <div className="h-40 flex items-center justify-center text-slate-500">
              No hourly data available
            </div>
          )}
        </div>
      </div>

      {/* SLA & Response Time */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-6">{t('stats.responseTime')}</h2>
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Average Response Time</span>
              <span className="text-2xl font-bold text-white">{responseTimes.avgResponse} min</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">SLA Compliance</span>
                <span className={`font-semibold ${responseTimes.withinSla >= 90 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {responseTimes.withinSla}%
                </span>
              </div>
              <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${responseTimes.withinSla >= 90 ? 'bg-emerald-500' : 'bg-amber-500'}`}
                  style={{ width: `${responseTimes.withinSla}%` }}
                />
              </div>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-2 block">SLA Threshold (minutes)</label>
              <input
                type="number"
                value={slaThreshold}
                onChange={(e) => setSlaThreshold(Number(e.target.value))}
                className="input w-32"
                min={1}
                max={60}
              />
            </div>
          </div>
        </div>

        {/* Alerts Summary */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-6">Alert Summary</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
              <span className="text-slate-400">Total Alerts (Period)</span>
              <span className="text-white font-semibold">{responseTimes.totalAlerts}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
              <span className="text-slate-400">Acknowledged</span>
              <span className="text-emerald-400 font-semibold">{responseTimes.acknowledged || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
              <span className="text-slate-400">Pending</span>
              <span className="text-amber-400 font-semibold">{Math.max(0, responseTimes.totalAlerts - responseTimes.acknowledged)}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
              <span className="text-slate-400">Avg Response Time</span>
              <span className="text-blue-400 font-semibold">{responseTimes.avgResponse} min</span>
            </div>
          </div>
        </div>
      </div>

      {/* 7-Day Trend */}
      {trendData?.daily_trend && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-6">7-Day Trend</h2>
          <div className="overflow-x-auto -mx-6 px-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-slate-800">
                  <th className="text-left py-3 px-4 font-medium">Date</th>
                  <th className="text-right py-3 px-4 font-medium">Critical</th>
                  <th className="text-right py-3 px-4 font-medium">High</th>
                  <th className="text-right py-3 px-4 font-medium">Medium</th>
                  <th className="text-right py-3 px-4 font-medium">Low</th>
                  <th className="text-right py-3 px-4 font-medium">Total</th>
                </tr>
              </thead>
              <tbody>
                {trendData.daily_trend.map((day: Record<string, unknown>) => (
                  <tr
                    key={day.date as string}
                    className="text-slate-300 border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
                  >
                    <td className="py-3 px-4 font-medium">{day.date as string}</td>
                    <td className="text-right py-3 px-4 text-red-400">{day.critical as number}</td>
                    <td className="text-right py-3 px-4 text-orange-400">{day.high as number}</td>
                    <td className="text-right py-3 px-4 text-amber-400">{day.medium as number}</td>
                    <td className="text-right py-3 px-4 text-emerald-400">{day.low as number}</td>
                    <td className="text-right py-3 px-4 font-semibold text-white">{day.total as number}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* System Info */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-6">System Information</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="bg-slate-800/50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">API Version</p>
            <p className="text-lg font-semibold text-white">1.0.0</p>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Time Window</p>
            <p className="text-lg font-semibold text-white">{timeWindow} hours</p>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Last Updated</p>
            <p className="text-sm font-medium text-white">
              {metrics?.timestamp
                ? new Date(metrics.timestamp).toLocaleString()
                : 'N/A'}
            </p>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Data Sources</p>
            <p className="text-sm font-medium text-white">USGS, OpenWeather</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatsPage;
