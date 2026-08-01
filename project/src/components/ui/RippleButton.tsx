import { motion } from 'framer-motion';
import { type ReactNode } from 'react';
import { cn } from '@/utils/cn';

interface RippleButtonProps {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
  activeClassName?: string;
}

export function RippleButton({ children, onClick, className }: RippleButtonProps) {
  return (
    <motion.button
      onClick={onClick}
      whileTap={{ scale: 0.96 }}
      className={cn(
        'relative overflow-hidden rounded-xl transition-colors duration-200',
        className,
      )}
    >
      {children}
    </motion.button>
  );
}
