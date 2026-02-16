'use client';

import { cn } from '@/lib/utils';
import { ArrowLeft, RotateCcw } from 'lucide-react';
import Link from 'next/link';
import type { Task } from '@/lib/tasks';
import type { Message } from '@/hooks/useChat';
import { Button } from '@/components/ui/Button';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';

export interface ChatPanelProps {
  task: Task | null;
  messages: Message[];
  isLoading: boolean;
  isComplete: boolean;
  onSendMessage: (message: string) => void;
  onReset?: () => void;
  className?: string;
}

export function ChatPanel({
  task,
  messages,
  isLoading,
  isComplete,
  onSendMessage,
  onReset,
  className,
}: ChatPanelProps) {
  return (
    <div
      className={cn(
        'flex flex-col h-full',
        'bg-sara-bg-base',
        className
      )}
    >
      {/* Header */}
      <header
        className={cn(
          'flex items-center justify-between gap-4 px-4 py-3',
          'bg-sara-bg-surface border-b border-sara-border'
        )}
      >
        <div className="flex items-center gap-3">
          <Link href="/">
            <Button variant="ghost" size="sm" aria-label="Back to tasks">
              <ArrowLeft className="w-4 h-4" />
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
            leftIcon={<RotateCcw className="w-4 h-4" />}
          >
            Reset
          </Button>
        )}
      </header>

      {/* Messages */}
      <MessageList
        messages={messages}
        isLoading={isLoading}
        className="flex-1"
      />

      {/* Input */}
      <ChatInput
        onSend={onSendMessage}
        isLoading={isLoading}
        disabled={!task}
        placeholder={
          isComplete
            ? 'Ask a follow-up question...'
            : 'Type a message...'
        }
      />
    </div>
  );
}

export default ChatPanel;
