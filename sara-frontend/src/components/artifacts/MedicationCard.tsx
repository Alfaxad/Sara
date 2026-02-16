'use client';

import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Pill, Clock, User as UserIcon } from 'lucide-react';

interface CodeableConcept {
  coding?: Array<{
    system?: string;
    code?: string;
    display?: string;
  }>;
  text?: string;
}

interface Dosage {
  text?: string;
  timing?: {
    code?: CodeableConcept;
    repeat?: {
      frequency?: number;
      period?: number;
      periodUnit?: string;
    };
  };
  doseAndRate?: Array<{
    doseQuantity?: {
      value?: number;
      unit?: string;
    };
  }>;
  route?: CodeableConcept;
}

interface Reference {
  reference?: string;
  display?: string;
}

interface MedicationData {
  resourceType: 'MedicationRequest' | 'MedicationStatement' | 'Medication';
  id?: string;
  status?: string;
  medicationCodeableConcept?: CodeableConcept;
  medicationReference?: Reference;
  code?: CodeableConcept;
  dosageInstruction?: Dosage[];
  dosage?: Dosage[];
  authoredOn?: string;
  effectivePeriod?: { start?: string; end?: string };
  dateAsserted?: string;
  requester?: Reference;
  informationSource?: Reference;
  [key: string]: unknown;
}

export interface MedicationCardProps {
  data: MedicationData;
  className?: string;
}

function getMedicationName(data: MedicationData): string {
  // Try medicationCodeableConcept first
  if (data.medicationCodeableConcept) {
    if (data.medicationCodeableConcept.text) {
      return data.medicationCodeableConcept.text;
    }
    if (data.medicationCodeableConcept.coding?.[0]?.display) {
      return data.medicationCodeableConcept.coding[0].display;
    }
  }

  // Try medicationReference
  if (data.medicationReference?.display) {
    return data.medicationReference.display;
  }

  // For Medication resource type
  if (data.code) {
    if (data.code.text) return data.code.text;
    if (data.code.coding?.[0]?.display) return data.code.coding[0].display;
  }

  return 'Unknown Medication';
}

function formatDosage(dosages?: Dosage[]): string {
  if (!dosages || dosages.length === 0) return '';

  const dosage = dosages[0];

  if (dosage.text) return dosage.text;

  const parts: string[] = [];

  // Get dose
  if (dosage.doseAndRate?.[0]?.doseQuantity) {
    const dose = dosage.doseAndRate[0].doseQuantity;
    if (dose.value !== undefined) {
      parts.push(`${dose.value}${dose.unit || ''}`);
    }
  }

  // Get frequency
  if (dosage.timing?.code?.text) {
    parts.push(dosage.timing.code.text);
  } else if (dosage.timing?.code?.coding?.[0]?.display) {
    parts.push(dosage.timing.code.coding[0].display);
  } else if (dosage.timing?.repeat) {
    const repeat = dosage.timing.repeat;
    if (repeat.frequency && repeat.period && repeat.periodUnit) {
      parts.push(`${repeat.frequency}x per ${repeat.period} ${repeat.periodUnit}`);
    }
  }

  // Get route
  if (dosage.route) {
    const route = dosage.route.text || dosage.route.coding?.[0]?.display;
    if (route) parts.push(route);
  }

  return parts.join(' ');
}

function getStatusBadge(status?: string) {
  if (!status) return null;

  const statusLower = status.toLowerCase();

  const statusMap: Record<string, { variant: 'success' | 'warning' | 'critical' | 'info' | 'default'; label: string }> = {
    active: { variant: 'success', label: 'Active' },
    completed: { variant: 'default', label: 'Completed' },
    'entered-in-error': { variant: 'critical', label: 'Error' },
    stopped: { variant: 'warning', label: 'Stopped' },
    'on-hold': { variant: 'warning', label: 'On Hold' },
    cancelled: { variant: 'critical', label: 'Cancelled' },
    draft: { variant: 'info', label: 'Draft' },
    intended: { variant: 'info', label: 'Intended' },
  };

  const config = statusMap[statusLower] || { variant: 'default' as const, label: status };

  return <Badge variant={config.variant} size="sm">{config.label}</Badge>;
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

function getPrescriberName(data: MedicationData): string | undefined {
  if (data.requester?.display) {
    return data.requester.display;
  }
  if (data.informationSource?.display) {
    return data.informationSource.display;
  }
  return undefined;
}

function getDate(data: MedicationData): string | undefined {
  return data.authoredOn || data.dateAsserted || data.effectivePeriod?.start;
}

export function MedicationCard({ data, className }: MedicationCardProps) {
  const name = getMedicationName(data);
  const dosageStr = formatDosage(data.dosageInstruction || data.dosage);
  const prescriber = getPrescriberName(data);
  const date = formatDate(getDate(data));

  return (
    <Card variant="surface" className={cn('overflow-hidden', className)}>
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-sara-secondary-soft flex items-center justify-center flex-shrink-0">
              <Pill className="w-4 h-4 text-sara-secondary" />
            </div>
            <h4 className="text-subheading text-sara-text-primary font-semibold">
              {name}
            </h4>
          </div>
          {getStatusBadge(data.status)}
        </div>

        {/* Dosage */}
        {dosageStr && (
          <div className="ml-10 mb-3">
            <p className="text-body text-sara-text-secondary">
              {dosageStr}
            </p>
          </div>
        )}

        {/* Footer with prescriber and date */}
        <div className="ml-10 flex items-center gap-4 text-body-small text-sara-text-muted">
          {prescriber && (
            <div className="flex items-center gap-1">
              <UserIcon className="w-3 h-3" />
              <span>{prescriber}</span>
            </div>
          )}
          {date && (
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{date}</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

export default MedicationCard;
