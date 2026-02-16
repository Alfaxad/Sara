export const API_URL = process.env.NEXT_PUBLIC_MODAL_URL || 'https://nadhari--sara-agent-api.modal.run';

export interface RunRequest {
  taskId: string;
  prompt: string;
  context: string;
}

export interface SSEEvent {
  type: 'status' | 'thinking' | 'tool_call' | 'tool_result' | 'complete' | 'error';
  data: Record<string, unknown>;
}

export async function* streamRun(request: RunRequest): AsyncGenerator<SSEEvent> {
  const response = await fetch(`${API_URL}/api/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  if (!response.body) {
    throw new Error('No response body');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') {
          return;
        }
        try {
          const event = JSON.parse(data) as SSEEvent;
          yield event;
        } catch {
          // Skip invalid JSON
        }
      }
    }
  }
}
