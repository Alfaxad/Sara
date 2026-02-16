'use client';

import { AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './Button';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-8 text-center',
        className
      )}
      role="alert"
      aria-live="polite"
    >
      <div
        className={cn(
          'w-16 h-16 rounded-full mb-4',
          'bg-sara-critical-soft',
          'flex items-center justify-center'
        )}
      >
        <AlertCircle
          className="w-8 h-8 text-sara-critical"
          aria-hidden="true"
        />
      </div>

      <h3 className="text-heading font-semibold text-sara-text-primary mb-2">
        {title}
      </h3>

      <p className="text-body text-sara-text-secondary mb-6 max-w-md">
        {message}
      </p>

      {onRetry && (
        <Button
          onClick={onRetry}
          variant="primary"
          leftIcon={<RefreshCw className="w-4 h-4" />}
          aria-label="Try again"
        >
          Try Again
        </Button>
      )}
    </div>
  );
}

export default ErrorState;
