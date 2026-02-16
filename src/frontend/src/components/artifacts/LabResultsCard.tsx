'use client';

import { cn } from '@/lib/utils';
import { FlaskConical, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { ExpandableSection } from '@/components/ui/ExpandableSection';

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

  const statusMap: Record<string, { bg: string; text: string; label: string }> = {
    final: { bg: 'bg-sara-accent-soft', text: 'text-sara-text-primary', label: 'Final' },
    preliminary: { bg: 'bg-sara-bg-elevated', text: 'text-sara-text-muted', label: 'Preliminary' },
    corrected: { bg: 'bg-sara-bg-elevated', text: 'text-sara-text-secondary', label: 'Corrected' },
    cancelled: { bg: 'bg-sara-bg-elevated', text: 'text-sara-text-muted', label: 'Cancelled' },
    'entered-in-error': { bg: 'bg-sara-bg-elevated', text: 'text-sara-text-muted', label: 'Error' },
  };

  const config = statusMap[statusLower] || { bg: 'bg-sara-bg-elevated', text: 'text-sara-text-muted', label: status };

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
    normal: 'border-sara-border bg-sara-bg-elevated',
    abnormal: 'border-sara-border bg-sara-bg-elevated',
    critical: 'border-sara-accent/30 bg-sara-accent-soft',
  };

  const statusLabels = {
    normal: 'Normal',
    abnormal: 'Abnormal',
    critical: 'Critical',
  };

  return (
    <div className={cn('rounded-sara bg-sara-bg-elevated border border-sara-border overflow-hidden', className)}>
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <div className="sara-icon-box">
              <FlaskConical className="w-[17px] h-[17px]" />
            </div>
            <h4 className="text-subheading text-sara-text-primary">
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
              <span className="text-display-lg font-medium text-sara-text-primary">
                {value}
              </span>
              <span className={cn(
                'px-2 py-0.5 rounded-full text-caption font-medium flex items-center gap-1',
                resultStatus === 'critical' ? 'bg-sara-accent-soft text-sara-text-primary' : 'bg-sara-bg-surface text-sara-text-muted'
              )}>
                {getTrendIcon(resultStatus)}
                <span>{statusLabels[resultStatus]}</span>
              </span>
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

        {/* Expandable: Interpretation Details */}
        {data.interpretation && data.interpretation.length > 0 && (
          <ExpandableSection title="Interpretation">
            <div className="space-y-2 pl-5">
              {data.interpretation.map((interp, index) => (
                <div key={index} className="text-body-small text-sara-text-secondary">
                  {interp.text || interp.coding?.[0]?.display || 'N/A'}
                </div>
              ))}
            </div>
          </ExpandableSection>
        )}

        {/* Expandable: Reference Ranges (if multiple) */}
        {data.referenceRange && data.referenceRange.length > 1 && (
          <ExpandableSection
            title="Reference Ranges"
            count={data.referenceRange.length}
          >
            <div className="space-y-2 pl-5">
              {data.referenceRange.map((range, index) => (
                <div key={index} className="text-body-small">
                  <span className="text-sara-text-muted">
                    {range.type?.text || `Range ${index + 1}`}:
                  </span>
                  <span className="text-sara-text-secondary ml-2">
                    {range.text || `${range.low?.value || '?'} - ${range.high?.value || '?'} ${range.low?.unit || ''}`}
                  </span>
                </div>
              ))}
            </div>
          </ExpandableSection>
        )}
      </div>
    </div>
  );
}

export default LabResultsCard;
