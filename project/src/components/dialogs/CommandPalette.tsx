import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Settings, Moon, Sun, Monitor, Cpu } from 'lucide-react';
import FocusTrap from 'focus-trap-react';
import { useUIStore } from '@/store/uiStore';
import { useChatStore } from '@/store/chatStore';
import { cn } from '@/utils/cn';

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen, theme, setTheme, setSettingsOpen } = useUIStore();
  const { conversations, setActiveId } = useChatStore();
  const [query, setQuery] = useState('');

  // Keyboard shortcut (Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
      if (e.key === 'Escape' && commandPaletteOpen) {
        setCommandPaletteOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  // Filter items
  const filteredConversations = conversations
    .filter((c) => c.title.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 5);

  const actions = [
    {
      id: 'settings',
      title: 'Open Settings',
      icon: Settings,
      onSelect: () => {
        setSettingsOpen(true);
        setCommandPaletteOpen(false);
      },
    },
    {
      id: 'theme-light',
      title: 'Light Theme',
      icon: Sun,
      onSelect: () => {
        setTheme('light');
        setCommandPaletteOpen(false);
      },
    },
    {
      id: 'theme-dark',
      title: 'Dark Theme',
      icon: Moon,
      onSelect: () => {
        setTheme('dark');
        setCommandPaletteOpen(false);
      },
    },
    {
      id: 'theme-system',
      title: 'System Theme',
      icon: Monitor,
      onSelect: () => {
        setTheme('system');
        setCommandPaletteOpen(false);
      },
    },
  ].filter((a) => a.title.toLowerCase().includes(query.toLowerCase()));

  return (
    <AnimatePresence>
      {commandPaletteOpen && (
        <FocusTrap>
          <div>
            <div
              className="fixed inset-0 z-[100] bg-background/80 backdrop-blur-sm transition-opacity"
              onClick={() => setCommandPaletteOpen(false)}
            />
            <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh]">
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -20 }}
                transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                className="relative z-10 w-full max-w-xl overflow-hidden rounded-2xl glass-strong shadow-2xl border border-white/[0.1] bg-card/80"
                role="dialog"
                aria-modal="true"
              >
                <div className="flex items-center gap-3 border-b border-white/[0.08] px-4 py-3">
                  <Search className="h-5 w-5 text-muted-foreground shrink-0" />
                  <input
                    type="text"
                    autoFocus
                    placeholder="Search chats, models, or settings..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="flex-1 bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none"
                  />
                  <kbd className="hidden sm:inline-flex items-center gap-1 rounded bg-white/10 px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
                    Esc
                  </kbd>
                </div>

                <div className="max-h-[60vh] overflow-y-auto scrollbar-thin p-2">
                  {filteredConversations.length > 0 && (
                    <div className="mb-4">
                      <div className="px-3 py-1.5 text-xs font-semibold uppercase text-muted-foreground tracking-wider">
                        Conversations
                      </div>
                      {filteredConversations.map((c) => (
                        <button
                          key={c.id}
                          onClick={() => {
                            setActiveId(c.id);
                            setCommandPaletteOpen(false);
                          }}
                          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-white/5 transition-colors text-left"
                        >
                          <div className="h-6 w-6 rounded-full bg-primary/20 text-primary flex items-center justify-center shrink-0">
                            {c.title.charAt(0)}
                          </div>
                          <span className="truncate">{c.title}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {actions.length > 0 && (
                    <div>
                      <div className="px-3 py-1.5 text-xs font-semibold uppercase text-muted-foreground tracking-wider">
                        Actions
                      </div>
                      {actions.map((action) => (
                        <button
                          key={action.id}
                          onClick={action.onSelect}
                          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-white/5 transition-colors text-left"
                        >
                          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-white/5 text-muted-foreground shrink-0">
                            <action.icon className="h-4 w-4" />
                          </div>
                          <span className="truncate">{action.title}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {filteredConversations.length === 0 && actions.length === 0 && (
                    <div className="py-12 text-center text-sm text-muted-foreground">
                      No results found for "{query}"
                    </div>
                  )}
                </div>
              </motion.div>
            </div>
          </div>
        </FocusTrap>
      )}
    </AnimatePresence>
  );
}
