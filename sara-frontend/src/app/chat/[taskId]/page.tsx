'use client';

import { use } from 'react';
import { useChat } from '@/hooks/useChat';
import { ChatPanel } from '@/components/chat';
import { SplitPane } from '@/components/ui';
import { cn } from '@/lib/utils';
import { FileText } from 'lucide-react';

interface ChatPageProps {
  params: Promise<{
    taskId: string;
  }>;
}

function ArtifactPanel({ artifacts }: { artifacts: Array<{ id: string; type: string; data: unknown }> }) {
  return (
    <div className="h-full flex flex-col bg-sara-bg-surface">
      {/* Header */}
      <header className={cn(
        'flex items-center gap-3 px-4 py-3',
        'border-b border-sara-border'
      )}>
        <FileText className="w-5 h-5 text-sara-accent" />
        <h2 className="text-subheading text-sara-text-primary">
          Artifacts
        </h2>
        {artifacts.length > 0 && (
          <span className="text-body-small text-sara-text-muted">
            ({artifacts.length})
          </span>
        )}
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {artifacts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className={cn(
              'w-12 h-12 rounded-full mb-4',
              'bg-sara-bg-subtle border border-sara-border',
              'flex items-center justify-center'
            )}>
              <FileText className="w-6 h-6 text-sara-text-muted" />
            </div>
            <p className="text-body text-sara-text-secondary mb-1">
              No artifacts yet
            </p>
            <p className="text-body-small text-sara-text-muted">
              Data retrieved from FHIR resources will appear here
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {artifacts.map((artifact) => (
              <div
                key={artifact.id}
                className={cn(
                  'p-4 rounded-sara',
                  'bg-sara-bg-base border border-sara-border'
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
    sendMessage,
    reset,
  } = useChat(taskId);

  // Show error if task not found
  if (!task) {
    return (
      <div className="h-screen flex items-center justify-center bg-sara-bg-base">
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
              'transition-colors duration-150'
            )}
          >
            Back to Tasks
          </a>
        </div>
      </div>
    );
  }

  return (
    <main className="h-screen bg-sara-bg-base">
      <SplitPane
        left={
          <ChatPanel
            task={task}
            messages={messages}
            isLoading={isLoading}
            isComplete={isComplete}
            onSendMessage={sendMessage}
            onReset={reset}
          />
        }
        right={
          <ArtifactPanel artifacts={artifacts} />
        }
        defaultLeftWidth={55}
        minLeftWidth={40}
        maxLeftWidth={70}
      />
    </main>
  );
}
