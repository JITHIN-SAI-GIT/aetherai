import { AnimatePresence, motion } from 'framer-motion';
import { useMemo } from 'react';
import { Pin } from 'lucide-react';
import type { Conversation } from '@/types';
import { SidebarHeader } from './SidebarHeader';
import { ConversationList } from './ConversationList';
import { SidebarFooter } from './SidebarFooter';
import type { UserProfile } from '@/types';
import { cn } from '@/utils/cn';

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  collapsed: boolean;
  onToggleCollapse: () => void;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onTogglePin: (id: string) => void;
  onRename: (id: string, newTitle: string) => void;
  onDuplicate: (id: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onSettings: () => void;
  user: UserProfile;
}

export function Sidebar({
  conversations,
  activeId,
  collapsed,
  onToggleCollapse,
  onNewChat,
  onSelect,
  onDelete,
  onTogglePin,
  onRename,
  onDuplicate,
  searchQuery,
  onSearchChange,
  onSettings,
  user,
}: SidebarProps) {
  const pinned = useMemo(
    () => conversations.filter((c) => c.pinned).sort((a, b) => b.updatedAt - a.updatedAt),
    [conversations],
  );
  const recent = useMemo(
    () => conversations.filter((c) => !c.pinned).sort((a, b) => b.updatedAt - a.updatedAt),
    [conversations],
  );

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 300 }}
      transition={{ type: 'spring', damping: 30, stiffness: 300 }}
      className={cn(
        'relative z-20 h-full shrink-0 flex-col',
        'glass border-r border-white/[0.06]',
        collapsed ? 'flex' : 'hidden md:flex',
      )}
    >
      <SidebarHeader
        collapsed={collapsed}
        onToggleCollapse={onToggleCollapse}
        onNewChat={onNewChat}
        searchQuery={searchQuery}
        onSearchChange={onSearchChange}
        onSettings={onSettings}
      />

      <div className="flex-1 overflow-y-auto scrollbar-thin px-2 pb-2">
        <AnimatePresence mode="wait">
          {collapsed ? (
            <motion.div
              key="collapsed"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-1 pt-2"
            >
              {conversations.slice(0, 8).map((c) => (
                <button
                  key={c.id}
                  onClick={() => onSelect(c.id)}
                  className={cn(
                    'flex h-9 w-9 items-center justify-center rounded-xl text-xs font-medium transition-colors',
                    c.id === activeId
                      ? 'glass-strong text-primary'
                      : 'text-muted-foreground hover:bg-white/5 hover:text-foreground',
                  )}
                  title={c.title}
                >
                  {c.title.charAt(0).toUpperCase()}
                </button>
              ))}
            </motion.div>
          ) : (
            <motion.div
              key="expanded"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              {pinned.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <Pin className="h-3 w-3" />
                    Pinned
                  </div>
                  <ConversationList
                    conversations={pinned}
                    activeId={activeId}
                    onSelect={onSelect}
                    onDelete={onDelete}
                    onTogglePin={onTogglePin}
                    onRename={onRename}
                    onDuplicate={onDuplicate}
                  />
                </div>
              )}

              <div>
                <div className="px-2.5 py-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Chat History
                </div>
                <ConversationList
                  conversations={recent}
                  activeId={activeId}
                  onSelect={onSelect}
                  onDelete={onDelete}
                  onTogglePin={onTogglePin}
                  onRename={onRename}
                  onDuplicate={onDuplicate}
                  emptyMessage="No conversations yet"
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <SidebarFooter user={user} onSettings={onSettings} onLogout={() => {}} collapsed={collapsed} />
    </motion.aside>
  );
}
