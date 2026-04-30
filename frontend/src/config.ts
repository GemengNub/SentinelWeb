// Capacitor is optional - only used for native apps
let Capacitor = {
  isNativePlatform: () => false,
  getPlatform: () => 'web'
};

function getDefaultWsUrl() {
  if (typeof window === 'undefined') {
    return 'ws://localhost:8000/api/v1/ws';
  }

  const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${wsProtocol}://${window.location.host}/api/v1/ws`;
}

export const config = {
  appName: 'Sentinel',
  version: '1.0.0',
  apiBaseUrl: import.meta.env.VITE_API_URL || '/api/v1',
  wsUrl: import.meta.env.VITE_WS_URL || getDefaultWsUrl(),
  isNative: Capacitor.isNativePlatform(),
  platform: Capacitor.getPlatform(),
};

export default config;
