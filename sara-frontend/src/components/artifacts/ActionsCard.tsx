'use client';

import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import {
  CheckCircle,
  Clock,
  Circle,
  AlertCircle,
  ArrowRight,
  Zap,
} from 'lucide-react';

export interface Action {
  id?: string;
  text: string;
  status?: 'completed' | 'pending' | 'in-progress' | 'suggested' | 'failed';
  timestamp?: string;
  description?: string;
}

export interface ActionsCardProps {
  actions: Action[];
  title?: string;
  className?: string;
}

function getStatusConfig(status?: Action['status']) {
  switch (status) {
    case 'completed':
      return {
        icon: CheckCircle,
        textColor: 'text-sara-success',
        bgColor: 'bg-sara-success-soft',
        label: 'Completed',
      };
    case 'in-progress':
      return {
        icon: Clock,
        textColor: 'text-sara-info',
        bgColor: 'bg-sara-info-soft',
        label: 'In Progress',
      };
    case 'failed':
      return {
        icon: AlertCircle,
        textColor: 'text-sara-critical',
        bgColor: 'bg-sara-critical-soft',
        label: 'Failed',
      };
    case 'suggested':
      return {
        icon: ArrowRight,
        textColor: 'text-sara-accent',
        bgColor: 'bg-sara-accent-soft',
        label: 'Suggested',
      };
    case 'pending':
    default:
      return {
        icon: Circle,
        textColor: 'text-sara-text-muted',
        bgColor: 'bg-sara-bg-subtle',
        label: 'Pending',
      };
  }
}

function formatTimestamp(timestamp?: string): string {
  if (!timestamp) return '';

  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

function ActionItem({ action }: { action: Action }) {
  const config = getStatusConfig(action.status);
  const Icon = config.icon;

  return (
    <div className="flex items-start gap-3 py-2">
      <div
        className={cn(
          'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0',
          config.bgColor
        )}
      >
        <Icon className={cn('w-3.5 h-3.5', config.textColor)} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <p
            className={cn(
              'text-body',
              action.status === 'completed'
                ? 'text-sara-text-secondary'
                : 'text-sara-text-primary'
            )}
          >
            {action.text}
          </p>
          {action.timestamp && (
            <span className="text-caption text-sara-text-muted flex-shrink-0">
              {formatTimestamp(action.timestamp)}
            </span>
          )}
        </div>
        {action.description && (
          <p className="text-body-small text-sara-text-muted mt-0.5">
            {action.description}
          </p>
        )}
      </div>
    </div>
  );
}

export function ActionsCard({
  actions,
  title = 'Actions',
  className,
}: ActionsCardProps) {
  if (actions.length === 0) {
    return null;
  }

  // Separate completed and pending/suggested actions
  const completedActions = actions.filter((a) => a.status === 'completed');
  const pendingActions = actions.filter((a) => a.status !== 'completed');

  // Count summaries
  const completedCount = completedActions.length;
  const pendingCount = pendingActions.length;

  return (
    <Card variant="surface" className={cn('overflow-hidden', className)}>
      <div className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-sara-accent" />
            <h4 className="text-subheading text-sara-text-primary font-semibold">
              {title}
            </h4>
          </div>
          <div className="flex items-center gap-3 text-caption">
            {completedCount > 0 && (
              <span className="flex items-center gap-1 text-sara-success">
                <CheckCircle className="w-3 h-3" />
                {completedCount} done
              </span>
            )}
            {pendingCount > 0 && (
              <span className="flex items-center gap-1 text-sara-text-muted">
                <Clock className="w-3 h-3" />
                {pendingCount} pending
              </span>
            )}
          </div>
        </div>

        {/* Actions List */}
        <div className="divide-y divide-sara-border">
          {/* Completed actions first */}
          {completedActions.map((action, index) => (
            <ActionItem key={action.id || `completed-${index}`} action={action} />
          ))}

          {/* Then pending/suggested */}
          {pendingActions.map((action, index) => (
            <ActionItem key={action.id || `pending-${index}`} action={action} />
          ))}
        </div>
      </div>
    </Card>
  );
}

export default ActionsCard;
