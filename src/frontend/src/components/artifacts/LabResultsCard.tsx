'use client';

import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { FlaskConical, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface CodeableConcept {
  coding?: Array<{
    system?: string;
    code?: string;
    display?: string;
  }>;
  text?: string;
}

interface Quantity {
  value?: number;
  unit?: string;
  system?: string;
  code?: string;
}

interface ReferenceRange {
  low?: Quantity;
  high?: Quantity;
  text?: string;
  type?: CodeableConcept;
}

interface ObservationData {
  resourceType: 'Observation';
  id?: string;
  status?: string;
  code?: CodeableConcept;
  valueQuantity?: Quantity;
  valueString?: string;
  valueCodeableConcept?: CodeableConcept;
  effectiveDateTime?: string;
  effectivePeriod?: { start?: string; end?: string };
  issued?: string;
  referenceRange?: ReferenceRange[];
  interpretation?: CodeableConcept[];
  [key: string]: unknown;
}

export interface LabResultsCardProps {
  data: ObservationData;
  className?: string;
}

type ResultStatus = 'normal' | 'abnormal' | 'critical';

function getLabName(code?: CodeableConcept): string {
  if (!code) return 'Unknown Lab';
  if (code.text) return code.text;
  if (code.coding?.[0]?.display) return code.coding[0].display;
  if (code.coding?.[0]?.code) return code.coding[0].code;
  return 'Unknown Lab';
}

function formatValue(data: ObservationData): string {
  if (data.valueQuantity) {
    const value = data.valueQuantity.value;
    const unit = data.valueQuantity.unit || data.valueQuantity.code || '';
    return value !== undefined ? `${value} ${unit}`.trim() : 'N/A';
  }
  if (data.valueString) {
    return data.valueString;
  }
  if (data.valueCodeableConcept) {
    return data.valueCodeableConcept.text || data.valueCodeableConcept.coding?.[0]?.display || 'N/A';
  }
  return 'N/A';
}

function formatReferenceRange(ranges?: ReferenceRange[]): string {
  if (!ranges || ranges.length === 0) return '';

  const range = ranges[0];

  if (range.text) return range.text;

  const parts: string[] = [];
  if (range.low?.value !== undefined) {
    parts.push(`${range.low.value}`);
  }
  if (range.high?.value !== undefined) {
    if (parts.length === 0) {
      parts.push(`< ${range.high.value}`);
    } else {
      parts.push(`${range.high.value}`);
    }
  }

  if (parts.length === 2) {
    const unit = range.low?.unit || range.high?.unit || '';
    return `${parts[0]} - ${parts[1]} ${unit}`.trim();
  }
  if (parts.length === 1) {
    return parts[0];
  }

  return '';
}

function getResultStatus(data: ObservationData): ResultStatus {
  // Check interpretation first
  if (data.interpretation && data.interpretation.length > 0) {
    const interp = data.interpretation[0];
    const code = interp.coding?.[0]?.code?.toUpperCase();
    const text = interp.text?.toLowerCase();

    // Critical values
    if (code === 'AA' || code === 'HH' || code === 'LL' || code === 'POS') {
      return 'critical';
    }
    if (text?.includes('critical')) {
      return 'critical';
    }

    // Abnormal values
    if (code === 'A' || code === 'H' || code === 'L') {
      return 'abnormal';
    }
    if (text?.includes('abnormal') || text?.includes('high') || text?.includes('low')) {
      return 'abnormal';
    }

    // Normal
    if (code === 'N') {
      return 'normal';
    }
  }

  // Check against reference range
  if (data.valueQuantity?.value !== undefined && data.referenceRange?.length) {
    const value = data.valueQuantity.value;
    const range = data.referenceRange[0];

    if (range.low?.value !== undefined && value < range.low.value) {
      return 'abnormal';
    }
    if (range.high?.value !== undefined && value > range.high.value) {
      return 'abnormal';
    }

    return 'normal';
  }

  return 'normal'; // Default to normal if we can't determine
}

function getStatusBadge(status?: string) {
  if (!status) return null;

  const statusLower = status.toLowerCase();

  if (statusLower === 'final') {
    return <Badge variant="success" size="sm">Final</Badge>;
  }
  if (statusLower === 'preliminary') {
    return <Badge variant="warning" size="sm">Preliminary</Badge>;
  }
  if (statusLower === 'corrected') {
    return <Badge variant="info" size="sm">Corrected</Badge>;
  }
  if (statusLower === 'cancelled' || statusLower === 'entered-in-error') {
    return <Badge variant="critical" size="sm">{status}</Badge>;
  }

  return <Badge variant="default" size="sm">{status}</Badge>;
}

function formatDate(dateString?: string): string {
  if (!dateString) return '';

  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getTrendIcon(status: ResultStatus) {
  switch (status) {
    case 'critical':
      return <TrendingUp className="w-4 h-4" />;
    case 'abnormal':
      return <TrendingDown className="w-4 h-4" />;
    default:
      return <Minus className="w-4 h-4" />;
  }
}

export function LabResultsCard({ data, className }: LabResultsCardProps) {
  const labName = getLabName(data.code);
  const value = formatValue(data);
  const referenceRange = formatReferenceRange(data.referenceRange);
  const resultStatus = getResultStatus(data);
  const date = formatDate(data.effectiveDateTime || data.issued);

  const statusColors = {
    normal: 'text-sara-success border-sara-success/30 bg-sara-success-soft',
    abnormal: 'text-sara-warning border-sara-warning/30 bg-sara-warning-soft',
    critical: 'text-sara-critical border-sara-critical/30 bg-sara-critical-soft',
  };

  const statusLabels = {
    normal: 'Normal',
    abnormal: 'Abnormal',
    critical: 'Critical',
  };

  return (
    <Card variant="surface" className={cn('overflow-hidden', className)}>
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-sara-accent flex-shrink-0" />
            <h4 className="text-subheading text-sara-text-primary font-semibold">
              {labName}
            </h4>
          </div>
          {getStatusBadge(data.status)}
        </div>

        {/* Value Display */}
        <div
          className={cn(
            'p-3 rounded-sara-sm border mb-3',
            statusColors[resultStatus]
          )}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-baseline gap-2">
              <span className="text-display-lg font-bold">
                {value}
              </span>
              <Badge
                variant={
                  resultStatus === 'normal'
                    ? 'success'
                    : resultStatus === 'abnormal'
                    ? 'warning'
                    : 'critical'
                }
                size="sm"
              >
                {getTrendIcon(resultStatus)}
                <span className="ml-1">{statusLabels[resultStatus]}</span>
              </Badge>
            </div>
          </div>
        </div>

        {/* Reference Range & Date */}
        <div className="flex items-center justify-between text-body-small text-sara-text-secondary">
          {referenceRange && (
            <span>
              Ref: <span className="text-sara-text-muted">{referenceRange}</span>
            </span>
          )}
          {date && (
            <span className="text-sara-text-muted">{date}</span>
          )}
        </div>
      </div>
    </Card>
  );
}

export default LabResultsCard;
