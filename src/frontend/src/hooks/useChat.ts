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
  return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
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
          const description = parseActionToDescription(action);
          const stepId = event.data.id as string || generateStepId();

          // Check if there's already a step with the same description
          // If so, don't add a duplicate - just update it to running
          const existingStepIndex = prev.workflowSteps.findIndex(
            s => s.description === description
          );

          let updatedSteps: WorkflowStep[];
          if (existingStepIndex >= 0) {
            // Update the existing step to running (it's a retry)
            updatedSteps = prev.workflowSteps.map((step, idx) =>
              idx === existingStepIndex
                ? { ...step, id: stepId, status: 'running' as const }
                : step
            );
          } else {
            // Create new workflow step
            const newStep: WorkflowStep = {
              id: stepId,
              action,
              description,
              status: 'running',
              timestamp: Date.now(),
            };
            updatedSteps = [...prev.workflowSteps, newStep];
          }

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
                  id: stepId,
                  tool: event.data.tool as string,
                  status: 'running',
                  args: event.data.args as Record<string, unknown>,
                },
              },
            ],
            workflowSteps: updatedSteps,
          };
        });
        break;

      case 'tool_result':
        // Tool completed
        setState(prev => {
          const toolId = event.data.id as string;
          const result = event.data.result;
          const status = event.data.status as string; // Keep for artifact filtering

          // Only mark as complete if it's a successful result
          // For errors, keep it as running - the agent will retry or continue
          const isSuccess = status !== 'error';

          // Update the tool call message
          const updatedMessages = prev.messages.map(m => {
            if (m.type === 'tool_call' && m.toolCall?.id === toolId) {
              return {
                ...m,
                content: isSuccess ? `${m.toolCall.tool} completed` : `Calling ${m.toolCall.tool}...`,
                toolCall: {
                  ...m.toolCall,
                  status: isSuccess ? 'complete' as const : 'running' as const,
                  result: isSuccess ? result : m.toolCall.result,
                },
              };
            }
            return m;
          });

          // Update workflow step status - only mark complete on success
          const updatedSteps = prev.workflowSteps.map(step => {
            if (step.id === toolId) {
              return {
                ...step,
                status: isSuccess ? 'complete' as const : 'running' as const,
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
              (resultObj.entry ? 'Bundle' : 'FHIR');

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

    // Reset state and immediately restart with the task question
    if (task) {
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

      // Start streaming with task question after a brief delay to ensure state is reset
      setTimeout(() => {
        startStream(taskId, task.question, task.context);
      }, 100);
    } else {
      setState({
        messages: [],
        artifacts: [],
        workflowSteps: [],
        isComplete: false,
        finalAnswer: null,
        isWarmingUp: false,
      });
    }
  }, [stopStream, task, taskId, startStream]);

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
