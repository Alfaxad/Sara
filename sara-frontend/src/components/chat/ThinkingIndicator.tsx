'use client';

import { cn } from '@/lib/utils';

export interface ThinkingIndicatorProps {
  className?: string;
}

export function ThinkingIndicator({ className }: ThinkingIndicatorProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="flex items-center gap-1">
        <span
          className="w-2 h-2 rounded-full bg-sara-accent animate-bounce"
          style={{ animationDelay: '0ms', animationDuration: '600ms' }}
        />
        <span
          className="w-2 h-2 rounded-full bg-sara-accent animate-bounce"
          style={{ animationDelay: '150ms', animationDuration: '600ms' }}
        />
        <span
          className="w-2 h-2 rounded-full bg-sara-accent animate-bounce"
          style={{ animationDelay: '300ms', animationDuration: '600ms' }}
        />
      </div>
      <span className="text-body-small text-sara-text-muted">Sara is thinking...</span>
    </div>
  );
}

export default ThinkingIndicator;
