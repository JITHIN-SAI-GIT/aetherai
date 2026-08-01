import { type ReactNode } from 'react';
import { cn } from '@/utils/cn';

interface AvatarProps {
  children: ReactNode;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'h-7 w-7 text-xs',
  md: 'h-9 w-9 text-sm',
  lg: 'h-12 w-12 text-base',
};

export function Avatar({ children, className, size = 'md' }: AvatarProps) {
  return (
    <div
      className={cn(
        'flex shrink-0 items-center justify-center rounded-full',
        sizeClasses[size],
        className,
      )}
    >
      {children}
    </div>
  );
}
