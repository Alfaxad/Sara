'use client';

import { cn } from '@/lib/utils';
import { User } from 'lucide-react';

export interface UserMessageProps {
  content: string;
  timestamp: number;
  className?: string;
}

export function UserMessage({ content, className }: UserMessageProps) {
  return (
    <div
      className={cn(
        'flex items-start gap-3 justify-end',
        'animate-sara-slide-up',
        className
      )}
    >
      <div
        className={cn(
          'max-w-[80%] px-4 py-3 rounded-sara',
          'bg-sara-accent text-white',
          'text-body'
        )}
      >
        {content}
      </div>

      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full',
          'bg-sara-bg-subtle border border-sara-border',
          'flex items-center justify-center'
        )}
      >
        <User className="w-4 h-4 text-sara-text-secondary" />
      </div>
    </div>
  );
}

export default UserMessage;
