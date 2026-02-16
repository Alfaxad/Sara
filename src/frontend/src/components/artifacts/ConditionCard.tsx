'use client';

import { cn } from '@/lib/utils';
import { HeartPulse, Calendar, AlertTriangle } from 'lucide-react';

interface CodeableConcept {
  coding?: Array<{
    system?: string;
    code?: string;
    display?: string;
  }>;
  text?: string;
}

interface ConditionData {
  resourceType: 'Condition';
  id?: string;
  clinicalStatus?: CodeableConcept;
  verificationStatus?: CodeableConcept;
  category?: CodeableConcept[];
  severity?: CodeableConcept;
  code?: CodeableConcept;
  onsetDateTime?: string;
  onsetPeriod?: { start?: string; end?: string };
  onsetString?: string;
  abatementDateTime?: string;
  recordedDate?: string;
  [key: string]: unknown;
}

export interface ConditionCardProps {
  data: ConditionData;
  className?: string;
}

function getConditionName(code?: CodeableConcept): string {
  if (!code) return 'Unknown Condition';
  if (code.text) return code.text;
  if (code.coding?.[0]?.display) return code.coding[0].display;
  if (code.coding?.[0]?.code) return code.coding[0].code;
  return 'Unknown Condition';
}

function getClinicalStatus(status?: CodeableConcept): { label: string; bg: string; text: string } {
  if (!status) return { label: 'Unknown', bg: 'bg-sara-bg-elevated', text: 'text-sara-text-muted' };

  const code = status.coding?.[0]?.code?.toLowerCase() || status.text?.toLowerCase();

  switch (code) {
    case 'active':
      return { label: 'Active', bg: 'bg-sara-accent-soft', text: 'text-sara-text-primary' };
    case 'recurrence':
    case 'relapse':
      return { label: code.charAt(0).toUpperCase() + code.slice(1), bg: 'bg-sara-accent-soft', text: 'text-sara-text-primary' };
    case 'inactive':
      return { label: 'Inactive', bg: 'bg-sara-bg-surface', text: 'text-sara-text-muted' };
    case 'remission':
    case 'resolved':
      return { label: code.charAt(0).toUpperCase() + code.slice(1), bg: 'bg-sara-bg-surface', text: 'text-sara-text-muted' };
    default:
      return { label: status.text || code || 'Unknown', bg: 'bg-sara-bg-elevated', text: 'text-sara-text-muted' };
  }
}

function getSeverity(severity?: CodeableConcept): { label: string; bg: string; text: string } | null {
  if (!severity) return null;

  const code = severity.coding?.[0]?.code?.toLowerCase() || severity.text?.toLowerCase();

  switch (code) {
    case 'severe':
      return { label: 'Severe', bg: 'bg-sara-accent-soft', text: 'text-sara-text-primary' };
    case 'moderate':
      return { label: 'Moderate', bg: 'bg-sara-bg-elevated', text: 'text-sara-text-secondary' };
    case 'mild':
      return { label: 'Mild', bg: 'bg-sara-bg-surface', text: 'text-sara-text-muted' };
    default:
      if (severity.text) {
        return { label: severity.text, bg: 'bg-sara-bg-elevated', text: 'text-sara-text-secondary' };
      }
      return null;
  }
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

function getOnsetDate(data: ConditionData): string | undefined {
  if (data.onsetDateTime) return data.onsetDateTime;
  if (data.onsetPeriod?.start) return data.onsetPeriod.start;
  if (data.onsetString) return data.onsetString;
  return undefined;
}

function getCategory(categories?: CodeableConcept[]): string | undefined {
  if (!categories || categories.length === 0) return undefined;

  const category = categories[0];
  return category.text || category.coding?.[0]?.display;
}

export function ConditionCard({ data, className }: ConditionCardProps) {
  const name = getConditionName(data.code);
  const clinicalStatus = getClinicalStatus(data.clinicalStatus);
  const severity = getSeverity(data.severity);
  const onsetDate = formatDate(getOnsetDate(data));
  const category = getCategory(data.category);

  return (
    <div className={cn('rounded-sara bg-sara-bg-elevated border border-sara-border overflow-hidden', className)}>
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2">
            <div className="sara-icon-box">
              <HeartPulse className="w-[17px] h-[17px]" />
            </div>
            <h4 className="text-subheading text-sara-text-primary">
              {name}
            </h4>
          </div>
          <div className="flex items-center gap-2">
            {severity && (
              <span className={cn('px-2 py-0.5 rounded-full text-caption font-medium flex items-center gap-1', severity.bg, severity.text)}>
                <AlertTriangle className="w-3 h-3" />
                {severity.label}
              </span>
            )}
            <span className={cn('px-2 py-0.5 rounded-full text-caption font-medium', clinicalStatus.bg, clinicalStatus.text)}>
              {clinicalStatus.label}
            </span>
          </div>
        </div>

        {/* Details */}
        <div className="ml-10 flex items-center gap-4 text-body-small text-sara-text-muted">
          {category && (
            <span className="text-sara-text-secondary">{category}</span>
          )}
          {onsetDate && (
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              <span>Onset: {onsetDate}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ConditionCard;
