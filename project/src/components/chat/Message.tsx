import { motion } from 'framer-motion';
import { Check, Copy, RefreshCw, ThumbsDown, ThumbsUp, Edit2, Zap, Cpu, Database, AlertCircle } from 'lucide-react';
import type { ChatMessage } from '@/types';
import { Markdown } from './Markdown';
import { Avatar } from '@/components/ui/Avatar';
import { Tooltip } from '@/components/ui/Tooltip';
import { Logo } from '@/components/ui/Logo';
import { formatTime } from '@/utils/time';
import { cn } from '@/utils/cn';
import { useState, memo } from 'react';

interface MessageProps {
  message: ChatMessage;
  isLast: boolean;
  isStreaming: boolean;
  onRegenerate: () => void;
  onLike: (value: boolean) => void;
  onCopy: (text: string) => void;
  onEdit?: (text: string) => void;
}

export const Message = memo(function Message({ message, isLast, isStreaming, onRegenerate, onLike, onCopy, onEdit }: MessageProps) {
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(message.content);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    onCopy(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleEditSubmit = () => {
    if (editValue.trim() !== message.content && onEdit) {
      onEdit(editValue.trim());
    }
    setIsEditing(false);
  };

  const showTypingCursor = isLast && isStreaming && message.role === 'assistant';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className={cn('flex w-full gap-3 group', isUser ? 'flex-row-reverse' : 'flex-row')}
    >
      {/* Avatar */}
      <Avatar className={cn(isUser ? 'bg-gradient-to-br from-accent to-primary' : 'glass-strong')}>
        {isUser ? (
          <span className="text-xs font-bold text-white">You</span>
        ) : (
          <Logo size="sm" />
        )}
      </Avatar>

      {/* Message content */}
      <div className={cn('flex flex-col gap-1.5 max-w-[85%]', isUser ? 'items-end' : 'items-start')}>
        <div
          className={cn(
            'relative rounded-2xl px-4 py-3',
            isUser
              ? 'bg-gradient-to-br from-primary/90 to-accent/90 text-primary-foreground shadow-glow-sm'
              : message.status === 'error'
                ? 'border border-destructive/30 bg-destructive/5 text-destructive'
                : 'glass-panel',
          )}
        >
          {isEditing ? (
            <div className="flex flex-col gap-2 min-w-[300px]">
              <textarea 
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="w-full bg-white/10 rounded p-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none scrollbar-thin"
                rows={Math.min(10, editValue.split('\n').length + 1)}
                autoFocus
              />
              <div className="flex justify-end gap-2">
                <button onClick={() => setIsEditing(false)} className="text-xs px-3 py-1.5 rounded-lg hover:bg-white/10 transition-colors">Cancel</button>
                <button onClick={handleEditSubmit} className="text-xs px-3 py-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors">Save & Send</button>
              </div>
            </div>
          ) : message.content ? (
            <>
              {message.status === 'error' && (
                <div className="flex items-center gap-2 font-bold mb-2 text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  Request Failed
                </div>
              )}
              {/* Search UI Component */}
              {!isUser && message.sources && message.sources.length > 0 && (
                <div className="mb-4 space-y-2 border-b border-white/10 pb-4">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground font-medium uppercase tracking-wider">
                    <Database className="h-3 w-3" />
                    <span>Searched {message.sources.length} Sources</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {message.sources.map((source, i) => (
                      <a key={i} href={`https://${source.domain}`} target="_blank" rel="noreferrer" className="flex flex-col gap-0.5 p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-white/5 hover:border-primary/30 group/src">
                        <span className="text-xs font-semibold text-foreground group-hover/src:text-primary transition-colors truncate">{source.title}</span>
                        <span className="text-[10px] text-muted-foreground truncate">{source.domain}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}
              <div aria-live="polite" aria-atomic="true">
                <Markdown content={message.content} className={isUser ? 'prose-invert' : ''} />
              </div>
            </>
          ) : (
            <TypingIndicator />
          )}
          {showTypingCursor && message.content && (
             <span className="inline-block w-1.5 h-4 bg-primary animate-blink ml-0.5 align-middle rounded-sm" />
          )}
        </div>

        {/* Timestamp + actions + metadata badges */}
        <div className={cn('flex items-center gap-2 px-1', isUser ? 'flex-row-reverse' : 'flex-row')}>
          <span className="text-[10px] text-muted-foreground/60">{formatTime(message.createdAt)}</span>

          {/* User actions */}
          {isUser && !isEditing && (
            <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center">
               <Tooltip content="Edit">
                 <button onClick={() => setIsEditing(true)} className="rounded-md p-1 text-muted-foreground/60 hover:text-foreground hover:bg-white/5 transition-colors">
                   <Edit2 className="h-3 w-3" />
                 </button>
               </Tooltip>
            </div>
          )}

          {/* Assistant Metadata Badges (Mocked for now until backend attaches them to the message) */}
          {!isUser && message.status === 'complete' && (
            <div className="hidden sm:flex items-center gap-1.5 mr-2 opacity-50 hover:opacity-100 transition-opacity">
               <div className="flex items-center gap-1 text-[9px] uppercase font-bold tracking-wider bg-white/5 px-1.5 py-0.5 rounded border border-white/10">
                 <Cpu className="h-2.5 w-2.5 text-primary" /> GPT-4o
               </div>
               <div className="flex items-center gap-1 text-[9px] uppercase font-bold tracking-wider bg-white/5 px-1.5 py-0.5 rounded border border-white/10">
                 <Database className="h-2.5 w-2.5 text-accent" /> OpenAI
               </div>
               <div className="flex items-center gap-1 text-[9px] uppercase font-bold tracking-wider bg-white/5 px-1.5 py-0.5 rounded border border-white/10">
                 <Zap className="h-2.5 w-2.5 text-yellow-500" /> 1.2s
               </div>
            </div>
          )}

          {/* Assistant actions */}
          {!isUser && (message.status === 'complete' || message.status === 'error') && (
            <div className="flex items-center gap-0.5">
              {message.status === 'error' && (
                <Tooltip content="Retry">
                  <button onClick={onRegenerate} className="rounded-md p-1 text-destructive hover:bg-destructive/10 transition-colors">
                    <RefreshCw className="h-3.5 w-3.5" />
                  </button>
                </Tooltip>
              )}
              {message.status === 'complete' && (
                <Tooltip content="Copy">
                  <button
                    onClick={handleCopy}
                    className="rounded-md p-1 text-muted-foreground/60 hover:text-foreground hover:bg-white/5 transition-colors"
                  >
                    {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
                  </button>
                </Tooltip>
              )}
              {isLast && message.status === 'complete' && (
                <Tooltip content="Regenerate">
                  <button
                    onClick={onRegenerate}
                    className="rounded-md p-1 text-muted-foreground/60 hover:text-foreground hover:bg-white/5 transition-colors"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                  </button>
                </Tooltip>
              )}
              {message.status === 'complete' && (
                <>
                  <Tooltip content="Good response">
                    <button
                      onClick={() => onLike(true)}
                      className={cn(
                        'rounded-md p-1 transition-colors',
                        message.liked === true
                          ? 'text-success'
                          : 'text-muted-foreground/60 hover:text-foreground hover:bg-white/5',
                      )}
                    >
                      <ThumbsUp className={cn('h-3.5 w-3.5', message.liked === true && 'fill-success')} />
                    </button>
                  </Tooltip>
                  <Tooltip content="Bad response">
                    <button
                      onClick={() => onLike(false)}
                      className={cn(
                        'rounded-md p-1 transition-colors',
                        message.liked === false
                          ? 'text-destructive'
                          : 'text-muted-foreground/60 hover:text-foreground hover:bg-white/5',
                      )}
                    >
                      <ThumbsDown className={cn('h-3.5 w-3.5', message.liked === false && 'fill-destructive')} />
                    </button>
                  </Tooltip>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
});

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 py-2 px-1">
      <span className="text-xs text-primary font-medium tracking-wide mr-1">Thinking</span>
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-primary/70"
          animate={{ opacity: [0.3, 1, 0.3], y: [0, -3, 0] }}
          transition={{
            duration: 1,
            repeat: Infinity,
            delay: i * 0.15,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  );
}
