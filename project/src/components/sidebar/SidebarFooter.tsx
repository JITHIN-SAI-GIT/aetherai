import { motion } from 'framer-motion';
import { LogOut, Settings, ChevronDown, Sparkles } from 'lucide-react';
import type { UserProfile } from '@/types';
import { cn } from '@/utils/cn';

interface SidebarFooterProps {
  user: UserProfile;
  onSettings: () => void;
  onLogout: () => void;
  collapsed: boolean;
}

export function SidebarFooter({ user, onSettings, onLogout, collapsed }: SidebarFooterProps) {
  if (collapsed) {
    return (
      <div className="flex flex-col items-center gap-2 p-2">
        <button
          onClick={onSettings}
          className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent text-sm font-bold text-primary-foreground transition-transform hover:scale-105"
        >
          {user.initials}
        </button>
        <button
          onClick={onSettings}
          className="flex h-9 w-9 items-center justify-center rounded-xl text-muted-foreground hover:bg-white/5 hover:text-foreground transition-colors"
        >
          <Settings className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-1.5 p-2">
      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={onSettings}
        className={cn(
          'group relative flex w-full items-center gap-3 rounded-xl p-2',
          'glass-panel hover:bg-white/5 transition-colors',
        )}
      >
        <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent text-sm font-bold text-primary-foreground">
          {user.initials}
          <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-success border-2 border-sidebar" />
        </div>
        <div className="flex-1 text-left">
          <p className="truncate text-sm font-medium">{user.name}</p>
          <p className="truncate text-xs text-muted-foreground flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-primary" />
            {user.plan}
          </p>
        </div>
        <ChevronDown className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-y-0.5" />
      </motion.button>

      <button
        onClick={onLogout}
        className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
      >
        <LogOut className="h-4 w-4" />
        Sign out
      </button>
    </div>
  );
}
