'use client';

import { cn } from '@/lib/utils';

export interface UserMessageProps {
  content: string;
  timestamp: number;
  className?: string;
}

export function UserMessage({ content, className }: UserMessageProps) {
  return (
    <div
      className={cn(
        'flex justify-end',
        'animate-msg-in',
        className
      )}
    >
      <div className="sara-bubble sara-bubble-user">
        {content}
      </div>
    </div>
  );
}

export default UserMessage;
