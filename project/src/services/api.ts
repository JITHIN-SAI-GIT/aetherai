import type { ChatMessage } from '@/types';

const API_BASE = 'http://localhost:8000';

export interface ChatCompletionRequest {
  model: string;
  messages: { role: string; content: string }[];
  stream?: boolean;
  temperature?: number;
  user?: string;
  // Custom extensions for AETHER AI backend routing
  provider?: string;
  agent?: string;
  signal?: AbortSignal;
}

export async function fetchModels() {
  try {
    const res = await fetch(`${API_BASE}/v1/models`);
    if (!res.ok) throw new Error('Failed to fetch models');
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function fetchProviders() {
  try {
    const res = await fetch(`${API_BASE}/internal/providers`);
    if (!res.ok) throw new Error('Failed to fetch providers');
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function fetchSearchProviders() {
  try {
    const res = await fetch(`${API_BASE}/internal/search/providers`);
    if (!res.ok) throw new Error('Failed to fetch search providers');
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function fetchMemoryProfile() {
  try {
    const res = await fetch(`${API_BASE}/internal/memory/profile`);
    if (!res.ok) throw new Error('Failed to fetch memory profile');
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function fetchMemoryPreferences() {
  try {
    const res = await fetch(`${API_BASE}/internal/memory/preferences`);
    if (!res.ok) throw new Error('Failed to fetch memory preferences');
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function fetchMemorySession() {
  try {
    const res = await fetch(`${API_BASE}/internal/memory/session`);
    if (!res.ok) throw new Error('Failed to fetch memory session');
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function fetchSecurityMetrics() {
  try {
    const res = await fetch(`${API_BASE}/internal/security/metrics`);
    if (!res.ok) throw new Error('Failed to fetch security metrics');
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function fetchPerformanceMetrics() {
  try {
    const res = await fetch(`${API_BASE}/internal/performance`);
    if (!res.ok) throw new Error('Failed to fetch performance metrics');
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function fetchPerformanceLatency() {
  try {
    const res = await fetch(`${API_BASE}/internal/performance/latency`);
    if (!res.ok) throw new Error('Failed to fetch performance latency');
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function fetchSearchMetrics() {
  try {
    const res = await fetch(`${API_BASE}/internal/search/metrics`);
    if (!res.ok) throw new Error('Failed to fetch search metrics');
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function streamChatCompletion(
  request: ChatCompletionRequest,
  onChunk: (text: string) => void,
  onComplete: () => void,
  onError: (error: Error) => void
) {
  try {
    const { signal, ...bodyParams } = request;
    const res = await fetch(`${API_BASE}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...bodyParams, stream: true }),
      signal,
    });

    if (!res.ok) {
      throw new Error(`API Error: ${res.status}`);
    }

    if (!res.body) {
      throw new Error('ReadableStream not supported');
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      
      // keep the last incomplete line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            continue;
          }
          try {
            const parsed = JSON.parse(data);
            const content = parsed.choices?.[0]?.delta?.content || '';
            if (content) {
              onChunk(content);
            }
          } catch (e) {
            console.warn('Failed to parse SSE data', data);
          }
        }
      }
    }
    onComplete();
  } catch (err: any) {
    if (err.name === 'AbortError') {
      console.log('Stream request aborted cleanly.');
      return; // Do not call onError if it's an intentional abort
    }
    onError(err instanceof Error ? err : new Error(String(err)));
  }
}
