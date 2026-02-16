'use client';

import { cn } from '@/lib/utils';

export interface AssistantMessageProps {
  content: string;
  timestamp: number;
  isThinking?: boolean;
  className?: string;
}

export function AssistantMessage({
  content,
  className,
}: AssistantMessageProps) {
  return (
    <div
      className={cn(
        'flex justify-start',
        'animate-msg-in',
        className
      )}
    >
      <div className="sara-bubble sara-bubble-assistant">
        {content.split('\n').map((line, idx) => (
          <p key={idx} className={idx > 0 ? 'mt-2' : ''}>
            {line || '\u00A0'}
          </p>
        ))}
      </div>
    </div>
  );
}

export default AssistantMessage;
