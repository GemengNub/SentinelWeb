import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketMessage, Alert } from '../types';
import { useAppStore } from '../store';
import toast from 'react-hot-toast';
import config from '../config';

interface UseWebSocketOptions {
  url?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    url = config.wsUrl,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastAlert, setLastAlert] = useState<Alert | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const { addAlert, setWsConnected } = useAppStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setWsConnected(true);
        reconnectAttemptsRef.current = 0;

        // Send ping to keep alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);

        ws.addEventListener('close', () => {
          clearInterval(pingInterval);
        });
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          switch (message.type) {
            case 'alert':
              const alertData = message.data as Alert;
              setLastAlert(alertData);
              addAlert(alertData);
              
              // Show toast for high severity alerts
              if (['HIGH', 'CRITICAL'].includes(alertData.severity)) {
                toast(`${alertData.severity}: ${alertData.title}`, {
                  icon: alertData.severity === 'CRITICAL' ? '🚨' : '⚠️',
                  duration: 5000,
                });
              }
              break;
              
            case 'connected':
              console.log('WebSocket client ID:', message.client_id);
              break;
              
            case 'pong':
              // Keep-alive response
              break;
              
            default:
              console.log('WebSocket message:', message);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setWsConnected(false);
        wsRef.current = null;

        // Attempt to reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.log(
            `Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`
          );
          
          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else {
          toast.error('Connection lost. Please refresh the page.');
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [url, reconnectInterval, maxReconnectAttempts, addAlert, setWsConnected]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
    }
  }, []);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const subscribe = useCallback((topic: string) => {
    sendMessage({ type: 'subscribe', topic });
  }, [sendMessage]);

  const unsubscribe = useCallback((topic: string) => {
    sendMessage({ type: 'unsubscribe', topic });
  }, [sendMessage]);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastAlert,
    connect,
    disconnect,
    sendMessage,
    subscribe,
    unsubscribe,
  };
}

export default useWebSocket;
