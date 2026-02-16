'use client';

import { cn } from '@/lib/utils';
import { ArrowLeft, RotateCcw } from 'lucide-react';
import Link from 'next/link';
import type { Task } from '@/lib/tasks';
import type { Message } from '@/hooks/useChat';
import { Button } from '@/components/ui/Button';
import { ErrorState } from '@/components/ui/ErrorState';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';

export interface ChatPanelProps {
  task: Task | null;
  messages: Message[];
  isLoading: boolean;
  isComplete: boolean;
  error?: string | null;
  onSendMessage: (message: string) => void;
  onReset?: () => void;
  onRetry?: () => void;
  className?: string;
}

export function ChatPanel({
  task,
  messages,
  isLoading,
  isComplete,
  error,
  onSendMessage,
  onReset,
  onRetry,
  className,
}: ChatPanelProps) {
  return (
    <div
      className={cn(
        'flex flex-col h-full',
        'bg-sara-bg-base',
        className
      )}
      role="main"
      aria-label="Chat panel"
    >
      {/* Header */}
      <header
        className={cn(
          'flex items-center justify-between gap-4 px-4 py-3',
          'bg-sara-bg-surface border-b border-sara-border'
        )}
      >
        <div className="flex items-center gap-3">
          <Link href="/" aria-label="Back to task list">
            <Button variant="ghost" size="sm" aria-label="Back to tasks">
              <ArrowLeft className="w-4 h-4" aria-hidden="true" />
            </Button>
          </Link>

          <div>
            <h1 className="text-subheading text-sara-text-primary">
              {task?.name || 'Chat'}
            </h1>
            {task && (
              <p className="text-body-small text-sara-text-muted">
                {task.context}
              </p>
            )}
          </div>
        </div>

        {onReset && isComplete && (
          <Button
            variant="secondary"
            size="sm"
            onClick={onReset}
            leftIcon={<RotateCcw className="w-4 h-4" aria-hidden="true" />}
            aria-label="Reset conversation"
          >
            Reset
          </Button>
        )}
      </header>

      {/* Error State */}
      {error && !isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <ErrorState
            title="Connection Error"
            message={error}
            onRetry={onRetry}
          />
        </div>
      )}

      {/* Messages */}
      {!error && (
        <MessageList
          messages={messages}
          isLoading={isLoading}
          className="flex-1"
        />
      )}

      {/* Input */}
      <ChatInput
        onSend={onSendMessage}
        isLoading={isLoading}
        disabled={!task || !!error}
        placeholder={
          error
            ? 'Fix the error to continue...'
            : isComplete
            ? 'Ask a follow-up question...'
            : 'Type a message...'
        }
      />
    </div>
  );
}

export default ChatPanel;
