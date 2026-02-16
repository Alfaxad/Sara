'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useStreaming } from './useStreaming';
import { TASKS } from '@/lib/tasks';
import type { SSEEvent } from '@/lib/api';
import { WorkflowStep, parseActionToDescription, generateStepId } from '@/lib/workflow';

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
  workflowSteps: WorkflowStep[];
  isComplete: boolean;
  finalAnswer: string | null;
  isWarmingUp: boolean;
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export function useChat(taskId: string) {
  const [state, setState] = useState<ChatState>({
    messages: [],
    artifacts: [],
    workflowSteps: [],
    isComplete: false,
    finalAnswer: null,
    isWarmingUp: false,
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
        setState(prev => {
          const filteredMessages = prev.messages.filter(m => m.type !== 'thinking');
          const toolName = event.data.tool as string;
          const args = event.data.args as Record<string, unknown>;

          // Create action string from tool call
          const method = args?.method as string || 'GET';
          const endpoint = args?.endpoint as string || `/${toolName}`;
          const action = `${method} ${endpoint}`;

          // Create new workflow step
          const newStep: WorkflowStep = {
            id: event.data.id as string || generateStepId(),
            action,
            description: parseActionToDescription(action),
            status: 'running',
            timestamp: Date.now(),
          };

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
            workflowSteps: [...prev.workflowSteps, newStep],
          };
        });
        break;

      case 'tool_result':
        // Tool completed
        setState(prev => {
          const toolId = event.data.id as string;
          const result = event.data.result;
          const status = event.data.status as string;

          // Find the matching tool call to get the tool name
          const matchingToolCall = prev.messages.find(
            m => m.type === 'tool_call' && m.toolCall?.id === toolId
          );
          const toolName = matchingToolCall?.toolCall?.tool || 'FHIR';

          // Update the tool call message
          const updatedMessages = prev.messages.map(m => {
            if (m.type === 'tool_call' && m.toolCall?.id === toolId) {
              return {
                ...m,
                content: status === 'error' ? `${m.toolCall.tool} failed` : `${m.toolCall.tool} completed`,
                toolCall: {
                  ...m.toolCall,
                  status: status === 'error' ? 'error' as const : 'complete' as const,
                  result,
                },
              };
            }
            return m;
          });

          // Update workflow step status
          const updatedSteps = prev.workflowSteps.map(step => {
            if (step.id === toolId) {
              return {
                ...step,
                status: status === 'error' ? 'error' as const : 'complete' as const,
              };
            }
            return step;
          });

          // Add artifact if present (only for SUCCESSFUL results with meaningful FHIR data)
          const newArtifacts = [...prev.artifacts];
          if (result && typeof result === 'object' && status !== 'error') {
            const resultObj = result as Record<string, unknown>;

            // Skip error responses
            if (resultObj.error || resultObj.status_code === 0) {
              // Don't add error results as artifacts
              return {
                ...prev,
                messages: updatedMessages,
                workflowSteps: updatedSteps,
              };
            }

            // Skip empty bundles (total: 0 or no entries)
            if (resultObj.resourceType === 'Bundle') {
              const entries = resultObj.entry as Array<unknown> | undefined;
              const total = resultObj.total as number | undefined;
              if (!entries || entries.length === 0 || total === 0) {
                // Don't add empty bundles as artifacts
                return {
                  ...prev,
                  messages: updatedMessages,
                  workflowSteps: updatedSteps,
                };
              }
            }

            // Determine the FHIR resource type from the result
            const resourceType = resultObj.resourceType as string ||
              (resultObj.entry ? 'Bundle' : toolName);

            newArtifacts.push({
              id: generateId(),
              type: resourceType,
              data: result,
              timestamp: Date.now(),
            });
          }

          return {
            ...prev,
            messages: updatedMessages,
            artifacts: newArtifacts,
            workflowSteps: updatedSteps,
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
    // Don't show timeout errors as chat errors - the UI will show a warmup indicator
    const isTimeoutError = error.includes('timeout') || error.includes('timed out');
    setState(prev => ({
      ...prev,
      messages: [
        ...prev.messages.filter(m => m.type !== 'thinking'),
        {
          id: generateId(),
          type: 'assistant',
          content: isTimeoutError
            ? 'The server is taking longer than expected. Please try again.'
            : `Connection error: ${error}`,
          timestamp: Date.now(),
        },
      ],
      isComplete: true,
      isWarmingUp: false,
    }));
  }, []);

  const handleWarmingUp = useCallback(() => {
    setState(prev => ({
      ...prev,
      isWarmingUp: true,
      messages: prev.messages.map(m =>
        m.type === 'thinking'
          ? { ...m, content: 'Connecting to Sara... (server warming up)' }
          : m
      ),
    }));
  }, []);

  const { isLoading, error, startStream, stopStream, isWarmingUp: streamWarmingUp } = useStreaming({
    onEvent: handleEvent,
    onComplete: handleComplete,
    onError: handleError,
    onWarmingUp: handleWarmingUp,
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
      workflowSteps: [],
      isComplete: false,
      finalAnswer: null,
      isWarmingUp: false,
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
        workflowSteps: [],
        isComplete: false,
        finalAnswer: null,
        isWarmingUp: false,
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
    isWarmingUp: state.isWarmingUp || streamWarmingUp,
    sendMessage,
    reset,
    stopStream,
  };
}
