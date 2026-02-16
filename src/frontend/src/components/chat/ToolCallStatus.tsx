'use client';

import { cn } from '@/lib/utils';
import { Check, Loader2, AlertCircle } from 'lucide-react';

export interface ToolCallStatusProps {
  tool: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  className?: string;
}

const toolDisplayNames: Record<string, string> = {
  get_patient: 'Fetching patient data',
  search_patients: 'Searching patients',
  get_medications: 'Retrieving medications',
  get_allergies: 'Checking allergies',
  get_conditions: 'Loading conditions',
  get_observations: 'Fetching observations',
  get_lab_results: 'Retrieving lab results',
  create_medication_request: 'Creating prescription',
  create_service_request: 'Creating order',
  create_observation: 'Recording observation',
  calculate_dose: 'Calculating dosage',
  default: 'Processing',
};

function getToolDisplayName(tool: string): string {
  return toolDisplayNames[tool] || toolDisplayNames.default;
}

export function ToolCallStatus({ tool, status, className }: ToolCallStatusProps) {
  const displayName = getToolDisplayName(tool);

  return (
    <div
      className={cn(
        'flex items-center gap-3 px-4 py-3 rounded-sara-sm',
        'bg-sara-bg-subtle border border-sara-border',
        'animate-sara-fade-in',
        className
      )}
    >
      {status === 'running' && (
        <Loader2 className="w-4 h-4 text-sara-info animate-sara-spin" />
      )}
      {status === 'complete' && (
        <Check className="w-4 h-4 text-sara-success" />
      )}
      {status === 'error' && (
        <AlertCircle className="w-4 h-4 text-sara-critical" />
      )}
      {status === 'pending' && (
        <div className="w-4 h-4 rounded-full border-2 border-sara-text-muted border-t-transparent animate-sara-spin" />
      )}

      <span
        className={cn(
          'text-body-small',
          status === 'running' && 'text-sara-text-secondary',
          status === 'complete' && 'text-sara-success',
          status === 'error' && 'text-sara-critical',
          status === 'pending' && 'text-sara-text-muted'
        )}
      >
        {status === 'running' && `${displayName}...`}
        {status === 'complete' && `${displayName} - Done`}
        {status === 'error' && `${displayName} - Failed`}
        {status === 'pending' && `${displayName} - Waiting`}
      </span>
    </div>
  );
}

export default ToolCallStatus;
