'use client';

import { cn } from '@/lib/utils';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import type { Task } from '@/lib/tasks';
import type { Message } from '@/hooks/useChat';
import type { WorkflowStep } from '@/lib/workflow';
import { ErrorState } from '@/components/ui/ErrorState';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';

export interface ChatPanelProps {
  task: Task | null;
  messages: Message[];
  workflowSteps?: WorkflowStep[];
  isLoading: boolean;
  isComplete: boolean;
  error?: string | null;
  onSendMessage: (message: string) => void;
  onRetry?: () => void;
  className?: string;
}

export function ChatPanel({
  task,
  messages,
  workflowSteps = [],
  isLoading,
  isComplete,
  error,
  onSendMessage,
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
          'border-b border-sara-border'
        )}
      >
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className={cn(
              'flex items-center justify-center w-8 h-8 rounded-full',
              'hover:bg-sara-accent-soft transition-colors'
            )}
            aria-label="Back to tasks"
          >
            <ArrowLeft className="w-4 h-4 text-sara-text-secondary" aria-hidden="true" />
          </Link>

          <div>
            <h1 className="text-subheading text-sara-text-primary">
              {task?.name || 'Chat'}
            </h1>
            {task && (
              <p className="text-body-small text-sara-text-muted line-clamp-1 max-w-md">
                {task.context}
              </p>
            )}
          </div>
        </div>

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
          workflowSteps={workflowSteps}
          isLoading={isLoading}
          className="flex-1"
        />
      )}

      {/* Input */}
      <ChatInput
        onSend={onSendMessage}
        isLoading={isLoading}
        disabled={!task || !!error}
        isComplete={isComplete}
        placeholder={
          error
            ? 'Fix the error to continue...'
            : 'Message Sara...'
        }
      />
    </div>
  );
}

export default ChatPanel;
