'use client';

import { cn } from '@/lib/utils';
import { Stethoscope, Calendar, User as UserIcon } from 'lucide-react';

interface CodeableConcept {
  coding?: Array<{
    system?: string;
    code?: string;
    display?: string;
  }>;
  text?: string;
}

interface Reference {
  reference?: string;
  display?: string;
}

interface Performer {
  actor?: Reference;
  function?: CodeableConcept;
}

interface ProcedureData {
  resourceType: 'Procedure';
  id?: string;
  status?: string;
  code?: CodeableConcept;
  performedDateTime?: string;
  performedPeriod?: { start?: string; end?: string };
  performedString?: string;
  performer?: Performer[];
  category?: CodeableConcept;
  outcome?: CodeableConcept;
  [key: string]: unknown;
}

export interface ProcedureCardProps {
  data: ProcedureData;
  className?: string;
}

function getProcedureName(code?: CodeableConcept): string {
  if (!code) return 'Unknown Procedure';
  if (code.text) return code.text;
  if (code.coding?.[0]?.display) return code.coding[0].display;
  if (code.coding?.[0]?.code) return code.coding[0].code;
  return 'Unknown Procedure';
}

function getStatusBadge(status?: string) {
  if (!status) return null;

  const statusLower = status.toLowerCase();

  const statusMap: Record<string, { bg: string; text: string; label: string }> = {
    completed: { bg: 'bg-sara-accent-soft', text: 'text-sara-text-primary', label: 'Completed' },
    'in-progress': { bg: 'bg-sara-bg-elevated', text: 'text-sara-text-secondary', label: 'In Progress' },
    'not-done': { bg: 'bg-sara-bg-surface', text: 'text-sara-text-muted', label: 'Not Done' },
    'on-hold': { bg: 'bg-sara-bg-elevated', text: 'text-sara-text-muted', label: 'On Hold' },
    stopped: { bg: 'bg-sara-bg-surface', text: 'text-sara-text-muted', label: 'Stopped' },
    'entered-in-error': { bg: 'bg-sara-bg-surface', text: 'text-sara-text-muted', label: 'Error' },
    unknown: { bg: 'bg-sara-bg-surface', text: 'text-sara-text-muted', label: 'Unknown' },
    preparation: { bg: 'bg-sara-bg-elevated', text: 'text-sara-text-secondary', label: 'Preparation' },
  };

  const config = statusMap[statusLower] || { bg: 'bg-sara-bg-surface', text: 'text-sara-text-muted', label: status };

  return (
    <span className={cn('px-2 py-0.5 rounded-full text-caption font-medium', config.bg, config.text)}>
      {config.label}
    </span>
  );
}

function formatDate(dateString?: string): string {
  if (!dateString) return '';

  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function getPerformedDate(data: ProcedureData): string | undefined {
  if (data.performedDateTime) return data.performedDateTime;
  if (data.performedPeriod?.start) return data.performedPeriod.start;
  if (data.performedString) return data.performedString;
  return undefined;
}

function getPerformerName(performers?: Performer[]): string | undefined {
  if (!performers || performers.length === 0) return undefined;

  const performer = performers[0];
  return performer.actor?.display;
}

function getOutcome(outcome?: CodeableConcept): string | undefined {
  if (!outcome) return undefined;
  return outcome.text || outcome.coding?.[0]?.display;
}

function getCategory(category?: CodeableConcept): string | undefined {
  if (!category) return undefined;
  return category.text || category.coding?.[0]?.display;
}

export function ProcedureCard({ data, className }: ProcedureCardProps) {
  const name = getProcedureName(data.code);
  const performedDate = formatDate(getPerformedDate(data));
  const performer = getPerformerName(data.performer);
  const outcome = getOutcome(data.outcome);
  const category = getCategory(data.category);

  return (
    <div className={cn('rounded-sara bg-sara-bg-elevated border border-sara-border overflow-hidden', className)}>
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2">
            <div className="sara-icon-box">
              <Stethoscope className="w-[17px] h-[17px]" />
            </div>
            <h4 className="text-subheading text-sara-text-primary">
              {name}
            </h4>
          </div>
          {getStatusBadge(data.status)}
        </div>

        {/* Outcome if present */}
        {outcome && (
          <div className="ml-10 mb-2">
            <p className="text-body text-sara-text-secondary">
              Outcome: <span className="text-sara-text-primary">{outcome}</span>
            </p>
          </div>
        )}

        {/* Footer with details */}
        <div className="ml-10 flex flex-wrap items-center gap-4 text-body-small text-sara-text-muted">
          {category && (
            <span className="text-sara-text-secondary">{category}</span>
          )}
          {performer && (
            <div className="flex items-center gap-1">
              <UserIcon className="w-3 h-3" />
              <span>{performer}</span>
            </div>
          )}
          {performedDate && (
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              <span>{performedDate}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProcedureCard;
