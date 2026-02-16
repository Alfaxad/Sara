'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useStreaming } from './useStreaming';
import { TASKS } from '@/lib/tasks';
import type { SSEEvent } from '@/lib/api';

export interface Message {
  id: string;
  type: 'user' | 'assistant' | 'tool_call' | 'thinking';
  content: string;
  timestamp: number;
  toolCall?: {
    id: string;
    tool: string;
    status: 'pending' | 'running' | 'complete' | 'error';
    args?: Record<string, unknown>;
    result?: unknown;
  };
}

export interface Artifact {
  id: string;
  type: string;
  data: unknown;
  timestamp: number;
}

export interface ChatState {
  messages: Message[];
  artifacts: Artifact[];
  isComplete: boolean;
  finalAnswer: string | null;
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export function useChat(taskId: string) {
  const [state, setState] = useState<ChatState>({
    messages: [],
    artifacts: [],
    isComplete: false,
    finalAnswer: null,
  });

  const hasStartedRef = useRef(false);
  const task = TASKS.find((t) => t.id === taskId) || null;

  const handleEvent = useCallback((event: SSEEvent) => {
    switch (event.type) {
      case 'status':
        // Status updates - can be used for thinking indicator
        if (event.data.status === 'thinking') {
          setState(prev => {
            // Only add thinking message if not already present
            const hasThinking = prev.messages.some(m => m.type === 'thinking');
            if (hasThinking) return prev;
            return {
              ...prev,
              messages: [
                ...prev.messages,
                {
                  id: generateId(),
                  type: 'thinking',
                  content: 'Thinking...',
                  timestamp: Date.now(),
                },
              ],
            };
          });
        }
        break;

      case 'thinking':
        // Extended thinking content
        setState(prev => ({
          ...prev,
          messages: prev.messages.map(m =>
            m.type === 'thinking'
              ? { ...m, content: event.data.content as string || 'Processing...' }
              : m
          ),
        }));
        break;

      case 'tool_call':
        // Tool is being called
        setState(prev => {
          // Remove thinking indicator
          const filteredMessages = prev.messages.filter(m => m.type !== 'thinking');
          return {
            ...prev,
            messages: [
              ...filteredMessages,
              {
                id: generateId(),
                type: 'tool_call',
                content: `Calling ${event.data.tool}...`,
                timestamp: Date.now(),
                toolCall: {
                  id: event.data.id as string || generateId(),
                  tool: event.data.tool as string,
                  status: 'running',
                  args: event.data.args as Record<string, unknown>,
                },
              },
            ],
          };
        });
        break;

      case 'tool_result':
        // Tool completed
        setState(prev => {
          const toolId = event.data.id as string;
          const result = event.data.result;

          // Update the tool call message
          const updatedMessages = prev.messages.map(m => {
            if (m.type === 'tool_call' && m.toolCall?.id === toolId) {
              return {
                ...m,
                content: `${m.toolCall.tool} completed`,
                toolCall: {
                  ...m.toolCall,
                  status: 'complete' as const,
                  result,
                },
              };
            }
            return m;
          });

          // Add artifact if present
          const newArtifacts = [...prev.artifacts];
          if (result && typeof result === 'object') {
            newArtifacts.push({
              id: generateId(),
              type: event.data.tool as string || 'unknown',
              data: result,
              timestamp: Date.now(),
            });
          }

          return {
            ...prev,
            messages: updatedMessages,
            artifacts: newArtifacts,
          };
        });
        break;

      case 'complete':
        // Final response
        setState(prev => {
          // Remove thinking indicator
          const filteredMessages = prev.messages.filter(m => m.type !== 'thinking');
          return {
            ...prev,
            messages: [
              ...filteredMessages,
              {
                id: generateId(),
                type: 'assistant',
                content: event.data.response as string || event.data.answer as string || '',
                timestamp: Date.now(),
              },
            ],
            isComplete: true,
            finalAnswer: event.data.response as string || event.data.answer as string || null,
          };
        });
        break;

      case 'error':
        setState(prev => ({
          ...prev,
          messages: [
            ...prev.messages.filter(m => m.type !== 'thinking'),
            {
              id: generateId(),
              type: 'assistant',
              content: `Error: ${event.data.message || event.data.error || 'An error occurred'}`,
              timestamp: Date.now(),
            },
          ],
          isComplete: true,
        }));
        break;
    }
  }, []);

  const handleComplete = useCallback(() => {
    setState(prev => ({
      ...prev,
      messages: prev.messages.filter(m => m.type !== 'thinking'),
      isComplete: true,
    }));
  }, []);

  const handleError = useCallback((error: string) => {
    setState(prev => ({
      ...prev,
      messages: [
        ...prev.messages.filter(m => m.type !== 'thinking'),
        {
          id: generateId(),
          type: 'assistant',
          content: `Connection error: ${error}`,
          timestamp: Date.now(),
        },
      ],
      isComplete: true,
    }));
  }, []);

  const { isLoading, error, startStream, stopStream } = useStreaming({
    onEvent: handleEvent,
    onComplete: handleComplete,
    onError: handleError,
  });

  const sendMessage = useCallback((content: string) => {
    if (!task) return;

    // Add user message
    setState(prev => ({
      ...prev,
      messages: [
        ...prev.messages,
        {
          id: generateId(),
          type: 'user',
          content,
          timestamp: Date.now(),
        },
      ],
      isComplete: false,
    }));

    // Start streaming
    startStream(taskId, content, task.context);
  }, [task, taskId, startStream]);

  const reset = useCallback(() => {
    stopStream();
    setState({
      messages: [],
      artifacts: [],
      isComplete: false,
      finalAnswer: null,
    });
    hasStartedRef.current = false;
  }, [stopStream]);

  // Auto-run on mount with task question
  useEffect(() => {
    if (task && !hasStartedRef.current) {
      hasStartedRef.current = true;
      // Add initial user message from task
      setState({
        messages: [
          {
            id: generateId(),
            type: 'user',
            content: task.question,
            timestamp: Date.now(),
          },
        ],
        artifacts: [],
        isComplete: false,
        finalAnswer: null,
      });

      // Start streaming with task question
      startStream(taskId, task.question, task.context);
    }
  }, [task, taskId, startStream]);

  return {
    ...state,
    task,
    isLoading,
    error,
    sendMessage,
    reset,
    stopStream,
  };
}
