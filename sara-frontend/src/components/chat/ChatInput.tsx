'use client';

import { useState, useCallback, KeyboardEvent } from 'react';
import { cn } from '@/lib/utils';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export function ChatInput({
  onSend,
  isLoading = false,
  disabled = false,
  placeholder = 'Type a message...',
  className,
}: ChatInputProps) {
  const [value, setValue] = useState('');

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (trimmed && !isLoading && !disabled) {
      onSend(trimmed);
      setValue('');
    }
  }, [value, isLoading, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const isDisabled = isLoading || disabled;

  return (
    <div
      className={cn(
        'flex items-center gap-3 p-4',
        'bg-sara-bg-surface border-t border-sara-border',
        className
      )}
      role="form"
      aria-label="Message input"
    >
      <label htmlFor="chat-input" className="sr-only">
        Type your message
      </label>
      <input
        id="chat-input"
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isDisabled}
        aria-describedby={isDisabled ? 'input-status' : undefined}
        className={cn(
          'flex-1 px-4 py-3 rounded-sara-sm',
          'bg-sara-bg-base border border-sara-border',
          'text-body text-sara-text-primary',
          'placeholder:text-sara-text-muted',
          'focus:outline-none focus:border-sara-border-focus',
          'transition-colors duration-150',
          isDisabled && 'opacity-50 cursor-not-allowed'
        )}
      />
      {isDisabled && (
        <span id="input-status" className="sr-only">
          {isLoading ? 'Processing message, please wait' : 'Input is disabled'}
        </span>
      )}

      <Button
        onClick={handleSend}
        disabled={isDisabled || !value.trim()}
        variant="primary"
        size="md"
        isLoading={isLoading}
        aria-label={isLoading ? 'Sending message' : 'Send message'}
      >
        {!isLoading && <Send className="w-4 h-4" aria-hidden="true" />}
        <span className="sr-only">Send</span>
      </Button>
    </div>
  );
}

export default ChatInput;
