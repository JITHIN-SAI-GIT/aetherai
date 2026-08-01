import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Pin, MoreHorizontal, Trash2, MessageSquare, Edit2, Share2, Copy } from 'lucide-react';
import type { Conversation } from '@/types';
import { cn } from '@/utils/cn';
import { formatRelativeTime } from '@/utils/time';

interface ConversationItemProps {
  conversation: Conversation;
  active: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onTogglePin: () => void;
  onRename: (newTitle: string) => void;
  onDuplicate: () => void;
}

export function ConversationItem({
  conversation,
  active,
  onSelect,
  onDelete,
  onTogglePin,
  onRename,
  onDuplicate
}: ConversationItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(conversation.title);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleRenameSubmit = () => {
    if (editValue.trim() !== '' && editValue.trim() !== conversation.title) {
      onRename(editValue.trim());
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleRenameSubmit();
    if (e.key === 'Escape') {
      setEditValue(conversation.title);
      setIsEditing(false);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.2 }}
      className="group relative"
    >
      <div
        onClick={!isEditing ? onSelect : undefined}
        className={cn(
          'relative flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-left transition-all duration-200 cursor-pointer',
          active
            ? 'glass-strong shadow-glow-sm'
            : 'hover:bg-white/5',
        )}
      >
        {active && (
          <motion.div
            layoutId="active-conv"
            className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-full bg-gradient-to-b from-primary to-accent"
          />
        )}
        <MessageSquare
          className={cn(
            'h-4 w-4 shrink-0 transition-colors',
            active ? 'text-primary' : 'text-muted-foreground',
          )}
        />
        <div className="flex-1 min-w-0">
          {isEditing ? (
            <input
              ref={inputRef}
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onBlur={handleRenameSubmit}
              onKeyDown={handleKeyDown}
              className="w-full bg-transparent text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary rounded px-1"
            />
          ) : (
            <p className={cn('truncate text-sm', active ? 'text-foreground font-medium' : 'text-muted-foreground')}>
              {conversation.title}
            </p>
          )}
          {!isEditing && (
            <p className="truncate text-[10px] text-muted-foreground/70 uppercase tracking-wider font-semibold mt-0.5">
              {formatRelativeTime(conversation.updatedAt)}
            </p>
          )}
        </div>
        {conversation.pinned && !isEditing && (
          <Pin className="h-3.5 w-3.5 shrink-0 fill-primary text-primary" />
        )}
      </div>

      {/* Hover actions */}
      {!isEditing && (
        <div className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity bg-background/80 backdrop-blur-sm rounded-lg p-0.5 shadow-sm border border-white/10">
          <button
            onClick={(e) => { e.stopPropagation(); onTogglePin(); }}
            className="rounded-md p-1.5 text-muted-foreground hover:text-primary hover:bg-white/10 transition-colors"
            title={conversation.pinned ? "Unpin" : "Pin"}
          >
            <Pin className={cn('h-3.5 w-3.5', conversation.pinned && 'fill-primary text-primary')} />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}
            className="rounded-md p-1.5 text-muted-foreground hover:text-accent hover:bg-white/10 transition-colors"
            title="Rename"
          >
            <Edit2 className="h-3 w-3" />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onDuplicate(); }}
            className="rounded-md p-1.5 text-muted-foreground hover:text-emerald-500 hover:bg-white/10 transition-colors"
            title="Fork Conversation"
          >
            <Copy className="h-3 w-3" />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            className="rounded-md p-1.5 text-muted-foreground hover:text-destructive hover:bg-white/10 transition-colors"
            title="Delete"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </motion.div>
  );
}

interface ConversationListProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onTogglePin: (id: string) => void;
  onRename: (id: string, newTitle: string) => void;
  onDuplicate: (id: string) => void;
  emptyMessage?: string;
}

export function ConversationList({
  conversations,
  activeId,
  onSelect,
  onDelete,
  onTogglePin,
  onRename,
  onDuplicate,
  emptyMessage = 'No conversations yet',
}: ConversationListProps) {
  if (conversations.length === 0) {
    return (
      <div className="px-3 py-8 text-center">
        <p className="text-sm text-muted-foreground">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <AnimatePresence mode="popLayout">
      {conversations.map((conv) => (
        <ConversationItem
          key={conv.id}
          conversation={conv}
          active={conv.id === activeId}
          onSelect={() => onSelect(conv.id)}
          onDelete={() => onDelete(conv.id)}
          onTogglePin={() => onTogglePin(conv.id)}
          onRename={(newTitle) => onRename(conv.id, newTitle)}
          onDuplicate={() => onDuplicate(conv.id)}
        />
      ))}
    </AnimatePresence>
  );
}
