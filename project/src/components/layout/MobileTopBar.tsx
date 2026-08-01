import { motion, AnimatePresence } from 'framer-motion';
import { Menu, Settings as SettingsIcon } from 'lucide-react';
import { Logo } from '@/components/ui/Logo';

interface MobileTopBarProps {
  onMenuClick: () => void;
  onSettingsClick: () => void;
  title: string;
}

export function MobileTopBar({ onMenuClick, onSettingsClick, title }: MobileTopBarProps) {
  return (
    <div className="flex items-center justify-between border-b border-white/[0.06] px-3 py-2.5 md:hidden">
      <button
        onClick={onMenuClick}
        className="flex h-9 w-9 items-center justify-center rounded-xl text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
      >
        <Menu className="h-5 w-5" />
      </button>
      <div className="flex items-center gap-2">
        <Logo size="sm" />
        <span className="text-sm font-semibold">{title}</span>
      </div>
      <button
        onClick={onSettingsClick}
        className="flex h-9 w-9 items-center justify-center rounded-xl text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
      >
        <SettingsIcon className="h-5 w-5" />
      </button>
    </div>
  );
}
