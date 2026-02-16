'use client';

import { useState, useCallback, useMemo } from 'react';
import { cn } from '@/lib/utils';
import {
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
  Code,
  FileJson,
} from 'lucide-react';

export interface SourceViewerProps {
  data: unknown;
  title?: string;
  defaultExpanded?: boolean;
  className?: string;
}

interface JsonToken {
  type: 'key' | 'string' | 'number' | 'boolean' | 'null' | 'punctuation';
  value: string;
}

function tokenizeJson(json: string): JsonToken[] {
  const tokens: JsonToken[] = [];
  const regex = /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|[{}\[\]:,]|\s+)/g;

  let match;
  while ((match = regex.exec(json)) !== null) {
    const value = match[0];

    if (/^\s+$/.test(value)) {
      // Whitespace - keep as punctuation
      tokens.push({ type: 'punctuation', value });
    } else if (/^"/.test(value)) {
      if (/:$/.test(value)) {
        tokens.push({ type: 'key', value });
      } else {
        tokens.push({ type: 'string', value });
      }
    } else if (/true|false/.test(value)) {
      tokens.push({ type: 'boolean', value });
    } else if (/null/.test(value)) {
      tokens.push({ type: 'null', value });
    } else if (/^-?\d/.test(value)) {
      tokens.push({ type: 'number', value });
    } else {
      tokens.push({ type: 'punctuation', value });
    }
  }

  return tokens;
}

function TokenSpan({ token }: { token: JsonToken }) {
  const colorClass = {
    key: 'text-sara-text-primary',
    string: 'text-sara-text-secondary',
    number: 'text-sara-text-secondary',
    boolean: 'text-sara-text-muted',
    null: 'text-sara-text-muted',
    punctuation: 'text-sara-text-muted',
  }[token.type];

  return <span className={colorClass}>{token.value}</span>;
}

export function SourceViewer({
  data,
  title = 'Source',
  defaultExpanded = false,
  className,
}: SourceViewerProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [copied, setCopied] = useState(false);

  const jsonString = useMemo(() => JSON.stringify(data, null, 2), [data]);
  const tokens = useMemo(() => tokenizeJson(jsonString), [jsonString]);

  const copyToClipboard = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, [jsonString]);

  // Calculate line count for display
  const lineCount = jsonString.split('\n').length;

  return (
    <div
      className={cn('overflow-hidden bg-sara-bg-base rounded-sara border border-sara-border', className)}
    >
      {/* Header - always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          'w-full px-4 py-3 flex items-center justify-between gap-2',
          'text-body-small text-sara-text-secondary',
          'hover:bg-sara-bg-elevated transition-colors duration-150'
        )}
      >
        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
          <FileJson className="w-4 h-4 text-sara-text-primary" />
          <span className="font-medium">{title}</span>
          <span className="text-sara-text-muted text-caption">
            ({lineCount} lines)
          </span>
        </div>
        <Code className="w-4 h-4 text-sara-text-muted" />
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-sara-border animate-sara-fade-in">
          {/* Toolbar */}
          <div className="px-4 py-2 flex items-center justify-end border-b border-sara-border bg-sara-bg-surface">
            <button
              onClick={(e) => {
                e.stopPropagation();
                copyToClipboard();
              }}
              className={cn(
                'flex items-center gap-1.5 px-2 py-1 rounded-sara-sm',
                'text-caption text-sara-text-secondary',
                'hover:bg-sara-bg-elevated transition-colors duration-150',
                copied && 'text-sara-text-primary'
              )}
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>

          {/* JSON Content */}
          <div className="p-4 overflow-x-auto">
            <pre className="font-mono text-caption leading-relaxed whitespace-pre">
              {tokens.map((token, index) => (
                <TokenSpan key={index} token={token} />
              ))}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default SourceViewer;
