import type { ChatMessage } from '@/types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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

// Client-side timeout (ms) — fires slightly after the backend's 14s streaming wall-clock limit.
// This is a last-resort safety net: the frontend should never trust the backend alone to
// end a loading state.
const STREAM_CLIENT_TIMEOUT_MS = 20_000;

export async function streamChatCompletion(
  request: ChatCompletionRequest,
  onChunk: (text: string) => void,
  onComplete: () => void,
  onError: (error: Error) => void
) {
  // Build a composite AbortSignal: the caller's signal OR our own timeout signal.
  const timeoutController = new AbortController();
  const timeoutId = setTimeout(() => {
    timeoutController.abort(new Error('client_timeout'));
  }, STREAM_CLIENT_TIMEOUT_MS);

  // Combine caller signal with our timeout signal
  const { signal: callerSignal, ...bodyParams } = request;
  const signals = [timeoutController.signal, callerSignal].filter(Boolean) as AbortSignal[];
  const combinedSignal = signals.length === 1
    ? signals[0]
    : AbortSignal.any
      ? AbortSignal.any(signals)
      : signals[0]; // fallback for older browsers

  try {
    const res = await fetch(`${API_BASE}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...bodyParams, stream: true }),
      signal: combinedSignal,
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
    let receivedContentChunks = 0; // track whether any real content arrived

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
              receivedContentChunks++;
              onChunk(content);
            }
          } catch (e) {
            console.warn('Failed to parse SSE data', data);
          }
        }
      }
    }

    // If the stream ended cleanly but no content was ever received, treat it as an error.
    // This happens when the backend drops the connection (provider crash) or sends no chunks.
    if (receivedContentChunks === 0) {
      onError(new Error('empty_stream: The backend returned no content. All providers may be rate-limited — please try again.'));
    } else {
      onComplete();
    }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      // Distinguish intentional user-abort from our own timeout abort
      if (timeoutController.signal.aborted) {
        onError(new Error('timeout: The request timed out after 20s. Please try again.'));
      } else {
        console.log('Stream request aborted cleanly by user.');
      }
      return;
    }
    onError(err instanceof Error ? err : new Error(String(err)));
  } finally {
    clearTimeout(timeoutId);
  }
}

