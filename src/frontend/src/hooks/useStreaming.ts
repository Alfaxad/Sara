'use client';

import { useState, useCallback, useRef } from 'react';
import { createParser, type EventSourceMessage } from 'eventsource-parser';
import { API_URL, type SSEEvent } from '@/lib/api';

// Modal cold starts can take 30-60s, so we need a generous timeout
const REQUEST_TIMEOUT_MS = 180000; // 3 minutes
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 2000;

export interface StreamingState {
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  retryCount: number;
  isWarmingUp: boolean;
}

export interface StreamingOptions {
  onEvent: (event: SSEEvent) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
  onWarmingUp?: () => void;
}

export function useStreaming(options: StreamingOptions) {
  const { onEvent, onComplete, onError, onWarmingUp } = options;
  const [state, setState] = useState<StreamingState>({
    isConnected: false,
    isLoading: false,
    error: null,
    retryCount: 0,
    isWarmingUp: false,
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const warmupTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const clearTimeouts = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (warmupTimeoutRef.current) {
      clearTimeout(warmupTimeoutRef.current);
      warmupTimeoutRef.current = null;
    }
  }, []);

  const startStream = useCallback(async (
    taskId: string,
    prompt: string,
    context: string,
    retryAttempt = 0
  ) => {
    // Cancel any existing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    clearTimeouts();

    abortControllerRef.current = new AbortController();

    setState({
      isConnected: true,
      isLoading: true,
      error: null,
      retryCount: retryAttempt,
      isWarmingUp: false,
    });

    // Set a warmup indicator after 5 seconds (indicates cold start)
    warmupTimeoutRef.current = setTimeout(() => {
      setState(prev => ({ ...prev, isWarmingUp: true }));
      onWarmingUp?.();
    }, 5000);

    // Set an overall timeout for the request
    const timeoutPromise = new Promise<never>((_, reject) => {
      timeoutRef.current = setTimeout(() => {
        abortControllerRef.current?.abort();
        reject(new Error('Request timed out - the server may be warming up'));
      }, REQUEST_TIMEOUT_MS);
    });

    try {
      const fetchPromise = fetch(`${API_URL}/api/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ taskId, prompt, context }),
        signal: abortControllerRef.current.signal,
      });

      // Race between fetch and timeout
      const response = await Promise.race([fetchPromise, timeoutPromise]);

      // Clear warmup indicator once we get a response
      clearTimeouts();
      setState(prev => ({ ...prev, isWarmingUp: false }));

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
            const parsedData = JSON.parse(data);
            // The event type comes from the SSE 'event:' field, not from JSON data
            const sseEvent: SSEEvent = {
              type: (event.event || 'status') as SSEEvent['type'],
              data: parsedData,
            };
            onEvent(sseEvent);
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
      clearTimeouts();

      if (error instanceof Error && error.name === 'AbortError') {
        // Check if this was a timeout-triggered abort vs user-triggered
        if (state.isLoading && retryAttempt < MAX_RETRIES) {
          // Auto-retry on timeout
          console.log(`Retrying request (attempt ${retryAttempt + 1}/${MAX_RETRIES})...`);
          await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
          return startStream(taskId, prompt, context, retryAttempt + 1);
        }
        // User cancelled or max retries reached
        setState(prev => ({ ...prev, isLoading: false, isConnected: false, isWarmingUp: false }));
        return;
      }

      // Check if it's a timeout error and we can retry
      const isTimeoutError = error instanceof Error &&
        (error.message.includes('timeout') || error.message.includes('timed out'));

      if (isTimeoutError && retryAttempt < MAX_RETRIES) {
        console.log(`Request timed out, retrying (attempt ${retryAttempt + 1}/${MAX_RETRIES})...`);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
        return startStream(taskId, prompt, context, retryAttempt + 1);
      }

      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setState({
        isConnected: false,
        isLoading: false,
        error: errorMessage,
        retryCount: retryAttempt,
        isWarmingUp: false,
      });
      onError?.(errorMessage);
    }
  }, [onEvent, onComplete, onError, onWarmingUp, clearTimeouts, state.isLoading]);

  const stopStream = useCallback(() => {
    clearTimeouts();
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState({
      isConnected: false,
      isLoading: false,
      error: null,
      retryCount: 0,
      isWarmingUp: false,
    });
  }, [clearTimeouts]);

  return {
    ...state,
    startStream,
    stopStream,
  };
}
