import { cn } from '@/utils/cn';

interface SliderProps {
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (value: number) => void;
  className?: string;
  trackClassName?: string;
  thumbClassName?: string;
}

export function Slider({
  value,
  min,
  max,
  step = 1,
  onChange,
  className,
  trackClassName,
  thumbClassName,
}: SliderProps) {
  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className={cn('relative flex items-center w-full', className)}>
      <div
        className={cn(
          'h-1.5 w-full rounded-full bg-white/10 cursor-pointer',
          trackClassName,
        )}
      >
        <div
          className="h-full rounded-full bg-gradient-to-r from-primary to-accent"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div
        className={cn(
          'absolute h-4 w-4 rounded-full bg-white shadow-glow-sm border-2 border-primary',
          'transition-transform duration-150 hover:scale-110 cursor-grab active:cursor-grabbing',
          thumbClassName,
        )}
        style={{ left: `calc(${percentage}% - 8px)` }}
      />
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="absolute inset-0 w-full cursor-pointer opacity-0"
      />
    </div>
  );
}
