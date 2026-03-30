import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Alert, FilterState, AlertStats } from '../types';

export interface SavedView {
  id: string;
  name: string;
  filters: FilterState;
  createdAt: string;
}

interface AppStore {
  // Alerts
  alerts: Alert[];
  setAlerts: (alerts: Alert[]) => void;
  addAlert: (alert: Alert) => void;
  
  // Filters
  filters: FilterState;
  setFilters: (filters: Partial<FilterState>) => void;
  resetFilters: () => void;
  
  // Saved Views
  savedViews: SavedView[];
  addSavedView: (name: string, filters: FilterState) => void;
  removeSavedView: (id: string) => void;
  applySavedView: (id: string) => void;
  
  // Stats
  stats: AlertStats | null;
  setStats: (stats: AlertStats) => void;
  
  // UI State
  selectedAlert: Alert | null;
  setSelectedAlert: (alert: Alert | null) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  
  // Connection
  wsConnected: boolean;
  setWsConnected: (connected: boolean) => void;
}

const initialFilters: FilterState = {
  severity: 'ALL',
  alertType: 'ALL',
  showAnomalies: false,
  dateRange: {
    start: null,
    end: null,
  },
};

export const useAppStore = create<AppStore>()(
  persist(
    (set, get) => ({
      // Alerts
      alerts: [],
      setAlerts: (alerts) => set({ alerts }),
      addAlert: (alert) =>
        set((state) => ({
          alerts: [alert, ...state.alerts].slice(0, 1000),
        })),

      // Filters
      filters: initialFilters,
      setFilters: (newFilters) =>
        set((state) => ({
          filters: { ...state.filters, ...newFilters },
        })),
      resetFilters: () => set({ filters: initialFilters }),

      // Saved Views
      savedViews: [],
      addSavedView: (name, filters) =>
        set((state) => ({
          savedViews: [
            ...state.savedViews,
            {
              id: crypto.randomUUID(),
              name,
              filters,
              createdAt: new Date().toISOString(),
            },
          ],
        })),
      removeSavedView: (id) =>
        set((state) => ({
          savedViews: state.savedViews.filter((v) => v.id !== id),
        })),
      applySavedView: (id) => {
        const view = get().savedViews.find((v) => v.id === id);
        if (view) {
          set({ filters: view.filters });
        }
      },

      // Stats
      stats: null,
      setStats: (stats) => set({ stats }),

      // UI State
      selectedAlert: null,
      setSelectedAlert: (alert) => set({ selectedAlert: alert }),
      sidebarOpen: true,
      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      // Connection
      wsConnected: false,
      setWsConnected: (connected) => set({ wsConnected: connected }),
    }),
    {
      name: 'sentinel-views',
      partialize: (state) => ({ savedViews: state.savedViews }),
    }
  )
);
