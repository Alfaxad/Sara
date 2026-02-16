'use client';

import { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import { Brain, CheckCircle, ArrowRight } from 'lucide-react';

export interface ReasoningPanelProps {
  reasoning: string;
  className?: string;
}

interface ReasoningStep {
  number: number;
  content: string;
  isConclusion?: boolean;
}

function parseReasoning(reasoning: string): ReasoningStep[] {
  // Try to detect if reasoning is structured
  const lines = reasoning.split('\n').filter((line) => line.trim());

  // Check for numbered steps (1., 2., etc.)
  const numberedPattern = /^(\d+)\.\s+(.+)$/;
  const isNumbered = lines.some((line) => numberedPattern.test(line.trim()));

  if (isNumbered) {
    const steps: ReasoningStep[] = [];
    let currentStep: ReasoningStep | null = null;

    for (const line of lines) {
      const match = line.trim().match(numberedPattern);
      if (match) {
        if (currentStep) {
          steps.push(currentStep);
        }
        currentStep = {
          number: parseInt(match[1], 10),
          content: match[2],
        };
      } else if (currentStep) {
        currentStep.content += ' ' + line.trim();
      }
    }

    if (currentStep) {
      steps.push(currentStep);
    }

    // Mark the last step as conclusion if it looks like one
    if (steps.length > 0) {
      const lastStep = steps[steps.length - 1];
      const conclusionKeywords = ['therefore', 'thus', 'conclusion', 'result', 'answer', 'final'];
      if (conclusionKeywords.some((kw) => lastStep.content.toLowerCase().includes(kw))) {
        lastStep.isConclusion = true;
      }
    }

    return steps;
  }

  // Check for bullet points
  const bulletPattern = /^[-*]\s+(.+)$/;
  const isBulleted = lines.some((line) => bulletPattern.test(line.trim()));

  if (isBulleted) {
    return lines
      .filter((line) => bulletPattern.test(line.trim()))
      .map((line, index) => {
        const match = line.trim().match(bulletPattern);
        return {
          number: index + 1,
          content: match ? match[1] : line.trim(),
        };
      });
  }

  // Fall back to splitting by sentences or paragraphs
  const paragraphs = reasoning.split(/\n\n+/).filter((p) => p.trim());

  if (paragraphs.length > 1) {
    return paragraphs.map((p, index) => ({
      number: index + 1,
      content: p.trim(),
      isConclusion: index === paragraphs.length - 1,
    }));
  }

  // Single block of text - split by periods for major sentences
  const sentences = reasoning
    .split(/(?<=[.!?])\s+/)
    .filter((s) => s.trim().length > 20); // Filter out very short fragments

  if (sentences.length > 1) {
    return sentences.map((s, index) => ({
      number: index + 1,
      content: s.trim(),
      isConclusion: index === sentences.length - 1,
    }));
  }

  // Return as single step
  return [{ number: 1, content: reasoning.trim() }];
}

function ReasoningStep({ step }: { step: ReasoningStep }) {
  return (
    <div className="flex items-start gap-3 py-2">
      <div
        className={cn(
          'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0',
          step.isConclusion
            ? 'bg-sara-accent-soft'
            : 'bg-sara-bg-subtle'
        )}
      >
        {step.isConclusion ? (
          <CheckCircle className="w-3.5 h-3.5 text-sara-accent" />
        ) : (
          <span className="text-caption font-medium text-sara-text-muted">
            {step.number}
          </span>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p
          className={cn(
            'text-body-small leading-relaxed',
            step.isConclusion
              ? 'text-sara-text-primary font-medium'
              : 'text-sara-text-secondary'
          )}
        >
          {step.content}
        </p>
      </div>
    </div>
  );
}

export function ReasoningPanel({ reasoning, className }: ReasoningPanelProps) {
  const steps = useMemo(() => parseReasoning(reasoning), [reasoning]);

  if (!reasoning.trim()) {
    return null;
  }

  return (
    <Card
      variant="outline"
      className={cn('overflow-hidden bg-sara-bg-base', className)}
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-4 h-4 text-sara-accent" />
          <h4 className="text-subheading text-sara-text-primary font-semibold">
            Sara&apos;s Reasoning
          </h4>
        </div>

        {/* Steps */}
        <div className="space-y-1">
          {steps.map((step, index) => (
            <div key={index}>
              <ReasoningStep step={step} />
              {index < steps.length - 1 && !step.isConclusion && (
                <div className="flex items-center pl-9 py-1">
                  <ArrowRight className="w-3 h-3 text-sara-text-muted" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

export default ReasoningPanel;
