import { motion, AnimatePresence } from 'framer-motion';
import { useRef, useState, type KeyboardEvent } from 'react';
import { ArrowUp, Square, Paperclip, Mic, Cpu, Database, Zap, Image as ImageIcon } from 'lucide-react';
import { useAutoResize } from '@/hooks/useAutoResize';
import { useChatStore } from '@/store/chatStore';
import { cn } from '@/utils/cn';

interface ChatInputProps {
  onSend: (text: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, onStop, isStreaming, disabled }: ChatInputProps) {
  const [value, setValue] = useState('');
  const [focused, setFocused] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const { textareaRef, height } = useAutoResize(value);
  const fileRef = useRef<HTMLInputElement>(null);
  
  const { activeModel, activeProvider, activeAgent } = useChatStore();

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
    setValue('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    // Prevent default paste if it's just an image (handle image paste here later)
    const items = e.clipboardData.items;
    for (const item of items) {
      if (item.type.indexOf('image') === 0) {
        console.log('Image pasted');
        // Handle image processing here
      }
    }
  };

  // Approximate token count (1 token ≈ 4 chars)
  const tokenCount = Math.ceil(value.length / 4);

  return (
    <div className="relative px-4 pb-4 pt-2">
      <motion.div
        animate={{
          boxShadow: focused
            ? '0 0 30px -5px hsl(var(--primary) / 0.35)'
            : '0 0 0 0 hsl(var(--primary) / 0)',
        }}
        className={cn(
          'relative mx-auto max-w-3xl rounded-3xl',
          'glass-strong transition-all duration-300 flex flex-col',
          focused && 'border-primary/30',
          isDragging && 'border-primary bg-primary/5'
        )}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => { e.preventDefault(); setIsDragging(false); }}
      >
        {/* Top toolbar (Selectors) */}
        <div className="flex items-center gap-3 px-4 pt-3 pb-1 text-[10px] uppercase font-bold tracking-wider text-muted-foreground">
          <div className="flex items-center gap-1.5 hover:text-foreground cursor-pointer transition-colors">
            <Cpu className="h-3 w-3" />
            {activeModel}
          </div>
          <div className="w-px h-3 bg-white/10" />
          <div className="flex items-center gap-1.5 hover:text-foreground cursor-pointer transition-colors">
            <Database className="h-3 w-3" />
            {activeProvider}
          </div>
          <div className="w-px h-3 bg-white/10" />
          <div className="flex items-center gap-1.5 hover:text-foreground cursor-pointer transition-colors">
            <Zap className="h-3 w-3" />
            {activeAgent}
          </div>
          <div className="flex-1" />
          {tokenCount > 0 && (
            <div className={cn("transition-colors", tokenCount > 4000 ? "text-warning" : "")}>
              ~{tokenCount} Tokens
            </div>
          )}
        </div>

        {/* Focus glow ring */}
        <AnimatePresence>
          {focused && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="pointer-events-none absolute -inset-px rounded-3xl bg-gradient-to-r from-primary/20 via-accent/20 to-primary/20 blur-md -z-10"
            />
          )}
        </AnimatePresence>

        <div className="flex items-end gap-2 p-3 pt-1">
          {/* Attach */}
          <button
            onClick={() => fileRef.current?.click()}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-muted-foreground hover:text-foreground hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            title="Attach file or image"
          >
            <Paperclip className="h-4.5 w-4.5" />
          </button>
          <input ref={fileRef} type="file" className="hidden" multiple accept="image/*,.pdf,.txt" />

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            onPaste={handlePaste}
            rows={1}
            placeholder="Message AETHER AI..."
            style={{ height }}
            className={cn(
              'flex-1 resize-none bg-transparent py-2 text-sm text-foreground',
              'placeholder:text-muted-foreground/70',
              'focus:outline-none scrollbar-thin',
              'max-h-[300px]',
            )}
          />

          {/* Mic */}
          <button
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-muted-foreground hover:text-foreground hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            title="Voice input"
          >
            <Mic className="h-4.5 w-4.5" />
          </button>

          {/* Send / Stop */}
          {isStreaming ? (
            <motion.button
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              onClick={onStop}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-black/10 dark:bg-white/10 text-foreground hover:bg-black/20 dark:hover:bg-white/15 transition-colors"
              title="Stop"
            >
              <Square className="h-4 w-4 fill-current" />
            </motion.button>
          ) : (
            <motion.button
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              whileTap={{ scale: 0.9 }}
              onClick={handleSend}
              disabled={!value.trim() || disabled}
              className={cn(
                'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-all',
                value.trim()
                  ? 'bg-gradient-to-br from-primary to-accent text-primary-foreground shadow-glow-sm'
                  : 'bg-black/5 dark:bg-white/5 text-muted-foreground/40',
              )}
              title="Send"
            >
              <ArrowUp className="h-4.5 w-4.5" />
            </motion.button>
          )}
        </div>
      </motion.div>

      <p className="mt-2 text-center text-[10px] text-muted-foreground/60">
        AETHER AI may produce inaccurate information. Always verify critical facts.
      </p>
    </div>
  );
}
