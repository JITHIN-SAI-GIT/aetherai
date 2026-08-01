import { motion } from 'framer-motion';
import { Plus, Search, PanelLeftClose, PanelLeft, Settings as SettingsIcon, PanelRight } from 'lucide-react';
import { Logo } from '@/components/ui/Logo';
import { useUIStore } from '@/store/uiStore';
import { cn } from '@/utils/cn';

interface SidebarHeaderProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  onNewChat: () => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onSettings: () => void;
}

export function SidebarHeader({
  collapsed,
  onToggleCollapse,
  onNewChat,
  searchQuery,
  onSearchChange,
  onSettings,
}: SidebarHeaderProps) {
  const { rightPanelOpen, setRightPanelOpen, setCommandPaletteOpen } = useUIStore();

  return (
    <div className="space-y-3 p-3">
      {/* Brand + collapse */}
      <div className="flex items-center justify-between">
        <div className={cn('flex items-center gap-2.5 overflow-hidden', collapsed && 'justify-center')}>
          <Logo size="md" animated />
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex flex-col leading-none"
            >
              <span className="text-base font-bold tracking-tight">
                AETHER<span className="gradient-text"> AI</span>
              </span>
              <span className="text-[10px] text-muted-foreground">Think Beyond Limits</span>
            </motion.div>
          )}
        </div>
        {!collapsed && (
          <div className="flex items-center gap-1">
            <button
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              className={cn("hidden lg:flex h-8 w-8 items-center justify-center rounded-lg transition-colors", rightPanelOpen ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-foreground hover:bg-white/5")}
              title="Toggle Right Panel"
            >
              <PanelRight className="h-4 w-4" />
            </button>
            <button
              onClick={onToggleCollapse}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      {/* New chat */}
      <motion.button
        whileHover={{ scale: collapsed ? 1.05 : 1.01 }}
        whileTap={{ scale: 0.97 }}
        onClick={onNewChat}
        className={cn(
          'flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium',
          'bg-gradient-to-r from-primary to-accent text-primary-foreground',
          'shadow-glow hover:shadow-glow-lg transition-shadow',
          collapsed && 'justify-center px-0',
        )}
      >
        <Plus className="h-4 w-4 shrink-0" />
        {!collapsed && <span>New Chat</span>}
      </motion.button>

      {/* Search */}
      {!collapsed && (
        <div className="relative group cursor-pointer" onClick={() => setCommandPaletteOpen(true)}>
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <div
            className={cn(
              'w-full rounded-xl bg-white/5 border border-white/[0.08] py-2 pl-9 pr-3 text-sm flex items-center justify-between text-muted-foreground group-hover:bg-white/10 transition-colors'
            )}
          >
            <span>Search...</span>
            <kbd className="hidden sm:inline-flex items-center gap-1 rounded bg-black/20 px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
              <span className="text-xs">Ctrl</span>K
            </kbd>
          </div>
        </div>
      )}

      {/* Collapsed quick actions */}
      {collapsed && (
        <div className="flex flex-col items-center gap-1.5">
          <button
            onClick={onToggleCollapse}
            className="flex h-9 w-9 items-center justify-center rounded-xl text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            <PanelLeft className="h-4 w-4" />
          </button>
          <button
            onClick={onSettings}
            className="flex h-9 w-9 items-center justify-center rounded-xl text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            <SettingsIcon className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
