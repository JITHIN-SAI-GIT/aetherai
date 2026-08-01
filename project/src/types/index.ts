export type Role = 'user' | 'assistant';

export type MessageStatus = 'sending' | 'sent' | 'streaming' | 'complete' | 'error';

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  createdAt: number;
  status: MessageStatus;
  liked?: boolean | null;
  pinned?: boolean;
  sources?: { title: string; domain: string }[];
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
  pinned: boolean;
}

export interface SuggestionCard {
  id: string;
  title: string;
  subtitle: string;
  icon: string;
  prompt: string;
  gradient: string;
}

export type ModelId = 'nova-pro' | 'nova-air' | 'nova-max' | 'nova-mini';

export interface AIModel {
  id: ModelId;
  name: string;
  description: string;
  badge: string;
}

export type AccentColor = 'teal' | 'blue' | 'emerald' | 'amber' | 'rose';

export interface Settings {
  accent: AccentColor;
  language: string;
  temperature: number;
  model: ModelId;
  memory: boolean;
  webSearch?: boolean;
  showCitations?: boolean;
  smartCaching?: boolean;
  streamingResponse?: boolean;
  promptInjectionFilter?: boolean;
  secretRedaction?: boolean;
  reducedMotion?: boolean;
  highContrast?: boolean;
  debugMode?: boolean;
  systemPrompt?: string;
}

export interface UserProfile {
  name: string;
  email: string;
  plan: string;
  initials: string;
}
