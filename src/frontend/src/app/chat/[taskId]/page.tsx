'use client';

import { use } from 'react';
import { useChat } from '@/hooks/useChat';
import { ChatPanel } from '@/components/chat';
import { SplitPane, ErrorBoundary, SkeletonCard } from '@/components/ui';
import { cn } from '@/lib/utils';
import { FileText } from 'lucide-react';

interface ChatPageProps {
  params: Promise<{
    taskId: string;
  }>;
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
}

function ArtifactPanel({ artifacts, isLoading }: ArtifactPanelProps) {
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
        <FileText className="w-5 h-5 text-sara-accent" aria-hidden="true" />
        <h2 className="text-subheading text-sara-text-primary">
          Artifacts
        </h2>
        {artifacts.length > 0 && (
          <span className="text-body-small text-sara-text-muted" aria-label={`${artifacts.length} artifacts`}>
            ({artifacts.length})
          </span>
        )}
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && artifacts.length === 0 ? (
          <ArtifactSkeleton />
        ) : artifacts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className={cn(
              'w-12 h-12 rounded-full mb-4',
              'bg-sara-bg-subtle border border-sara-border',
              'flex items-center justify-center'
            )}>
              <FileText className="w-6 h-6 text-sara-text-muted" aria-hidden="true" />
            </div>
            <p className="text-body text-sara-text-secondary mb-1">
              No artifacts yet
            </p>
            <p className="text-body-small text-sara-text-muted">
              Data retrieved from FHIR resources will appear here
            </p>
          </div>
        ) : (
          <div className="space-y-4" role="list" aria-label="Retrieved artifacts">
            {artifacts.map((artifact) => (
              <div
                key={artifact.id}
                role="listitem"
                className={cn(
                  'p-4 rounded-sara',
                  'bg-sara-bg-base border border-sara-border',
                  'sara-fade-in'
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-caption text-sara-accent uppercase">
                    {artifact.type}
                  </span>
                </div>
                <pre className="text-body-small text-sara-text-secondary overflow-x-auto">
                  {JSON.stringify(artifact.data, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatPage({ params }: ChatPageProps) {
  const resolvedParams = use(params);
  const { taskId } = resolvedParams;

  const {
    task,
    messages,
    artifacts,
    isLoading,
    isComplete,
    error,
    sendMessage,
    reset,
  } = useChat(taskId);

  // Retry handler for connection errors
  const handleRetry = () => {
    if (task) {
      reset();
      // The useChat hook auto-starts on mount, so reset is enough
    }
  };

  // Show error if task not found
  if (!task) {
    return (
      <div className="h-screen flex items-center justify-center bg-sara-bg-base" role="main">
        <div className="text-center">
          <h1 className="text-display-lg text-sara-text-primary mb-2">
            Task Not Found
          </h1>
          <p className="text-body text-sara-text-secondary mb-4">
            The task &quot;{taskId}&quot; could not be found.
          </p>
          <a
            href="/"
            className={cn(
              'inline-flex items-center gap-2 px-4 py-2 rounded-sara-sm',
              'bg-sara-accent text-white',
              'hover:bg-sara-accent-hover',
              'transition-colors duration-150',
              'focus:outline-none focus:ring-2 focus:ring-sara-accent focus:ring-offset-2'
            )}
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
              isLoading={isLoading}
              isComplete={isComplete}
              error={error}
              onSendMessage={sendMessage}
              onReset={reset}
              onRetry={handleRetry}
            />
          }
          right={
            <ArtifactPanel artifacts={artifacts} isLoading={isLoading} />
          }
          defaultLeftWidth={55}
          minLeftWidth={40}
          maxLeftWidth={70}
        />
      </main>
    </ErrorBoundary>
  );
}
