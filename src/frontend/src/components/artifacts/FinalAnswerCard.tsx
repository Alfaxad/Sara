'use client';

import { cn } from '@/lib/utils';
import { CheckCircle, AlertCircle, Info } from 'lucide-react';

export interface FinalAnswerCardProps {
  taskId: string;
  answer: string;
  className?: string;
}

interface ParsedAnswer {
  type: 'value' | 'confirmation' | 'multi-step' | 'not-found';
  label: string;
  value: string;
  unit?: string;
  status?: 'success' | 'warning' | 'info';
  details?: string[];
}

function parseAnswer(taskId: string, answer: string): ParsedAnswer {
  const answerLower = answer.toLowerCase();

  // Patient Lookup (task1)
  if (taskId === 'task1') {
    if (answerLower.includes('not found') || answerLower.includes('no patient')) {
      // In demo context, patient should always exist - this indicates an issue
      return { type: 'not-found', label: 'Patient', value: 'Not found', status: 'warning' };
    }
    // Extract MRN - look for S followed by digits
    const mrnMatch = answer.match(/S\d+/);
    return {
      type: 'value',
      label: 'MRN',
      value: mrnMatch ? mrnMatch[0] : answer,
      status: 'success',
    };
  }

  // Patient Age (task2)
  if (taskId === 'task2') {
    const ageMatch = answer.match(/(\d+)/);
    return {
      type: 'value',
      label: 'Age',
      value: ageMatch ? ageMatch[1] : answer,
      unit: 'years',
      status: 'success',
    };
  }

  // Record Vitals (task3)
  if (taskId === 'task3') {
    return {
      type: 'confirmation',
      label: 'Blood Pressure',
      value: 'Recorded',
      status: 'success',
      details: ['Measurement saved to patient record'],
    };
  }

  // Lab Results (task4) - Magnesium
  if (taskId === 'task4') {
    const valueMatch = answer.match(/([\d.]+)/);
    if (valueMatch && valueMatch[1] === '-1') {
      return {
        type: 'not-found',
        label: 'Magnesium Level',
        value: 'No recent result',
        status: 'warning',
        details: ['No measurement within last 24 hours'],
      };
    }
    return {
      type: 'value',
      label: 'Magnesium Level',
      value: valueMatch ? valueMatch[1] : answer,
      unit: 'mg/dL',
      status: 'success',
    };
  }

  // Check & Order (task5)
  if (taskId === 'task5') {
    const details: string[] = [];
    if (answerLower.includes('order') || answerLower.includes('medication')) {
      details.push('Replacement medication ordered');
    }
    if (answerLower.includes('no order') || answerLower.includes('normal')) {
      return {
        type: 'value',
        label: 'Magnesium Status',
        value: 'Within normal range',
        status: 'success',
        details: ['No replacement needed'],
      };
    }
    return {
      type: 'multi-step',
      label: 'Magnesium Check',
      value: 'Completed',
      status: 'success',
      details,
    };
  }

  // Average CBG (task6)
  if (taskId === 'task6') {
    const valueMatch = answer.match(/([\d.]+)/);
    if (valueMatch && valueMatch[1] === '-1') {
      return {
        type: 'not-found',
        label: 'Average CBG',
        value: 'No recent readings',
        status: 'warning',
      };
    }
    return {
      type: 'value',
      label: 'Average CBG (24h)',
      value: valueMatch ? valueMatch[1] : answer,
      unit: 'mg/dL',
      status: 'success',
    };
  }

  // Recent CBG (task7)
  if (taskId === 'task7') {
    const valueMatch = answer.match(/([\d.]+)/);
    return {
      type: 'value',
      label: 'Most Recent CBG',
      value: valueMatch ? valueMatch[1] : answer,
      unit: 'mg/dL',
      status: 'success',
    };
  }

  // Order Referral (task8)
  if (taskId === 'task8') {
    return {
      type: 'confirmation',
      label: 'Orthopedic Referral',
      value: 'Created',
      status: 'success',
      details: ['Referral submitted for orthopedic evaluation'],
    };
  }

  // K+ Check & Order (task9)
  if (taskId === 'task9') {
    const details: string[] = [];
    if (answerLower.includes('potassium') || answerLower.includes('order')) {
      details.push('Potassium replacement ordered');
    }
    if (answerLower.includes('lab') || answerLower.includes('follow')) {
      details.push('Follow-up lab scheduled for 8am');
    }
    return {
      type: 'multi-step',
      label: 'Potassium Check',
      value: 'Completed',
      status: 'success',
      details,
    };
  }

  // HbA1C Check (task10)
  if (taskId === 'task10') {
    const details: string[] = [];
    if (answerLower.includes('order') || answerLower.includes('new test')) {
      details.push('New HbA1C test ordered');
    }
    const valueMatch = answer.match(/([\d.]+)%?/);
    if (valueMatch && valueMatch[1] === '-1') {
      return {
        type: 'not-found',
        label: 'HbA1C',
        value: 'No result found',
        status: 'warning',
        details: ['No HbA1C on record'],
      };
    }
    return {
      type: 'value',
      label: 'HbA1C',
      value: valueMatch ? valueMatch[1] : answer,
      unit: '%',
      status: 'success',
      details: details.length > 0 ? details : undefined,
    };
  }

  // Default fallback
  return {
    type: 'value',
    label: 'Result',
    value: answer,
    status: 'info',
  };
}

function StatusIcon({ status }: { status?: ParsedAnswer['status'] }) {
  switch (status) {
    case 'success':
      return <CheckCircle className="w-5 h-5 text-sara-success" />;
    case 'warning':
      return <AlertCircle className="w-5 h-5 text-sara-warning" />;
    case 'info':
    default:
      return <Info className="w-5 h-5 text-sara-info" />;
  }
}

export function FinalAnswerCard({ taskId, answer, className }: FinalAnswerCardProps) {
  const parsed = parseAnswer(taskId, answer);

  return (
    <div
      className={cn(
        'rounded-sara bg-sara-bg-elevated border border-sara-border overflow-hidden',
        'animate-sara-fade-in',
        className
      )}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-sara-border flex items-center gap-2">
        <StatusIcon status={parsed.status} />
        <span className="text-body-small font-medium text-sara-text-secondary">
          {parsed.type === 'confirmation' ? 'Action Complete' : 'Result'}
        </span>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="text-caption text-sara-text-muted uppercase tracking-wider mb-1">
          {parsed.label}
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-display-lg font-medium text-sara-text-primary">
            {parsed.value}
          </span>
          {parsed.unit && (
            <span className="text-body text-sara-text-secondary">
              {parsed.unit}
            </span>
          )}
        </div>

        {/* Details */}
        {parsed.details && parsed.details.length > 0 && (
          <div className="mt-3 pt-3 border-t border-sara-border">
            <ul className="space-y-1">
              {parsed.details.map((detail, index) => (
                <li
                  key={index}
                  className="text-body-small text-sara-text-secondary flex items-center gap-2"
                >
                  <span className="w-1 h-1 rounded-full bg-sara-text-muted" />
                  {detail}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default FinalAnswerCard;
