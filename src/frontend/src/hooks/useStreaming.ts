'use client';

import { useState, useCallback, useRef } from 'react';
import { createParser, type EventSourceMessage } from 'eventsource-parser';
import { API_URL, type SSEEvent } from '@/lib/api';

export interface StreamingState {
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface StreamingOptions {
  onEvent: (event: SSEEvent) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useStreaming(options: StreamingOptions) {
  const { onEvent, onComplete, onError } = options;
  const [state, setState] = useState<StreamingState>({
    isConnected: false,
    isLoading: false,
    error: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const startStream = useCallback(async (
    taskId: string,
    prompt: string,
    context: string
  ) => {
    // Cancel any existing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    setState({
      isConnected: true,
      isLoading: true,
      error: null,
    });

    try {
      const response = await fetch(`${API_URL}/api/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ taskId, prompt, context }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const parser = createParser({
        onEvent: (event: EventSourceMessage) => {
          const data = event.data;
          if (data === '[DONE]') {
            setState(prev => ({ ...prev, isLoading: false }));
            onComplete?.();
            return;
          }
          try {
            const parsedEvent = JSON.parse(data) as SSEEvent;
            onEvent(parsedEvent);
          } catch {
            // Skip invalid JSON
          }
        },
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          setState(prev => ({ ...prev, isLoading: false, isConnected: false }));
          onComplete?.();
          break;
        }

        const text = decoder.decode(value, { stream: true });
        parser.feed(text);
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        // Stream was cancelled, don't treat as error
        setState(prev => ({ ...prev, isLoading: false, isConnected: false }));
        return;
      }

      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setState({
        isConnected: false,
        isLoading: false,
        error: errorMessage,
      });
      onError?.(errorMessage);
    }
  }, [onEvent, onComplete, onError]);

  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState({
      isConnected: false,
      isLoading: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    startStream,
    stopStream,
  };
}
