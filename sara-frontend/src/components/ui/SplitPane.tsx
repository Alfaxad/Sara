'use client';

import { useState, useCallback, useRef, useEffect, ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface SplitPaneProps {
  left: ReactNode;
  right: ReactNode;
  defaultLeftWidth?: number;
  minLeftWidth?: number;
  maxLeftWidth?: number;
  className?: string;
}

export function SplitPane({
  left,
  right,
  defaultLeftWidth = 50,
  minLeftWidth = 30,
  maxLeftWidth = 70,
  className,
}: SplitPaneProps) {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const newLeftWidth =
        ((e.clientX - containerRect.left) / containerRect.width) * 100;

      setLeftWidth(
        Math.min(maxLeftWidth, Math.max(minLeftWidth, newLeftWidth))
      );
    },
    [isDragging, minLeftWidth, maxLeftWidth]
  );

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <div
      ref={containerRef}
      className={cn(
        'flex h-full w-full',
        // Stack vertically on mobile
        'flex-col md:flex-row',
        className
      )}
    >
      {/* Left Pane */}
      <div
        className={cn(
          'flex-shrink-0 overflow-hidden',
          // Full width on mobile, percentage on desktop
          'h-1/2 md:h-full'
        )}
        style={{
          width: typeof window !== 'undefined' && window.innerWidth >= 768
            ? `${leftWidth}%`
            : '100%',
        }}
      >
        {left}
      </div>

      {/* Divider */}
      <div
        className={cn(
          'flex-shrink-0 bg-sara-border',
          'hover:bg-sara-accent transition-colors duration-150',
          // Horizontal divider on mobile, vertical on desktop
          'h-1 md:h-full md:w-1',
          'cursor-row-resize md:cursor-col-resize',
          isDragging && 'bg-sara-accent'
        )}
        onMouseDown={handleMouseDown}
      />

      {/* Right Pane */}
      <div className="flex-1 overflow-hidden h-1/2 md:h-full">
        {right}
      </div>
    </div>
  );
}

export default SplitPane;
