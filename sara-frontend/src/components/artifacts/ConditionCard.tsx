'use client';

import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
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

function getClinicalStatus(status?: CodeableConcept): { label: string; variant: 'success' | 'warning' | 'critical' | 'info' | 'default' } {
  if (!status) return { label: 'Unknown', variant: 'default' };

  const code = status.coding?.[0]?.code?.toLowerCase() || status.text?.toLowerCase();

  switch (code) {
    case 'active':
      return { label: 'Active', variant: 'warning' };
    case 'recurrence':
      return { label: 'Recurrence', variant: 'critical' };
    case 'relapse':
      return { label: 'Relapse', variant: 'critical' };
    case 'inactive':
      return { label: 'Inactive', variant: 'default' };
    case 'remission':
      return { label: 'Remission', variant: 'success' };
    case 'resolved':
      return { label: 'Resolved', variant: 'success' };
    default:
      return { label: status.text || code || 'Unknown', variant: 'default' };
  }
}

function getSeverity(severity?: CodeableConcept): { label: string; variant: 'success' | 'warning' | 'critical' } | null {
  if (!severity) return null;

  const code = severity.coding?.[0]?.code?.toLowerCase() || severity.text?.toLowerCase();

  switch (code) {
    case 'severe':
      return { label: 'Severe', variant: 'critical' };
    case 'moderate':
      return { label: 'Moderate', variant: 'warning' };
    case 'mild':
      return { label: 'Mild', variant: 'success' };
    default:
      if (severity.text) {
        return { label: severity.text, variant: 'warning' };
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

  const isActive = clinicalStatus.label.toLowerCase() === 'active' ||
                   clinicalStatus.label.toLowerCase() === 'recurrence' ||
                   clinicalStatus.label.toLowerCase() === 'relapse';

  return (
    <Card variant="surface" className={cn('overflow-hidden', className)}>
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2">
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                isActive ? 'bg-sara-warning-soft' : 'bg-sara-bg-subtle'
              )}
            >
              <HeartPulse
                className={cn(
                  'w-4 h-4',
                  isActive ? 'text-sara-warning' : 'text-sara-text-muted'
                )}
              />
            </div>
            <h4 className="text-subheading text-sara-text-primary font-semibold">
              {name}
            </h4>
          </div>
          <div className="flex items-center gap-2">
            {severity && (
              <Badge variant={severity.variant} size="sm">
                <AlertTriangle className="w-3 h-3 mr-1" />
                {severity.label}
              </Badge>
            )}
            <Badge variant={clinicalStatus.variant} size="sm">
              {clinicalStatus.label}
            </Badge>
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
    </Card>
  );
}

export default ConditionCard;
