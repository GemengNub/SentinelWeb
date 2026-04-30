import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Alert, AlertListResponse, AlertStats, MetricsData } from '../types';
import config from '../config';

const api = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 10000,
});

// Alerts API
export function useAlerts(params?: {
  page?: number;
  pageSize?: number;
  severity?: string;
  alertType?: string;
  isActive?: boolean;
  isAnomaly?: boolean;
}) {
  return useQuery<AlertListResponse>({
    queryKey: ['alerts', params],
    queryFn: async () => {
      const pageSize = Math.min(params?.pageSize || 50, 100);
      const { data } = await api.get('/alerts/', {
        params: {
          page: params?.page || 1,
          page_size: pageSize,
          alert_type: params?.alertType,
          severity: params?.severity,
          is_anomaly: params?.isAnomaly,
          is_active: params?.isActive,
        },
      });
      return data;
    },
    refetchInterval: 30000,
    retry: 1,
  });
}

export function useAlert(id: string) {
  return useQuery<Alert>({
    queryKey: ['alert', id],
    queryFn: async () => {
      const { data } = await api.get(`/alerts/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useActiveAlerts() {
  return useQuery<Alert[]>({
    queryKey: ['alerts', 'active'],
    queryFn: async () => {
      const { data } = await api.get('/alerts/active');
      return data;
    },
    refetchInterval: 15000,
  });
}

export function useRecentAlerts(hours: number = 24) {
  return useQuery<Alert[]>({
    queryKey: ['alerts', 'recent', hours],
    queryFn: async () => {
      const { data } = await api.get('/alerts/recent', {
        params: { hours },
      });
      return data;
    },
    refetchInterval: 30000,
  });
}

export function useAlertStats() {
  return useQuery<AlertStats>({
    queryKey: ['alerts', 'stats'],
    queryFn: async () => {
      const { data } = await api.get('/alerts/stats');
      return data;
    },
    refetchInterval: 60000,
  });
}

// Metrics API
export function useMetrics(hours: number = 24) {
  return useQuery<MetricsData>({
    queryKey: ['metrics', hours],
    queryFn: async () => {
      const { data } = await api.get('/metrics/', {
        params: { hours },
      });
      return data;
    },
    refetchInterval: 60000,
  });
}

export function useHourlyMetrics(hours: number = 24) {
  return useQuery({
    queryKey: ['metrics', 'hourly', hours],
    queryFn: async () => {
      const { data } = await api.get('/metrics/hourly', {
        params: { hours },
      });
      return data;
    },
    refetchInterval: 300000,
  });
}

export function useSeverityTrend(days: number = 7) {
  return useQuery({
    queryKey: ['metrics', 'severity-trend', days],
    queryFn: async () => {
      const { data } = await api.get('/metrics/severity-trend', {
        params: { days },
      });
      return data;
    },
    refetchInterval: 300000,
  });
}

// Health API
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await api.get('/health');
      return data;
    },
    refetchInterval: 60000,
    retry: 3,
  });
}

// Mutation hooks
export function useAcknowledgeAlert() {
  return {
    mutate: async (alertId: string) => {
      const { data } = await api.post(`/alerts/${alertId}/acknowledge`);
      return data;
    },
  };
}

export function useDeactivateAlert() {
  return {
    mutate: async (alertId: string) => {
      const { data } = await api.post(`/alerts/${alertId}/deactivate`);
      return data;
    },
  };
}

export default api;
