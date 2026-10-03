import { useState, useEffect, useRef, useCallback } from 'react';
import { storage } from '../utils/storage';

export const SSE_STATUS = {
  CONNECTING: 'CONNECTING',
  CONNECTED: 'CONNECTED',
  RECONNECTING: 'RECONNECTING',
  DISCONNECTED: 'DISCONNECTED'
};

export const useSSE = (onEventCallback) => {
  const [connectionStatus, setConnectionStatus] = useState(SSE_STATUS.DISCONNECTED);
  const callbackRef = useRef(onEventCallback);
  const abortControllerRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const isComponentMounted = useRef(true);
  const retryCount = useRef(0);

  useEffect(() => {
    callbackRef.current = onEventCallback;
  }, [onEventCallback]);

  const connectStream = useCallback(() => {
    const token = storage.getToken();
    if (!token) {
      setConnectionStatus(SSE_STATUS.DISCONNECTED);
      return;
    }

    // Cancel existing connection attempt if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setConnectionStatus((prev) =>
      prev === SSE_STATUS.CONNECTED ? SSE_STATUS.RECONNECTING : SSE_STATUS.CONNECTING
    );

    const streamUrl = import.meta.env.VITE_API_BASE_URL 
      ? `${import.meta.env.VITE_API_BASE_URL}/api/stream`
      : '/api/stream';

    fetch(streamUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache'
      },
      signal: abortController.signal
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`SSE HTTP error: ${response.status}`);
        }
        if (!response.body) {
          throw new Error('ReadableStream not supported by response');
        }

        retryCount.current = 0;
        if (isComponentMounted.current) {
          setConnectionStatus(SSE_STATUS.CONNECTED);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (isComponentMounted.current) {
          const { value, done } = await reader.read();
          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          // Retain incomplete last line in buffer
          buffer = lines.pop() || '';

          let currentEventType = 'message';
          let currentEventData = '';

          for (const line of lines) {
            const trimmedLine = line.trim();
            if (!trimmedLine) {
              // Empty line signals dispatch of current event block
              if (currentEventData && callbackRef.current) {
                try {
                  const parsedData = JSON.parse(currentEventData);
                  callbackRef.current({
                    type: currentEventType,
                    data: parsedData
                  });
                } catch {
                  callbackRef.current({
                    type: currentEventType,
                    data: currentEventData
                  });
                }
              }
              currentEventType = 'message';
              currentEventData = '';
              continue;
            }

            if (trimmedLine.startsWith('event:')) {
              currentEventType = trimmedLine.slice(6).trim();
            } else if (trimmedLine.startsWith('data:')) {
              const dataContent = trimmedLine.slice(5).trim();
              currentEventData = currentEventData ? `${currentEventData}\n${dataContent}` : dataContent;
            } else if (trimmedLine.startsWith(':')) {
              // Comment/heartbeat line from server
              if (callbackRef.current) {
                callbackRef.current({ type: 'heartbeat', data: trimmedLine });
              }
            }
          }
        }
      })
      .catch((err) => {
        if (err.name === 'AbortError') {
          // Connection intentionally aborted (logout or unmount)
          return;
        }
        console.warn('SSE connection lost or error:', err.message);
        if (!isComponentMounted.current) return;

        setConnectionStatus(SSE_STATUS.RECONNECTING);

        // Exponential backoff reconnect: 3s, 6s, 12s, max 30s
        const backoffDelay = Math.min(3000 * Math.pow(1.5, retryCount.current), 30000);
        retryCount.current += 1;

        reconnectTimeoutRef.current = setTimeout(() => {
          if (isComponentMounted.current) {
            connectStream();
          }
        }, backoffDelay);
      });
  }, []);

  const disconnectStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setConnectionStatus(SSE_STATUS.DISCONNECTED);
  }, []);

  useEffect(() => {
    isComponentMounted.current = true;
    connectStream();

    return () => {
      isComponentMounted.current = false;
      disconnectStream();
    };
  }, [connectStream, disconnectStream]);

  return {
    connectionStatus,
    reconnect: connectStream,
    disconnect: disconnectStream
  };
};
