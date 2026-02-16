'use client';

import { cn } from '@/lib/utils';
import { Bot } from 'lucide-react';

export interface AssistantMessageProps {
  content: string;
  timestamp: number;
  isThinking?: boolean;
  className?: string;
}

export function AssistantMessage({
  content,
  isThinking = false,
  className,
}: AssistantMessageProps) {
  return (
    <div
      className={cn(
        'flex items-start gap-3',
        'animate-sara-slide-up',
        className
      )}
    >
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full',
          'bg-sara-accent-soft border border-sara-accent',
          'flex items-center justify-center',
          isThinking && 'animate-sara-pulse'
        )}
      >
        <Bot className="w-4 h-4 text-sara-accent" />
      </div>

      <div
        className={cn(
          'max-w-[80%] px-4 py-3 rounded-sara',
          'bg-sara-bg-surface border border-sara-border',
          'text-body text-sara-text-primary'
        )}
      >
        <div className="prose prose-sm prose-invert max-w-none">
          {content.split('\n').map((line, idx) => (
            <p key={idx} className={idx > 0 ? 'mt-2' : ''}>
              {line || '\u00A0'}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AssistantMessage;
