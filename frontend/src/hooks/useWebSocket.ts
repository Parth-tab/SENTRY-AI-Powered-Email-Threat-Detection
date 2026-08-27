import { useState, useEffect, useRef } from "react";

function getWebSocketUrl(): string {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.hostname || "127.0.0.1";
    return `${proto}//${host}:8000/api/v1/dashboard/live`;
  }
  return "ws://127.0.0.1:8000/api/v1/dashboard/live";
}

export function useWebSocket(onNewAlert?: (alert: any) => void, onEmailAnalyzed?: (data: any) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimeout: any;

    const connect = () => {
      try {
        const url = getWebSocketUrl();
        ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setLastMessage(data);

            if (data.type === "NEW_ALERT" && onNewAlert) {
              onNewAlert(data.data);
            }
            if (data.type === "EMAIL_ANALYZED" && onEmailAnalyzed) {
              onEmailAnalyzed(data.data);
            }
          } catch (e) {
            // ignore non-json keepalive messages
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          reconnectTimeout = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          setIsConnected(false);
          ws.close();
        };
      } catch (e) {
        setIsConnected(false);
        reconnectTimeout = setTimeout(connect, 3000);
      }
    };

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return { isConnected, lastMessage };
}
