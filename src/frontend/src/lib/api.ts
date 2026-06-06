const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_MODAL_URL;

export const API_URL =
  configuredApiUrl ||
  (process.env.NODE_ENV === 'development'
    ? 'http://127.0.0.1:8000'
    : 'https://nadhari--sara-for-iris-api.modal.run');

export interface RunRequest {
  taskId: string;
  prompt: string;
  context: string;
}

export interface SSEEvent {
  type: 'status' | 'thinking' | 'tool_call' | 'tool_result' | 'trace' | 'complete' | 'error';
  data: Record<string, unknown>;
}

const knownEventTypes = new Set<SSEEvent['type']>([
  'status',
  'thinking',
  'tool_call',
  'tool_result',
  'trace',
  'complete',
  'error',
]);

function parseSSEBlock(block: string): SSEEvent | null {
  let eventType: string | null = null;
  const dataLines: string[] = [];

  for (const rawLine of block.split('\n')) {
    const line = rawLine.trimEnd();
    if (!line || line.startsWith(':')) {
      continue;
    }
    if (line.startsWith('event:')) {
      eventType = line.slice(6).trim();
      continue;
    }
    if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  const rawData = dataLines.join('\n');
  if (!rawData || rawData === '[DONE]') {
    return rawData === '[DONE]' ? { type: 'complete', data: { done: true } } : null;
  }

  try {
    const parsed = JSON.parse(rawData) as Record<string, unknown>;
    if (
      typeof parsed.type === 'string' &&
      knownEventTypes.has(parsed.type as SSEEvent['type']) &&
      parsed.data &&
      typeof parsed.data === 'object'
    ) {
      return parsed as unknown as SSEEvent;
    }
    if (eventType && knownEventTypes.has(eventType as SSEEvent['type'])) {
      return {
        type: eventType as SSEEvent['type'],
        data: parsed,
      };
    }
  } catch {
    if (eventType && knownEventTypes.has(eventType as SSEEvent['type'])) {
      return {
        type: eventType as SSEEvent['type'],
        data: { content: rawData },
      };
    }
  }

  return null;
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
    const blocks = buffer.split(/\n\n|\r\n\r\n/);
    buffer = blocks.pop() || '';

    for (const block of blocks) {
      const event = parseSSEBlock(block);
      if (!event) {
        continue;
      }
      if (event.data.done === true) {
        return;
      }
      yield event;
    }
  }

  const finalEvent = parseSSEBlock(buffer);
  if (finalEvent && finalEvent.data.done !== true) {
    yield finalEvent;
  }
}
