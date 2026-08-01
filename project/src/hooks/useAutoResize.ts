import { useEffect, useRef, useState } from 'react';

export function useAutoResize(value: string, maxHeight = 200) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [height, setHeight] = useState('auto');

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    const scrollHeight = Math.min(textarea.scrollHeight, maxHeight);
    setHeight(`${scrollHeight}px`);
  }, [value, maxHeight]);

  return { textareaRef, height };
}
