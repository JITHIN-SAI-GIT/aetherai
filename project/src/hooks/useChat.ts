import { useCallback, useRef } from 'react';
import { useChatStore } from '@/store/chatStore';
import { streamChatCompletion } from '@/services/api';
import { uid } from '@/utils/id';

export function useChat() {
  const store = useChatStore();
  const stopRef = useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const activeConversation = store.conversations.find((c) => c.id === store.activeId) ?? null;

  const handleStreamRequest = useCallback(async (
    convId: string, 
    assistantMsgId: string, 
    requestPayload: any, 
    retryCount = 0
  ) => {
    try {
      abortControllerRef.current = new AbortController();
      await streamChatCompletion(
        { ...requestPayload, signal: abortControllerRef.current.signal },
        (chunk) => {
          if (stopRef.current) return;
          store.updateMessage(convId, assistantMsgId, (m) => ({
            ...m,
            content: m.content + chunk,
          }));
        },
        () => {
          if (stopRef.current) return;
          store.updateMessage(convId, assistantMsgId, (m) => ({
            ...m,
            status: 'complete',
          }));
          store.setIsStreaming(false);
          abortControllerRef.current = null;
        },
        async (error) => {
          if (stopRef.current) return;
          if (error.name === 'AbortError') return;

          // Timeout and empty-stream errors: do NOT retry — each retry would waste another
          // 14–20s. Show the error immediately and clearly.
          const isTimeoutOrEmpty =
            error.message.startsWith('timeout:') ||
            error.message.startsWith('empty_stream:') ||
            error.message.includes('504') ||
            error.message.includes('timed out') ||
            error.message.includes('rate-limited');

          if (!isTimeoutOrEmpty && retryCount < 3) {
            const delay = Math.pow(2, retryCount) * 1000;
            console.warn(`Streaming failed. Retrying in ${delay}ms... (Attempt ${retryCount + 1}/3)`);
            setTimeout(() => {
              handleStreamRequest(convId, assistantMsgId, requestPayload, retryCount + 1);
            }, delay);
            return;
          }

          // Always show a non-empty, human-readable error so the user is never
          // left with a blank or stuck "Thinking..." message.
          const userMessage = isTimeoutOrEmpty
            ? '⚠️ The request timed out — all AI providers may be busy. Please try again in a moment.'
            : '⚠️ Failed to connect to the AI after multiple attempts. Please check your connection and try again.';

          store.updateMessage(convId, assistantMsgId, (m) => ({
            ...m,
            status: 'error',
            content: m.content || userMessage,
          }));
          store.setIsStreaming(false);
          abortControllerRef.current = null;
        }
      );
    } catch (err: any) {
      if (err.name !== 'AbortError') {
         store.setIsStreaming(false);
      }
    }
  }, [store]);


  const sendMessage = useCallback(
    async (text: string) => {
      let convId = store.activeId;
      if (!convId) {
        convId = store.newConversation();
      }

      const userMsg = {
        id: uid('msg'),
        role: 'user' as const,
        content: text,
        createdAt: Date.now(),
        status: 'complete' as const,
      };

      const assistantMsg = {
        id: uid('msg'),
        role: 'assistant' as const,
        content: '',
        createdAt: Date.now() + 1,
        status: 'streaming' as const,
        liked: null,
      };

      // Add user msg
      store.addMessage(convId, userMsg);
      // Setup title if first msg
      const conv = store.conversations.find((c) => c.id === convId);
      if (conv && conv.messages.length === 0) {
        store.renameConversation(convId, text.slice(0, 40));
      }
      
      // Add empty assistant msg
      store.addMessage(convId, assistantMsg);
      store.setIsStreaming(true);
      stopRef.current = false;

      // Extract current conversation messages
      const currentConv = useChatStore.getState().conversations.find(c => c.id === convId);
      if (!currentConv) return;
      
      const history = currentConv.messages
        .filter(m => m.status === 'complete' && m.id !== assistantMsg.id)
        .map(m => ({ role: m.role, content: m.content }));

      const payload = {
        model: store.activeModel,
        provider: store.activeProvider,
        agent: store.activeAgent,
        messages: [...history, { role: 'user', content: text }],
      };

      await handleStreamRequest(convId, assistantMsg.id, payload);
    },
    [store, handleStreamRequest]
  );

  const regenerate = useCallback(
    async (messageId: string) => {
      const convId = store.activeId;
      if (!convId) return;
      const currentConv = store.conversations.find(c => c.id === convId);
      if (!currentConv) return;

      const msgIndex = currentConv.messages.findIndex(m => m.id === messageId);
      if (msgIndex === -1) return;

      const targetMessage = currentConv.messages[msgIndex];
      if (targetMessage.role !== 'assistant') return;

      const newMessages = currentConv.messages.slice(0, msgIndex);
      
      store.setConversations(store.conversations.map(c => 
        c.id === convId ? { ...c, messages: newMessages } : c
      ));

      const assistantMsg = {
        id: uid('msg'),
        role: 'assistant' as const,
        content: '',
        createdAt: Date.now(),
        status: 'streaming' as const,
        liked: null,
      };

      store.addMessage(convId, assistantMsg);
      store.setIsStreaming(true);
      stopRef.current = false;

      const history = newMessages
        .filter(m => m.status === 'complete')
        .map(m => ({ role: m.role, content: m.content }));

      const payload = {
        model: store.activeModel,
        provider: store.activeProvider,
        agent: store.activeAgent,
        messages: history,
      };

      await handleStreamRequest(convId, assistantMsg.id, payload);
    },
    [store, handleStreamRequest]
  );

  const editMessage = useCallback(
    async (messageId: string, newText: string) => {
      const convId = store.activeId;
      if (!convId) return;
      const currentConv = store.conversations.find(c => c.id === convId);
      if (!currentConv) return;

      const msgIndex = currentConv.messages.findIndex(m => m.id === messageId);
      if (msgIndex === -1) return;

      const targetMessage = currentConv.messages[msgIndex];
      if (targetMessage.role !== 'user') return;

      const previousMessages = currentConv.messages.slice(0, msgIndex);

      store.setConversations(store.conversations.map(c => 
        c.id === convId ? { ...c, messages: previousMessages } : c
      ));

      await sendMessage(newText);
    },
    [store, sendMessage]
  );

  const stopStreaming = useCallback(() => {
    stopRef.current = true;
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    store.setIsStreaming(false);
  }, [store]);

  return {
    ...store,
    activeConversation,
    sendMessage,
    stopStreaming,
    regenerate,
    editMessage,
    toggleLike: (id: string, val: boolean) => {
       if (store.activeId) {
         store.updateMessage(store.activeId, id, (m) => ({ ...m, liked: m.liked === val ? null : val }));
       }
    }
  };
}
