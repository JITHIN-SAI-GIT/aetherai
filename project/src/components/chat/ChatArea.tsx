import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import { Trash2, Download, MoreHorizontal } from 'lucide-react';
import type { Conversation } from '@/types';
import { Message } from './Message';
import { cn } from '@/utils/cn';

interface ChatAreaProps {
  conversation: Conversation | null;
  isStreaming: boolean;
  onRegenerate: (messageId: string) => void;
  onLike: (messageId: string, value: boolean) => void;
  onClear: () => void;
  onExport: () => void;
  onEdit?: (messageId: string, newText: string) => void;
}

export function ChatArea({
  conversation,
  isStreaming,
  onRegenerate,
  onLike,
  onClear,
  onExport,
  onEdit,
}: ChatAreaProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showMenu, setShowMenu] = useState(false);
  const messages = conversation?.messages ?? [];
  const messageCount = messages.length;
  const lastMessageContent = messages[messageCount - 1]?.content;

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messageCount, lastMessageContent]);

  return (
    <div className="relative flex h-full flex-col">
      {/* Chat header */}
      <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="truncate text-sm font-medium">
            {conversation?.title ?? 'New Chat'}
          </h2>
        </div>
        <div className="relative">
          <button
            onClick={() => setShowMenu((v) => !v)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
          <AnimatePresence>
            {showMenu && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
                <motion.div
                  initial={{ opacity: 0, scale: 0.95, y: -8 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: -8 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-10 z-20 w-44 glass-strong rounded-xl p-1.5 shadow-xl"
                >
                  <button
                    onClick={() => { onExport(); setShowMenu(false); }}
                    className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm text-foreground hover:bg-white/5 transition-colors"
                  >
                    <Download className="h-4 w-4" />
                    Export Chat
                  </button>
                  <button
                    onClick={() => { onClear(); setShowMenu(false); }}
                    className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                    Clear Chat
                  </button>
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className={cn(
          'flex-1 overflow-y-auto scrollbar-thin',
          'px-4 py-6',
        )}
      >
        <div className="mx-auto flex max-w-3xl flex-col gap-6">
          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <Message
                key={msg.id}
                message={msg}
                isLast={i === messages.length - 1}
                isStreaming={isStreaming}
                onRegenerate={() => onRegenerate(msg.id)}
                onLike={(v) => onLike(msg.id, v)}
                onCopy={(text) => navigator.clipboard?.writeText(text).catch(() => {})}
                onEdit={(newText) => onEdit && onEdit(msg.id, newText)}
              />
            ))}
          </AnimatePresence>
        </div>
      </div>

    </div>
  );
}
