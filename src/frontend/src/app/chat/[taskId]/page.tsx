'use client';

import { useChat } from '@/hooks/useChat';
import { ChatPanel } from '@/components/chat';
import { SplitPane, ErrorBoundary, SkeletonCard } from '@/components/ui';
import { FhirResourceRenderer } from '@/components/FhirResourceRenderer';
import { cn } from '@/lib/utils';
import { FileText } from 'lucide-react';
import { FinalAnswerCard } from '@/components/artifacts/FinalAnswerCard';

interface ChatPageProps {
  params: {
    taskId: string;
  };
}

// Loading skeleton for artifacts
function ArtifactSkeleton() {
  return (
    <div className="p-4 space-y-4" aria-label="Loading artifacts">
      <SkeletonCard hasHeader hasFooter={false} />
      <SkeletonCard hasHeader={false} hasFooter={false} />
    </div>
  );
}

interface ArtifactPanelProps {
  artifacts: Array<{ id: string; type: string; data: unknown }>;
  isLoading?: boolean;
  taskId?: string;
  finalAnswer?: string | null;
}

// Individual artifact wrapper
function ArtifactCard({ artifact }: { artifact: { id: string; type: string; data: unknown } }) {
  return (
    <div role="listitem" className="animate-msg-in">
      <FhirResourceRenderer resource={artifact.data} />
    </div>
  );
}

function ArtifactPanel({ artifacts, isLoading, taskId, finalAnswer }: ArtifactPanelProps) {
  return (
    <div
      className="h-full flex flex-col bg-sara-bg-surface"
      role="complementary"
      aria-label="Artifacts panel"
    >
      {/* Header */}
      <header className={cn(
        'flex items-center gap-3 px-4 py-3',
        'border-b border-sara-border'
      )}>
        <FileText className="w-4 h-4 text-sara-text-secondary" aria-hidden="true" />
        <h2 className="text-subheading text-sara-text-primary">
          FHIR Resources
        </h2>
        {artifacts.length > 0 && (
          <span className="text-body-small text-sara-text-muted" aria-label={`${artifacts.length} resources`}>
            ({artifacts.length})
          </span>
        )}
      </header>

      {/* Final Answer Card - shown prominently at top */}
      {finalAnswer && taskId && (
        <div className="p-4 border-b border-sara-border">
          <FinalAnswerCard taskId={taskId} answer={finalAnswer} />
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && artifacts.length === 0 ? (
          <ArtifactSkeleton />
        ) : artifacts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className={cn(
              'w-12 h-12 rounded-full mb-4',
              'bg-sara-accent-soft border border-sara-border',
              'flex items-center justify-center'
            )}>
              <FileText className="w-5 h-5 text-sara-text-muted" aria-hidden="true" />
            </div>
            <p className="text-body text-sara-text-secondary mb-1">
              No FHIR resources yet
            </p>
            <p className="text-body-small text-sara-text-muted">
              Data retrieved from FHIR APIs will appear here
            </p>
          </div>
        ) : (
          <div className="space-y-4" role="list" aria-label="Retrieved FHIR resources">
            {artifacts.map((artifact) => (
              <ArtifactCard key={artifact.id} artifact={artifact} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatPage({ params }: ChatPageProps) {
  const { taskId } = params;

  const {
    task,
    messages,
    artifacts,
    workflowSteps,
    isLoading,
    isComplete,
    error,
    sendMessage,
    finalAnswer,
  } = useChat(taskId);

  // Show error if task not found
  if (!task) {
    return (
      <div className="h-screen flex items-center justify-center bg-sara-bg-base" role="main">
        <div className="text-center animate-fade-up">
          <h1 className="text-display-lg text-sara-text-primary mb-2">
            Task Not Found
          </h1>
          <p className="text-body text-sara-text-secondary mb-6">
            The task &quot;{taskId}&quot; could not be found.
          </p>
          <a
            href="/"
            className="sara-btn sara-btn-primary"
          >
            Back to Tasks
          </a>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <main className="h-screen bg-sara-bg-base">
        <SplitPane
          left={
            <ChatPanel
              task={task}
              messages={messages}
              workflowSteps={workflowSteps}
              isLoading={isLoading}
              isComplete={isComplete}
              error={error}
              onSendMessage={sendMessage}
            />
          }
          right={
            <ArtifactPanel artifacts={artifacts} isLoading={isLoading} taskId={taskId} finalAnswer={finalAnswer} />
          }
          defaultLeftWidth={55}
          minLeftWidth={40}
          maxLeftWidth={70}
        />
      </main>
    </ErrorBoundary>
  );
}
