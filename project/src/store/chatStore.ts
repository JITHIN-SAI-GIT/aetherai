import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Conversation, ChatMessage } from '@/types';
import { uid } from '@/utils/id';

interface ChatState {
  conversations: Conversation[];
  activeId: string | null;
  isStreaming: boolean;
  searchQuery: string;
  activeModel: string;
  activeProvider: string;
  activeAgent: string;

  // Actions
  setSearchQuery: (query: string) => void;
  setActiveId: (id: string | null) => void;
  setActiveModel: (model: string) => void;
  setActiveProvider: (provider: string) => void;
  setActiveAgent: (agent: string) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  setConversations: (conversations: Conversation[]) => void;
  
  newConversation: () => string;
  addMessage: (conversationId: string, message: ChatMessage) => void;
  updateMessage: (conversationId: string, messageId: string, updater: (m: ChatMessage) => ChatMessage) => void;
  deleteConversation: (id: string) => void;
  togglePin: (id: string) => void;
  renameConversation: (id: string, title: string) => void;
  clearMessages: (id: string) => void;
  duplicateConversation: (id: string) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      conversations: [],
      activeId: null,
      isStreaming: false,
      searchQuery: '',
      activeModel: 'gpt-4o', // default
      activeProvider: 'openai',
      activeAgent: 'general',

      setSearchQuery: (searchQuery) => set({ searchQuery }),
      setActiveId: (activeId) => set({ activeId }),
      setActiveModel: (activeModel) => set({ activeModel }),
      setActiveProvider: (activeProvider) => set({ activeProvider }),
      setActiveAgent: (activeAgent) => set({ activeAgent }),
      setIsStreaming: (isStreaming) => set({ isStreaming }),
      setConversations: (conversations) => set({ conversations }),

      newConversation: () => {
        const id = uid('conv');
        const conv: Conversation = {
          id,
          title: 'New Chat',
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
          pinned: false,
        };
        set((state) => ({
          conversations: [conv, ...state.conversations],
          activeId: id,
        }));
        return id;
      },

      addMessage: (convId, message) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === convId
              ? {
                  ...c,
                  messages: [...c.messages, message],
                  updatedAt: Date.now(),
                }
              : c
          ),
        }));
      },

      updateMessage: (convId, msgId, updater) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === convId
              ? {
                  ...c,
                  messages: c.messages.map((m) => (m.id === msgId ? updater(m) : m)),
                  updatedAt: Date.now(),
                }
              : c
          ),
        }));
      },

      deleteConversation: (id) => {
        set((state) => ({
          conversations: state.conversations.filter((c) => c.id !== id),
          activeId: state.activeId === id ? null : state.activeId,
        }));
      },

      togglePin: (id) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === id ? { ...c, pinned: !c.pinned } : c
          ),
        }));
      },

      renameConversation: (id, title) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === id ? { ...c, title } : c
          ),
        }));
      },

      clearMessages: (id) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === id ? { ...c, messages: [], updatedAt: Date.now() } : c
          ),
        }));
      },

      duplicateConversation: (id) => {
        set((state) => {
          const conv = state.conversations.find((c) => c.id === id);
          if (!conv) return state;
          const newId = uid('conv');
          const duplicated = {
            ...conv,
            id: newId,
            title: `${conv.title} (Copy)`,
            createdAt: Date.now(),
            updatedAt: Date.now(),
            messages: conv.messages.map(m => ({ ...m, id: uid('msg') })),
            pinned: false
          };
          return {
            conversations: [duplicated, ...state.conversations],
            activeId: newId,
          };
        });
      },
    }),
    {
      name: 'aether-chat-storage',
      partialize: (state) => ({ 
        conversations: state.conversations,
        activeModel: state.activeModel,
        activeProvider: state.activeProvider,
        activeAgent: state.activeAgent
      }),
    }
  )
);
