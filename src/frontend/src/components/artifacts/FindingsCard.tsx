'use client';

import { cn } from '@/lib/utils';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  Info,
  Sparkles,
} from 'lucide-react';

export interface Finding {
  id?: string;
  text: string;
  severity?: 'critical' | 'warning' | 'normal' | 'info';
  source?: string;
  value?: string;
  reference?: string;
}

export interface FindingsCardProps {
  findings: Finding[];
  title?: string;
  className?: string;
}

function getSeverityConfig(severity?: Finding['severity']) {
  switch (severity) {
    case 'critical':
      return {
        icon: AlertCircle,
        bgColor: 'bg-sara-accent-soft',
        textColor: 'text-sara-text-primary',
        borderColor: 'border-sara-accent/30',
        dotColor: 'bg-sara-accent',
      };
    case 'warning':
      return {
        icon: AlertTriangle,
        bgColor: 'bg-sara-bg-elevated',
        textColor: 'text-sara-text-secondary',
        borderColor: 'border-sara-border',
        dotColor: 'bg-sara-text-secondary',
      };
    case 'normal':
      return {
        icon: CheckCircle,
        bgColor: 'bg-sara-bg-surface',
        textColor: 'text-sara-text-muted',
        borderColor: 'border-sara-border',
        dotColor: 'bg-sara-text-muted',
      };
    case 'info':
    default:
      return {
        icon: Info,
        bgColor: 'bg-sara-bg-elevated',
        textColor: 'text-sara-text-secondary',
        borderColor: 'border-sara-border',
        dotColor: 'bg-sara-text-secondary',
      };
  }
}

function FindingItem({ finding }: { finding: Finding }) {
  const config = getSeverityConfig(finding.severity);
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-3 rounded-sara-sm border',
        config.bgColor,
        config.borderColor
      )}
    >
      <Icon className={cn('w-4 h-4 flex-shrink-0 mt-0.5', config.textColor)} />
      <div className="flex-1 min-w-0">
        <p className={cn('text-body font-medium', config.textColor)}>
          {finding.text}
        </p>
        {(finding.value || finding.reference) && (
          <div className="flex items-center gap-2 mt-1 text-body-small">
            {finding.value && (
              <span className="text-sara-text-primary font-semibold">
                {finding.value}
              </span>
            )}
            {finding.reference && (
              <span className="text-sara-text-muted">
                (Ref: {finding.reference})
              </span>
            )}
          </div>
        )}
        {finding.source && (
          <p className="text-caption text-sara-text-muted mt-1">
            Source: {finding.source}
          </p>
        )}
      </div>
    </div>
  );
}

export function FindingsCard({
  findings,
  title = 'Key Findings',
  className,
}: FindingsCardProps) {
  if (findings.length === 0) {
    return null;
  }

  // Sort findings by severity: critical > warning > info > normal
  const sortedFindings = [...findings].sort((a, b) => {
    const severityOrder = { critical: 0, warning: 1, info: 2, normal: 3 };
    const aOrder = severityOrder[a.severity || 'info'];
    const bOrder = severityOrder[b.severity || 'info'];
    return aOrder - bOrder;
  });

  // Count by severity
  const criticalCount = findings.filter((f) => f.severity === 'critical').length;
  const warningCount = findings.filter((f) => f.severity === 'warning').length;

  return (
    <div className={cn('rounded-sara bg-sara-bg-elevated border border-sara-border overflow-hidden', className)}>
      <div className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2">
            <div className="sara-icon-box">
              <Sparkles className="w-[17px] h-[17px]" />
            </div>
            <h4 className="text-subheading text-sara-text-primary">
              {title}
            </h4>
          </div>
          <div className="flex items-center gap-2 text-caption">
            {criticalCount > 0 && (
              <span className="flex items-center gap-1 text-sara-text-primary">
                <span className="w-2 h-2 rounded-full bg-sara-accent" />
                {criticalCount}
              </span>
            )}
            {warningCount > 0 && (
              <span className="flex items-center gap-1 text-sara-text-secondary">
                <span className="w-2 h-2 rounded-full bg-sara-text-secondary" />
                {warningCount}
              </span>
            )}
          </div>
        </div>

        {/* Findings List */}
        <div className="space-y-2">
          {sortedFindings.map((finding, index) => (
            <FindingItem key={finding.id || index} finding={finding} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default FindingsCard;
