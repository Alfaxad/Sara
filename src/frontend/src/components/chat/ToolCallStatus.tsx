'use client';

import { cn } from '@/lib/utils';
import { Check, Loader2, AlertCircle } from 'lucide-react';

export interface ToolCallStatusProps {
  tool: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  className?: string;
}

export function ToolCallStatus({ tool, status, className }: ToolCallStatusProps) {
  // Display the actual FHIR endpoint being called
  const displayName = tool.includes('/fhir/') ? tool : `FHIR ${tool}`;

  return (
    <div
      className={cn(
        'flex items-center gap-2.5 px-3 py-2',
        'animate-msg-in',
        className
      )}
    >
      {status === 'running' && (
        <Loader2 className="w-3.5 h-3.5 text-sara-text-muted sara-spin" />
      )}
      {status === 'complete' && (
        <Check className="w-3.5 h-3.5 text-sara-success" />
      )}
      {status === 'error' && (
        <AlertCircle className="w-3.5 h-3.5 text-sara-error" />
      )}
      {status === 'pending' && (
        <div className="w-3.5 h-3.5 rounded-full border border-sara-text-muted border-t-transparent sara-spin" />
      )}

      <span
        className={cn(
          'text-body-small font-mono',
          status === 'running' && 'text-sara-text-muted',
          status === 'complete' && 'text-sara-text-secondary',
          status === 'error' && 'text-sara-error',
          status === 'pending' && 'text-sara-text-muted'
        )}
      >
        {displayName}
      </span>

      {status === 'complete' && (
        <span className="text-body-small text-sara-success">✓</span>
      )}
    </div>
  );
}

export default ToolCallStatus;
