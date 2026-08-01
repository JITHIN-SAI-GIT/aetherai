import { motion } from 'framer-motion';
import { useMemo } from 'react';
import { useMouseGlow } from '@/hooks/useMouseGlow';

interface OrbConfig {
  id: number;
  size: number;
  x: string;
  y: string;
  color: string;
  duration: number;
  delay: number;
}

const orbs: OrbConfig[] = [
  { id: 1, size: 500, x: '-10%', y: '-15%', color: 'hsl(172 76% 51% / 0.15)', duration: 20, delay: 0 },
  { id: 2, size: 400, x: '70%', y: '10%', color: 'hsl(199 89% 48% / 0.12)', duration: 25, delay: 2 },
  { id: 3, size: 350, x: '20%', y: '70%', color: 'hsl(142 71% 45% / 0.1)', duration: 30, delay: 4 },
  { id: 4, size: 300, x: '80%', y: '75%', color: 'hsl(172 76% 51% / 0.08)', duration: 22, delay: 1 },
];

const particles = Array.from({ length: 30 }, (_, i) => ({
  id: i,
  x: Math.random() * 100,
  y: Math.random() * 100,
  size: Math.random() * 3 + 1,
  duration: Math.random() * 10 + 10,
  delay: Math.random() * 5,
}));

export function AnimatedBackground() {
  const { position, visible } = useMouseGlow();

  const particleElements = useMemo(
    () =>
      particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute rounded-full bg-white/20"
          style={{ left: `${p.x}%`, top: `${p.y}%`, width: p.size, height: p.size }}
          animate={{ y: [0, -30, 0], opacity: [0.1, 0.4, 0.1] }}
          transition={{ duration: p.duration, delay: p.delay, repeat: Infinity, ease: 'easeInOut' }}
        />
      )),
    [],
  );

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden bg-background">
      {/* Base gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-[hsl(220_30%_4%)]" />

      {/* Grid overlay */}
      <div className="absolute inset-0 bg-grid opacity-30" />

      {/* Floating orbs */}
      {orbs.map((orb) => (
        <motion.div
          key={orb.id}
          className="absolute rounded-full blur-3xl"
          style={{
            width: orb.size,
            height: orb.size,
            left: orb.x,
            top: orb.y,
            background: orb.color,
          }}
          animate={{
            x: [0, 50, -30, 0],
            y: [0, -40, 20, 0],
            scale: [1, 1.1, 0.95, 1],
          }}
          transition={{
            duration: orb.duration,
            delay: orb.delay,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}

      {/* Particles */}
      {particleElements}

      {/* Mouse glow */}
      <motion.div
        className="absolute pointer-events-none rounded-full blur-3xl"
        style={{
          width: 400,
          height: 400,
          background: 'radial-gradient(circle, hsl(var(--primary) / 0.08), transparent 70%)',
          left: position.x - 200,
          top: position.y - 200,
          opacity: visible ? 1 : 0,
        }}
        animate={{ opacity: visible ? 1 : 0 }}
        transition={{ duration: 0.3 }}
      />

      {/* Vignette */}
      <div className="absolute inset-0 bg-gradient-to-t from-background/80 via-transparent to-background/40" />
    </div>
  );
}
