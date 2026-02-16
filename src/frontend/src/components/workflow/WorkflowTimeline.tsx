'use client';

import { cn } from '@/lib/utils';
import { Circle, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import type { WorkflowStep } from '@/lib/workflow';

export interface WorkflowTimelineProps {
  steps: WorkflowStep[];
  className?: string;
}

function StepIcon({ status }: { status: WorkflowStep['status'] }) {
  switch (status) {
    case 'complete':
      return <CheckCircle className="w-4 h-4 text-sara-text-primary" />;
    case 'running':
      return <Loader2 className="w-4 h-4 text-sara-text-secondary animate-spin" />;
    case 'error':
      return <AlertCircle className="w-4 h-4 text-sara-error" />;
    case 'pending':
    default:
      return <Circle className="w-4 h-4 text-sara-text-muted" />;
  }
}

function StepItem({ step, isLast }: { step: WorkflowStep; isLast: boolean }) {
  return (
    <div className="flex gap-3">
      {/* Timeline column */}
      <div className="flex flex-col items-center">
        <div
          className={cn(
            'w-6 h-6 rounded-full flex items-center justify-center',
            step.status === 'running' && 'bg-sara-accent-soft',
            step.status === 'complete' && 'bg-sara-accent-soft',
            step.status === 'error' && 'bg-sara-error-soft',
            step.status === 'pending' && 'bg-sara-bg-elevated'
          )}
        >
          <StepIcon status={step.status} />
        </div>
        {!isLast && (
          <div
            className={cn(
              'w-px flex-1 min-h-[16px] my-1',
              step.status === 'complete'
                ? 'bg-sara-text-muted'
                : 'bg-sara-border'
            )}
          />
        )}
      </div>

      {/* Content column */}
      <div className="flex-1 pb-3">
        <p
          className={cn(
            'text-body-small',
            step.status === 'running' && 'text-sara-text-primary font-medium',
            step.status === 'complete' && 'text-sara-text-secondary',
            step.status === 'error' && 'text-sara-error',
            step.status === 'pending' && 'text-sara-text-muted'
          )}
        >
          {step.description}
        </p>
      </div>
    </div>
  );
}

export function WorkflowTimeline({ steps, className }: WorkflowTimelineProps) {
  if (steps.length === 0) {
    return null;
  }

  return (
    <div
      className={cn(
        'rounded-sara bg-sara-bg-elevated border border-sara-border p-4',
        'animate-sara-fade-in',
        className
      )}
    >
      <h4 className="text-caption font-medium text-sara-text-muted uppercase tracking-wider mb-3">
        Progress
      </h4>
      <div>
        {steps.map((step, index) => (
          <StepItem
            key={step.id}
            step={step}
            isLast={index === steps.length - 1}
          />
        ))}
      </div>
    </div>
  );
}

export default WorkflowTimeline;
