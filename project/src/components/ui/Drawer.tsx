import { AnimatePresence, motion } from 'framer-motion';
import { type ReactNode } from 'react';
import FocusTrap from 'focus-trap-react';
import { cn } from '@/utils/cn';

interface DrawerProps {
  open: boolean;
  onClose: () => void;
  side?: 'left' | 'right' | 'bottom';
  children: ReactNode;
  className?: string;
}

const sideVariants = {
  left: { initial: { x: '-100%' }, animate: { x: 0 }, exit: { x: '-100%' } },
  right: { initial: { x: '100%' }, animate: { x: 0 }, exit: { x: '100%' } },
  bottom: { initial: { y: '100%' }, animate: { y: 0 }, exit: { y: '100%' } },
};

export function Drawer({ open, onClose, side = 'left', children, className }: DrawerProps) {
  const dragProps = side === 'left' || side === 'right' 
    ? { drag: 'x' as const, dragConstraints: { left: 0, right: 0 }, dragElastic: 0.2, onDragEnd: (e: any, { offset, velocity }: any) => {
        if (side === 'left' && (offset.x < -100 || velocity.x < -500)) onClose();
        if (side === 'right' && (offset.x > 100 || velocity.x > 500)) onClose();
      }}
    : { drag: 'y' as const, dragConstraints: { top: 0, bottom: 0 }, dragElastic: 0.2, onDragEnd: (e: any, { offset, velocity }: any) => {
        if (offset.y > 100 || velocity.y > 500) onClose();
      }};

  return (
    <AnimatePresence>
      {open && (
        <FocusTrap>
          <motion.div 
            className="fixed inset-0 z-50 flex"
            role="dialog"
            aria-modal="true"
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={onClose}
              aria-hidden="true"
            />
            <motion.div
              {...dragProps}
              className={cn(
                'absolute glass-strong shadow-2xl overflow-hidden flex flex-col',
                side === 'left' && 'left-0 top-0 bottom-0 w-[300px]',
                side === 'right' && 'right-0 top-0 bottom-0 w-[300px]',
                side === 'bottom' && 'left-0 right-0 bottom-0 max-h-[80vh] rounded-t-3xl',
                className,
              )}
              variants={sideVariants[side]}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            >
              {side === 'bottom' && (
                <div className="w-full flex justify-center pt-3 pb-1" aria-hidden="true">
                  <div className="w-12 h-1.5 rounded-full bg-white/20" />
                </div>
              )}
              {children}
            </motion.div>
          </motion.div>
        </FocusTrap>
      )}
    </AnimatePresence>
  );
}
