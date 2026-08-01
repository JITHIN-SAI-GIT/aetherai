import { motion } from 'framer-motion';
import { cn } from '@/utils/cn';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  animated?: boolean;
  className?: string;
}

const sizeMap = {
  sm: { box: 'h-7 w-7', icon: 16, glow: 40 },
  md: { box: 'h-9 w-9', icon: 20, glow: 60 },
  lg: { box: 'h-14 w-14', icon: 32, glow: 100 },
  xl: { box: 'h-24 w-24', icon: 56, glow: 160 },
};

export function Logo({ size = 'md', animated = false, className }: LogoProps) {
  const s = sizeMap[size];
  return (
    <div className={cn('relative flex items-center justify-center', className)}>
      {animated && (
        <motion.div
          className="absolute rounded-full bg-primary/30 blur-2xl"
          style={{ width: s.glow, height: s.glow }}
          animate={{ scale: [1, 1.2, 1], opacity: [0.4, 0.7, 0.4] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        />
      )}
      <motion.div
        className={cn('relative flex items-center justify-center rounded-2xl', s.box)}
        style={{
          background: 'linear-gradient(135deg, hsl(var(--primary)), hsl(var(--accent)))',
        }}
        animate={animated ? { rotate: [0, 5, -5, 0] } : undefined}
        transition={animated ? { duration: 6, repeat: Infinity, ease: 'easeInOut' } : undefined}
      >
        <svg
          width={s.icon}
          height={s.icon}
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M12 2 L20 12 L12 22 L4 12 Z"
            fill="rgba(10,13,20,0.9)"
            stroke="rgba(10,13,20,0.95)"
            strokeWidth="0.5"
            strokeLinejoin="round"
          />
          <circle cx="12" cy="12" r="3" fill="white" opacity="0.95" />
        </svg>
      </motion.div>
    </div>
  );
}
