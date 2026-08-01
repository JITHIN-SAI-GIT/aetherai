import type { AccentColor } from '@/types';

interface AccentHSL {
  primary: string;
  accent: string;
  ring: string;
}

const accents: Record<AccentColor, AccentHSL> = {
  teal: { primary: '172 76% 51%', accent: '199 89% 48%', ring: '172 76% 51%' },
  blue: { primary: '217 91% 60%', accent: '199 89% 48%', ring: '217 91% 60%' },
  emerald: { primary: '142 71% 45%', accent: '160 84% 39%', ring: '142 71% 45%' },
  amber: { primary: '38 92% 50%', accent: '25 95% 53%', ring: '38 92% 50%' },
  rose: { primary: '347 77% 60%', accent: '10 80% 56%', ring: '347 77% 60%' },
};

export function applyAccent(color: AccentColor): void {
  const root = document.documentElement;
  const values = accents[color];
  root.style.setProperty('--primary', values.primary);
  root.style.setProperty('--accent', values.accent);
  root.style.setProperty('--ring', values.ring);
}

export const accentList: { id: AccentColor; label: string; swatch: string }[] = [
  { id: 'teal', label: 'Teal', swatch: 'hsl(172 76% 51%)' },
  { id: 'blue', label: 'Azure', swatch: 'hsl(217 91% 60%)' },
  { id: 'emerald', label: 'Emerald', swatch: 'hsl(142 71% 45%)' },
  { id: 'amber', label: 'Amber', swatch: 'hsl(38 92% 50%)' },
  { id: 'rose', label: 'Rose', swatch: 'hsl(347 77% 60%)' },
];
