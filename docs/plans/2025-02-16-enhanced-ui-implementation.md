# Enhanced Sara Demo UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement enhanced UI for Sara demo with workflow timeline, expandable FHIR cards, task-specific final answers, and demo mode restrictions.

**Architecture:** Build on existing component structure. New components for workflow timeline and final answer card. Enhance existing artifact cards with ExpandableSection component. Modify useChat hook to track workflow steps. Update ChatInput to disable after completion.

**Tech Stack:** Next.js 14, TypeScript, Tailwind CSS, Lucide React icons, existing Sara design system (monochromatic black with white accents)

---

## Task 1: Create ExpandableSection Component

**Files:**
- Create: `src/frontend/src/components/ui/ExpandableSection.tsx`

**Step 1: Create the ExpandableSection component**

```tsx
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
```

**Step 2: Export from ui index (if exists) or verify file is importable**

Run: `ls src/frontend/src/components/ui/`

**Step 3: Commit**

```bash
git add src/frontend/src/components/ui/ExpandableSection.tsx
git commit -m "feat: add ExpandableSection component for card expansion"
```

---

## Task 2: Create WorkflowStep Type and Parser Utility

**Files:**
- Create: `src/frontend/src/lib/workflow.ts`

**Step 1: Create workflow types and parser**

```typescript
export interface WorkflowStep {
  id: string;
  action: string;
  description: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  timestamp?: number;
}

/**
 * Parse a raw FHIR action into a human-readable description
 */
export function parseActionToDescription(action: string): string {
  // GET requests
  if (action.startsWith('GET')) {
    if (action.includes('/Patient')) {
      if (action.includes('name=') || action.includes('identifier=')) {
        return 'Searching patient records';
      }
      return 'Retrieving patient information';
    }
    if (action.includes('/Observation')) {
      if (action.includes('code=MG') || action.includes('code=magnesium')) {
        return 'Checking magnesium levels';
      }
      if (action.includes('code=K') || action.includes('code=potassium')) {
        return 'Checking potassium levels';
      }
      if (action.includes('code=GLU') || action.includes('code=glucose')) {
        return 'Retrieving blood glucose readings';
      }
      if (action.includes('code=A1C') || action.includes('code=HbA1C')) {
        return 'Checking HbA1C levels';
      }
      if (action.includes('code=BP') || action.includes('blood-pressure')) {
        return 'Retrieving blood pressure readings';
      }
      return 'Retrieving lab results';
    }
    if (action.includes('/MedicationRequest')) {
      return 'Checking medication orders';
    }
    if (action.includes('/ServiceRequest')) {
      return 'Checking service requests';
    }
    if (action.includes('/Condition')) {
      return 'Retrieving patient conditions';
    }
    if (action.includes('/Procedure')) {
      return 'Retrieving procedure history';
    }
    return 'Querying medical records';
  }

  // POST requests
  if (action.startsWith('POST')) {
    if (action.includes('/Observation')) {
      return 'Recording measurement';
    }
    if (action.includes('/MedicationRequest')) {
      return 'Ordering medication';
    }
    if (action.includes('/ServiceRequest')) {
      return 'Creating referral';
    }
    if (action.includes('/DiagnosticReport')) {
      return 'Creating diagnostic report';
    }
    return 'Creating medical record';
  }

  // FINISH
  if (action.startsWith('FINISH')) {
    return 'Completing task';
  }

  // Default
  return 'Processing request';
}

/**
 * Extract the endpoint from a raw action string
 */
export function extractEndpoint(action: string): string {
  // Match GET /endpoint or POST /endpoint patterns
  const match = action.match(/(GET|POST)\s+([^\s?]+)/);
  return match ? match[2] : action;
}

/**
 * Generate a unique step ID
 */
export function generateStepId(): string {
  return `step-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
```

**Step 2: Commit**

```bash
git add src/frontend/src/lib/workflow.ts
git commit -m "feat: add workflow parsing utilities for action descriptions"
```

---

## Task 3: Create WorkflowTimeline Component

**Files:**
- Create: `src/frontend/src/components/workflow/WorkflowTimeline.tsx`

**Step 1: Create the WorkflowTimeline component**

```tsx
'use client';

import { cn } from '@/lib/utils';
import { Circle, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import type { WorkflowStep } from '@/lib/workflow';

export interface WorkflowTimelineProps {
  steps: WorkflowStep[];
  className?: string;
}

function StepIcon({ status }: { status: WorkflowStep['status'] }) {
  switch (status) {
    case 'complete':
      return <CheckCircle className="w-4 h-4 text-sara-text-primary" />;
    case 'running':
      return <Loader2 className="w-4 h-4 text-sara-text-secondary animate-spin" />;
    case 'error':
      return <AlertCircle className="w-4 h-4 text-sara-error" />;
    case 'pending':
    default:
      return <Circle className="w-4 h-4 text-sara-text-muted" />;
  }
}

function StepItem({ step, isLast }: { step: WorkflowStep; isLast: boolean }) {
  return (
    <div className="flex gap-3">
      {/* Timeline column */}
      <div className="flex flex-col items-center">
        <div
          className={cn(
            'w-6 h-6 rounded-full flex items-center justify-center',
            step.status === 'running' && 'bg-sara-accent-soft',
            step.status === 'complete' && 'bg-sara-accent-soft',
            step.status === 'error' && 'bg-sara-error-soft',
            step.status === 'pending' && 'bg-sara-bg-elevated'
          )}
        >
          <StepIcon status={step.status} />
        </div>
        {!isLast && (
          <div
            className={cn(
              'w-px flex-1 min-h-[16px] my-1',
              step.status === 'complete'
                ? 'bg-sara-text-muted'
                : 'bg-sara-border'
            )}
          />
        )}
      </div>

      {/* Content column */}
      <div className="flex-1 pb-3">
        <p
          className={cn(
            'text-body-small',
            step.status === 'running' && 'text-sara-text-primary font-medium',
            step.status === 'complete' && 'text-sara-text-secondary',
            step.status === 'error' && 'text-sara-error',
            step.status === 'pending' && 'text-sara-text-muted'
          )}
        >
          {step.description}
        </p>
      </div>
    </div>
  );
}

export function WorkflowTimeline({ steps, className }: WorkflowTimelineProps) {
  if (steps.length === 0) {
    return null;
  }

  return (
    <div
      className={cn(
        'rounded-sara bg-sara-bg-elevated border border-sara-border p-4',
        'animate-sara-fade-in',
        className
      )}
    >
      <h4 className="text-caption font-medium text-sara-text-muted uppercase tracking-wider mb-3">
        Progress
      </h4>
      <div>
        {steps.map((step, index) => (
          <StepItem
            key={step.id}
            step={step}
            isLast={index === steps.length - 1}
          />
        ))}
      </div>
    </div>
  );
}

export default WorkflowTimeline;
```

**Step 2: Create index export**

```bash
mkdir -p src/frontend/src/components/workflow
```

**Step 3: Commit**

```bash
git add src/frontend/src/components/workflow/WorkflowTimeline.tsx
git commit -m "feat: add WorkflowTimeline component for visual progress"
```

---

## Task 4: Create FinalAnswerCard Component

**Files:**
- Create: `src/frontend/src/components/artifacts/FinalAnswerCard.tsx`

**Step 1: Create the FinalAnswerCard component**

```tsx
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
```

**Step 2: Commit**

```bash
git add src/frontend/src/components/artifacts/FinalAnswerCard.tsx
git commit -m "feat: add FinalAnswerCard with task-specific parsing"
```

---

## Task 5: Add Tailwind Animation Classes

**Files:**
- Modify: `src/frontend/src/app/globals.css`

**Step 1: Add new animation keyframes and utility classes**

Add these to the existing globals.css after the existing `@keyframes` section:

```css
@keyframes sara-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes sara-slide-up {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

Add to the `@layer utilities` section:

```css
  /* Sara animations */
  .animate-sara-fade-in {
    animation: sara-fade-in 0.2s ease-out;
  }

  .animate-sara-slide-up {
    animation: sara-slide-up 0.3s ease-out;
  }
```

**Step 2: Verify animations work**

Run: `cd src/frontend && npm run build`
Expected: Build succeeds without errors

**Step 3: Commit**

```bash
git add src/frontend/src/app/globals.css
git commit -m "feat: add sara-fade-in and sara-slide-up animations"
```

---

## Task 6: Update useChat Hook to Track Workflow Steps

**Files:**
- Modify: `src/frontend/src/hooks/useChat.ts`

**Step 1: Import workflow utilities and add WorkflowStep to state**

Add import at top:
```typescript
import { WorkflowStep, parseActionToDescription, generateStepId } from '@/lib/workflow';
```

Update ChatState interface:
```typescript
export interface ChatState {
  messages: Message[];
  artifacts: Artifact[];
  workflowSteps: WorkflowStep[];  // Add this
  isComplete: boolean;
  finalAnswer: string | null;
  isWarmingUp: boolean;
}
```

Update initial state:
```typescript
const [state, setState] = useState<ChatState>({
  messages: [],
  artifacts: [],
  workflowSteps: [],  // Add this
  isComplete: false,
  finalAnswer: null,
  isWarmingUp: false,
});
```

**Step 2: Update tool_call event handler to add workflow step**

In the `case 'tool_call':` handler, add workflow step creation:

```typescript
case 'tool_call':
  setState(prev => {
    const filteredMessages = prev.messages.filter(m => m.type !== 'thinking');
    const toolName = event.data.tool as string;
    const args = event.data.args as Record<string, unknown>;

    // Create action string from tool call
    const method = args?.method as string || 'GET';
    const endpoint = args?.endpoint as string || `/${toolName}`;
    const action = `${method} ${endpoint}`;

    // Create new workflow step
    const newStep: WorkflowStep = {
      id: event.data.id as string || generateStepId(),
      action,
      description: parseActionToDescription(action),
      status: 'running',
      timestamp: Date.now(),
    };

    return {
      ...prev,
      messages: [
        ...filteredMessages,
        {
          id: generateId(),
          type: 'tool_call',
          content: `Calling ${event.data.tool}...`,
          timestamp: Date.now(),
          toolCall: {
            id: event.data.id as string || generateId(),
            tool: event.data.tool as string,
            status: 'running',
            args: event.data.args as Record<string, unknown>,
          },
        },
      ],
      workflowSteps: [...prev.workflowSteps, newStep],
    };
  });
  break;
```

**Step 3: Update tool_result handler to complete workflow step**

In the `case 'tool_result':` handler, update workflow step status:

```typescript
// Inside the setState callback, after updating messages and artifacts:
// Update workflow step status
const updatedSteps = prev.workflowSteps.map(step => {
  if (step.id === toolId) {
    return {
      ...step,
      status: status === 'error' ? 'error' as const : 'complete' as const,
    };
  }
  return step;
});

return {
  ...prev,
  messages: updatedMessages,
  artifacts: newArtifacts,
  workflowSteps: updatedSteps,
};
```

**Step 4: Reset workflowSteps in reset function**

```typescript
const reset = useCallback(() => {
  stopStream();
  setState({
    messages: [],
    artifacts: [],
    workflowSteps: [],  // Add this
    isComplete: false,
    finalAnswer: null,
    isWarmingUp: false,
  });
  hasStartedRef.current = false;
}, [stopStream]);
```

**Step 5: Reset workflowSteps in initial useEffect**

```typescript
setState({
  messages: [
    {
      id: generateId(),
      type: 'user',
      content: task.question,
      timestamp: Date.now(),
    },
  ],
  artifacts: [],
  workflowSteps: [],  // Add this
  isComplete: false,
  finalAnswer: null,
  isWarmingUp: false,
});
```

**Step 6: Build and verify**

Run: `cd src/frontend && npm run build`
Expected: Build succeeds without errors

**Step 7: Commit**

```bash
git add src/frontend/src/hooks/useChat.ts
git commit -m "feat: track workflow steps in useChat hook"
```

---

## Task 7: Update MessageList to Show WorkflowTimeline

**Files:**
- Modify: `src/frontend/src/components/chat/MessageList.tsx`

**Step 1: Import WorkflowTimeline and update props**

```tsx
import { WorkflowTimeline } from '@/components/workflow/WorkflowTimeline';
import type { WorkflowStep } from '@/lib/workflow';

export interface MessageListProps {
  messages: Message[];
  workflowSteps?: WorkflowStep[];  // Add this
  isLoading?: boolean;
  className?: string;
}
```

**Step 2: Update component to render WorkflowTimeline instead of individual tool calls**

Replace the message rendering logic:

```tsx
export function MessageList({
  messages,
  workflowSteps = [],
  isLoading = false,
  className,
}: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, workflowSteps]);

  // Filter out tool_call messages - they'll be shown in WorkflowTimeline
  const displayMessages = messages.filter(m => m.type !== 'tool_call');
  const hasActiveWorkflow = workflowSteps.length > 0 && workflowSteps.some(s => s.status === 'running');

  return (
    <div
      ref={containerRef}
      className={cn(
        'flex-1 overflow-y-auto p-4 space-y-4',
        className
      )}
      role="log"
      aria-label="Chat messages"
      aria-live="polite"
      aria-relevant="additions"
    >
      {displayMessages.map((message) => {
        switch (message.type) {
          case 'user':
            return (
              <UserMessage
                key={message.id}
                content={message.content}
                timestamp={message.timestamp}
              />
            );

          case 'assistant':
            return (
              <AssistantMessage
                key={message.id}
                content={message.content}
                timestamp={message.timestamp}
              />
            );

          case 'thinking':
            return (
              <div key={message.id} className="pl-11">
                <ThinkingIndicator />
              </div>
            );

          default:
            return null;
        }
      })}

      {/* Show WorkflowTimeline when there are steps */}
      {workflowSteps.length > 0 && (
        <div className="pl-11">
          <WorkflowTimeline steps={workflowSteps} />
        </div>
      )}

      {/* Show thinking indicator if loading but no thinking message and no active workflow */}
      {isLoading && !messages.some((m) => m.type === 'thinking') && !hasActiveWorkflow && (
        <div className="pl-11">
          <ThinkingIndicator />
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
```

**Step 3: Build and verify**

Run: `cd src/frontend && npm run build`
Expected: Build succeeds without errors

**Step 4: Commit**

```bash
git add src/frontend/src/components/chat/MessageList.tsx
git commit -m "feat: integrate WorkflowTimeline into MessageList"
```

---

## Task 8: Update ChatPanel to Pass workflowSteps

**Files:**
- Modify: `src/frontend/src/components/chat/ChatPanel.tsx`

**Step 1: Add workflowSteps to props**

```tsx
import type { WorkflowStep } from '@/lib/workflow';

export interface ChatPanelProps {
  task: Task | null;
  messages: Message[];
  workflowSteps?: WorkflowStep[];  // Add this
  isLoading: boolean;
  isComplete: boolean;
  error?: string | null;
  onSendMessage: (message: string) => void;
  onReset?: () => void;
  onRetry?: () => void;
  className?: string;
}
```

**Step 2: Destructure and pass to MessageList**

```tsx
export function ChatPanel({
  task,
  messages,
  workflowSteps = [],  // Add this
  isLoading,
  isComplete,
  error,
  onSendMessage,
  onReset,
  onRetry,
  className,
}: ChatPanelProps) {
  // ... existing code ...

  {/* Messages */}
  {!error && (
    <MessageList
      messages={messages}
      workflowSteps={workflowSteps}  // Add this
      isLoading={isLoading}
      className="flex-1"
    />
  )}
```

**Step 3: Build and verify**

Run: `cd src/frontend && npm run build`
Expected: Build succeeds without errors

**Step 4: Commit**

```bash
git add src/frontend/src/components/chat/ChatPanel.tsx
git commit -m "feat: pass workflowSteps through ChatPanel"
```

---

## Task 9: Update Task Page to Pass workflowSteps

**Files:**
- Modify: `src/frontend/src/app/task/[id]/page.tsx`

**Step 1: Read current file**

Run: `cat src/frontend/src/app/task/[id]/page.tsx`

**Step 2: Update to pass workflowSteps from useChat**

The useChat hook now returns workflowSteps. Pass it to ChatPanel:

```tsx
<ChatPanel
  task={task}
  messages={messages}
  workflowSteps={workflowSteps}  // Add this
  isLoading={isLoading}
  isComplete={isComplete}
  error={error}
  onSendMessage={sendMessage}
  onReset={reset}
  onRetry={reset}
/>
```

**Step 3: Build and verify**

Run: `cd src/frontend && npm run build`
Expected: Build succeeds without errors

**Step 4: Commit**

```bash
git add src/frontend/src/app/task/[id]/page.tsx
git commit -m "feat: pass workflowSteps to ChatPanel in task page"
```

---

## Task 10: Update ChatInput to Hide in Demo Mode After Completion

**Files:**
- Modify: `src/frontend/src/components/chat/ChatInput.tsx`

**Step 1: Add isComplete prop and hide input when complete**

```tsx
export interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  isComplete?: boolean;  // Add this
  placeholder?: string;
  className?: string;
}

export function ChatInput({
  onSend,
  isLoading = false,
  disabled = false,
  isComplete = false,  // Add this
  placeholder = 'Message Sara...',
  className,
}: ChatInputProps) {
  const [value, setValue] = useState('');

  // ... existing handlers ...

  // Hide entirely when complete (demo mode)
  if (isComplete) {
    return (
      <div
        className={cn(
          'p-4 border-t border-sara-border',
          className
        )}
      >
        <div className="text-center text-body-small text-sara-text-muted py-2">
          Demo complete. Click Reset to try again.
        </div>
      </div>
    );
  }

  // ... rest of existing component ...
```

**Step 2: Update ChatPanel to pass isComplete**

In ChatPanel.tsx:

```tsx
<ChatInput
  onSend={onSendMessage}
  isLoading={isLoading}
  disabled={!task || !!error}
  isComplete={isComplete}  // Add this
  placeholder={
    error
      ? 'Fix the error to continue...'
      : 'Message Sara...'
  }
/>
```

**Step 3: Build and verify**

Run: `cd src/frontend && npm run build`
Expected: Build succeeds without errors

**Step 4: Commit**

```bash
git add src/frontend/src/components/chat/ChatInput.tsx src/frontend/src/components/chat/ChatPanel.tsx
git commit -m "feat: hide chat input after demo completion"
```

---

## Task 11: Update ArtifactPanel to Show FinalAnswerCard

**Files:**
- Modify: `src/frontend/src/components/artifacts/ArtifactPanel.tsx`

**Step 1: Import FinalAnswerCard and add props**

```tsx
import { FinalAnswerCard } from './FinalAnswerCard';

export interface ArtifactPanelProps {
  artifacts: Artifact[];
  reasoning?: string;
  taskId?: string;  // Add this
  finalAnswer?: string | null;  // Add this
  className?: string;
}
```

**Step 2: Add FinalAnswerCard at the top of artifacts**

```tsx
export function ArtifactPanel({
  artifacts,
  reasoning,
  taskId,
  finalAnswer,
  className
}: ArtifactPanelProps) {
  const [showSource, setShowSource] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);

  if (artifacts.length === 0 && !reasoning && !finalAnswer) {
    return null;
  }

  return (
    <div
      className={cn(
        'bg-sara-bg-surface rounded-sara border border-sara-border',
        'animate-sara-fade-in',
        className
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-sara-border">
        <div className="flex items-center gap-2">
          <div className="sara-icon-box">
            <Sparkles className="w-[17px] h-[17px]" />
          </div>
          <h2 className="text-subheading text-sara-text-primary">
            Key Findings
          </h2>
        </div>
      </div>

      {/* Final Answer Card - shown prominently at top */}
      {finalAnswer && taskId && (
        <div className="p-4 border-b border-sara-border">
          <FinalAnswerCard taskId={taskId} answer={finalAnswer} />
        </div>
      )}

      {/* Artifacts Stack */}
      <div className="p-4 space-y-4">
        {artifacts.map((artifact) => (
          <div key={artifact.id} className="animate-sara-slide-up">
            {renderArtifactContent(artifact)}
          </div>
        ))}
      </div>

      {/* ... rest of collapsible sections ... */}
```

**Step 3: Build and verify**

Run: `cd src/frontend && npm run build`
Expected: Build succeeds without errors

**Step 4: Commit**

```bash
git add src/frontend/src/components/artifacts/ArtifactPanel.tsx
git commit -m "feat: integrate FinalAnswerCard into ArtifactPanel"
```

---

## Task 12: Update Task Page to Pass taskId and finalAnswer to ArtifactPanel

**Files:**
- Modify: `src/frontend/src/app/task/[id]/page.tsx`

**Step 1: Pass taskId and finalAnswer to ArtifactPanel**

```tsx
<ArtifactPanel
  artifacts={artifacts}
  taskId={taskId}  // Add this
  finalAnswer={finalAnswer}  // Add this
/>
```

**Step 2: Build and verify**

Run: `cd src/frontend && npm run build`
Expected: Build succeeds without errors

**Step 3: Commit**

```bash
git add src/frontend/src/app/task/[id]/page.tsx
git commit -m "feat: pass taskId and finalAnswer to ArtifactPanel"
```

---

## Task 13: Update Disclaimer Component with New Text

**Files:**
- Modify: `src/frontend/src/components/landing/Disclaimer.tsx`

**Step 1: Update disclaimer text**

```tsx
export function Disclaimer({ className }: DisclaimerProps) {
  return (
    <section className={cn("w-full px-5 py-12", className)}>
      <div className="max-w-[840px] mx-auto">
        <div className="border-t border-sara-border pt-6">
          <div className="flex items-start gap-3">
            {/* Warning Icon */}
            <div className="flex-shrink-0 mt-0.5">
              <AlertTriangle className="w-4 h-4 text-sara-text-muted" />
            </div>

            {/* Disclaimer Text */}
            <div className="flex-1">
              <h3 className="text-body-small font-medium text-sara-text-secondary mb-2">
                Disclaimer
              </h3>
              <p className="text-caption text-sara-text-muted leading-relaxed">
                This demonstration is for illustrative purposes only and does not
                represent a finished or approved product. It is not representative
                of compliance to any regulations or standards for quality, safety
                or efficacy. Any real-world application would require additional
                development, training, and adaptation. The experience highlighted
                in this demo shows MedGemma&apos;s baseline capability for the displayed
                task and is intended to help developers and users explore possible
                applications and inspire further development.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
```

**Step 2: Build and verify**

Run: `cd src/frontend && npm run build`
Expected: Build succeeds without errors

**Step 3: Commit**

```bash
git add src/frontend/src/components/landing/Disclaimer.tsx
git commit -m "feat: update disclaimer with new legal text"
```

---

## Task 14: Enhance PatientCard with Expandable Sections

**Files:**
- Modify: `src/frontend/src/components/artifacts/PatientCard.tsx`

**Step 1: Import ExpandableSection**

```tsx
import { ExpandableSection } from '@/components/ui/ExpandableSection';
```

**Step 2: Add expandable sections for identifiers and contact info**

After the MRN section, add expandable sections:

```tsx
{/* Expandable: Contact Information */}
{(address || phone) && (
  <ExpandableSection
    title="Contact Information"
    count={[address, phone].filter(Boolean).length}
  >
    <div className="space-y-2 pl-5">
      {address && (
        <div className="flex items-start gap-2 text-body-small">
          <MapPin className="w-3.5 h-3.5 text-sara-text-muted flex-shrink-0 mt-0.5" />
          <span className="text-sara-text-secondary">{address}</span>
        </div>
      )}
      {phone && (
        <div className="flex items-center gap-2 text-body-small">
          <Phone className="w-3.5 h-3.5 text-sara-text-muted flex-shrink-0" />
          <span className="text-sara-text-secondary">{phone}</span>
        </div>
      )}
    </div>
  </ExpandableSection>
)}

{/* Expandable: All Identifiers */}
{data.identifier && data.identifier.length > 1 && (
  <ExpandableSection
    title="Identifiers"
    count={data.identifier.length}
  >
    <div className="space-y-2 pl-5">
      {data.identifier.map((id, index) => (
        <div key={index} className="flex items-center gap-2 text-body-small">
          <Hash className="w-3.5 h-3.5 text-sara-text-muted flex-shrink-0" />
          <span className="text-sara-text-muted">
            {id.type?.text || id.type?.coding?.[0]?.display || 'ID'}:
          </span>
          <span className="text-sara-text-secondary font-mono">{id.value}</span>
        </div>
      ))}
    </div>
  </ExpandableSection>
)}
```

**Step 3: Remove the previous inline contact display (since it's now in expandable)**

Remove the standalone address/phone display at the bottom.

**Step 4: Build and verify**

Run: `cd src/frontend && npm run build`
Expected: Build succeeds without errors

**Step 5: Commit**

```bash
git add src/frontend/src/components/artifacts/PatientCard.tsx
git commit -m "feat: add expandable sections to PatientCard"
```

---

## Task 15: Enhance LabResultsCard with Expandable Sections

**Files:**
- Modify: `src/frontend/src/components/artifacts/LabResultsCard.tsx`

**Step 1: Import ExpandableSection**

```tsx
import { ExpandableSection } from '@/components/ui/ExpandableSection';
```

**Step 2: Add expandable section for interpretation details**

After the reference range display, add:

```tsx
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
```

**Step 3: Build and verify**

Run: `cd src/frontend && npm run build`
Expected: Build succeeds without errors

**Step 4: Commit**

```bash
git add src/frontend/src/components/artifacts/LabResultsCard.tsx
git commit -m "feat: add expandable sections to LabResultsCard"
```

---

## Task 16: Final Integration Test

**Step 1: Run full build**

```bash
cd src/frontend && npm run build
```

Expected: Build succeeds without errors

**Step 2: Run dev server and manually test**

```bash
cd src/frontend && npm run dev
```

Test checklist:
- [ ] Landing page shows updated disclaimer
- [ ] Task page shows WorkflowTimeline during execution
- [ ] Tool calls appear as steps in timeline
- [ ] FinalAnswerCard displays after completion
- [ ] Chat input is hidden after completion
- [ ] PatientCard shows expandable sections
- [ ] LabResultsCard shows expandable sections
- [ ] Reset button works to restart task

**Step 3: Commit final integration**

```bash
git add -A
git commit -m "feat: complete enhanced Sara demo UI implementation

- WorkflowTimeline shows human-readable action progress
- FinalAnswerCard with task-specific result parsing
- Expandable sections in PatientCard and LabResultsCard
- Chat input hidden after demo completion
- Updated disclaimer text on landing page"
```

---

## Summary

This plan implements the enhanced Sara demo UI in 16 tasks:

1. **Tasks 1-4**: Create new components (ExpandableSection, workflow utils, WorkflowTimeline, FinalAnswerCard)
2. **Task 5**: Add CSS animations
3. **Tasks 6-9**: Integrate workflow tracking through useChat → MessageList → ChatPanel → Page
4. **Task 10**: Hide chat input after completion
5. **Tasks 11-12**: Integrate FinalAnswerCard into ArtifactPanel
6. **Task 13**: Update disclaimer text
7. **Tasks 14-15**: Enhance existing cards with expandable sections
8. **Task 16**: Final integration test

Each task is atomic, testable, and builds on previous work. The implementation maintains the existing monochromatic design system and follows established patterns.
