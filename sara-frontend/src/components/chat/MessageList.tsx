'use client';

import { useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import type { Message } from '@/hooks/useChat';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { ToolCallStatus } from './ToolCallStatus';
import { ThinkingIndicator } from './ThinkingIndicator';

export interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  className?: string;
}

export function MessageList({
  messages,
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
  }, [messages]);

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
      {messages.map((message) => {
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

          case 'tool_call':
            if (message.toolCall) {
              return (
                <div key={message.id} className="pl-11">
                  <ToolCallStatus
                    tool={message.toolCall.tool}
                    status={message.toolCall.status}
                  />
                </div>
              );
            }
            return null;

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

      {/* Show thinking indicator if loading but no thinking message */}
      {isLoading && !messages.some((m) => m.type === 'thinking') && (
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
