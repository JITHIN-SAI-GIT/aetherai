import { motion } from 'framer-motion';
import { Logo } from '@/components/ui/Logo';
import { useGreeting } from '@/hooks/useGreeting';

interface WelcomeScreenProps {
  onSuggestionClick: (prompt: string) => void;
}

export function WelcomeScreen({ onSuggestionClick: _ }: WelcomeScreenProps) {
  const { greeting, emoji } = useGreeting();

  return (
    <div className="flex h-full flex-col items-center justify-center px-4 py-8 overflow-y-auto scrollbar-thin">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col items-center text-center"
      >
        {/* Animated logo */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1, type: 'spring', damping: 15 }}
        >
          <Logo size="xl" animated />
        </motion.div>

        {/* Branding & Greeting */}
        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-8 text-4xl font-extrabold tracking-tight sm:text-5xl"
        >
          <span className="gradient-text">AETHER</span> AI
        </motion.h1>
        
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-2 text-lg font-medium text-muted-foreground uppercase tracking-[0.2em]"
        >
          Think Beyond Limits
        </motion.p>
        
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-6 text-sm text-muted-foreground/80 max-w-md"
        >
          {greeting} {emoji} What would you like to explore today?
        </motion.p>
      </motion.div>

    </div>
  );
}
