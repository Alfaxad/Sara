import { ChatPageClient } from './ChatPageClient';

interface ChatPageProps {
  params: Promise<{
    taskId: string;
  }>;
}

export default async function ChatPage({ params }: ChatPageProps) {
  const { taskId } = await params;
  return <ChatPageClient taskId={taskId} />;
}
