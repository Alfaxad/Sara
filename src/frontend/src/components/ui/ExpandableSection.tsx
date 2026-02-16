'use client';

import { useState, ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight } from 'lucide-react';

export interface ExpandableSectionProps {
  title: string;
  count?: number;
  defaultExpanded?: boolean;
  children: ReactNode;
  className?: string;
}

export function ExpandableSection({
  title,
  count,
  defaultExpanded = false,
  children,
  className,
}: ExpandableSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className={cn('border-t border-sara-border', className)}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          'w-full py-2.5 flex items-center gap-2',
          'text-body-small text-sara-text-secondary',
          'hover:text-sara-text-primary transition-colors duration-150'
        )}
        aria-expanded={isExpanded}
      >
        <span
          className={cn(
            'transition-transform duration-200',
            isExpanded && 'rotate-90'
          )}
        >
          <ChevronRight className="w-3.5 h-3.5" />
        </span>
        <span>{title}</span>
        {count !== undefined && count > 0 && (
          <span className="text-sara-text-muted">({count})</span>
        )}
      </button>
      {isExpanded && (
        <div className="pb-3 animate-sara-fade-in">
          {children}
        </div>
      )}
    </div>
  );
}

export default ExpandableSection;
