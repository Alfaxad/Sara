'use client';

import { useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import type { Message } from '@/hooks/useChat';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { ThinkingIndicator } from './ThinkingIndicator';
import { WorkflowTimeline } from '@/components/workflow/WorkflowTimeline';
import type { WorkflowStep } from '@/lib/workflow';

export interface MessageListProps {
  messages: Message[];
  workflowSteps?: WorkflowStep[];
  isLoading?: boolean;
  className?: string;
}

export function MessageList({
  messages,
  workflowSteps = [],
  isLoading = false,
  className,
}: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, workflowSteps]);

  // Filter out tool_call messages - they'll be shown in WorkflowTimeline
  const displayMessages = messages.filter(m => m.type !== 'tool_call');
  const hasActiveWorkflow = workflowSteps.length > 0 && workflowSteps.some(s => s.status === 'running');

  return (
    <div
      ref={containerRef}
      className={cn(
        'flex-1 overflow-y-auto p-4 space-y-4',
        className
      )}
      role="log"
      aria-label="Chat messages"
      aria-live="polite"
      aria-relevant="additions"
    >
      {displayMessages.map((message) => {
        switch (message.type) {
          case 'user':
            return (
              <UserMessage
                key={message.id}
                content={message.content}
                timestamp={message.timestamp}
              />
            );

          case 'assistant':
            return (
              <AssistantMessage
                key={message.id}
                content={message.content}
                timestamp={message.timestamp}
              />
            );

          case 'thinking':
            return (
              <div key={message.id} className="pl-11">
                <ThinkingIndicator />
              </div>
            );

          default:
            return null;
        }
      })}

      {/* Show WorkflowTimeline when there are steps */}
      {workflowSteps.length > 0 && (
        <div className="pl-11">
          <WorkflowTimeline steps={workflowSteps} />
        </div>
      )}

      {/* Show thinking indicator if loading but no thinking message and no active workflow */}
      {isLoading && !messages.some((m) => m.type === 'thinking') && !hasActiveWorkflow && (
        <div className="pl-11">
          <ThinkingIndicator />
        </div>
      )}

      {/* Scroll anchor */}
      <div ref={bottomRef} />
    </div>
  );
}

export default MessageList;
