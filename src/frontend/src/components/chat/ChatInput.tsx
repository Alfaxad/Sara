'use client';

import { useState, useCallback, KeyboardEvent } from 'react';
import { cn } from '@/lib/utils';
import { ArrowRight, Loader2 } from 'lucide-react';

export interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  isComplete?: boolean;
  placeholder?: string;
  className?: string;
}

export function ChatInput({
  onSend,
  isLoading = false,
  disabled = false,
  isComplete = false,
  placeholder = 'Message Sara...',
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
  const canSend = value.trim() && !isDisabled;

  // Hide input when demo is complete
  if (isComplete) {
    return (
      <div
        className={cn(
          'p-4 border-t border-sara-border',
          className
        )}
      >
        <div className="text-center text-body-small text-sara-text-muted py-2">
          Demo complete. Click Reset to try again.
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'p-4',
        className
      )}
      role="form"
      aria-label="Message input"
    >
      <div className="sara-chat-input">
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
        />
        {isDisabled && (
          <span id="input-status" className="sr-only">
            {isLoading ? 'Processing message, please wait' : 'Input is disabled'}
          </span>
        )}

        <button
          onClick={handleSend}
          disabled={!canSend}
          className={cn(
            'sara-icon-btn',
            !canSend && 'opacity-40 cursor-not-allowed'
          )}
          aria-label={isLoading ? 'Sending message' : 'Send message'}
        >
          {isLoading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
          ) : (
            <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
          )}
        </button>
      </div>
    </div>
  );
}

export default ChatInput;
