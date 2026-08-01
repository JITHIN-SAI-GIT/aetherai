import { useEffect, useState } from 'react';
import { createHighlighter, type Highlighter } from 'shiki';

let highlighterPromise: Promise<Highlighter> | null = null;

export function useShiki() {
  const [highlighter, setHighlighter] = useState<Highlighter | null>(null);

  useEffect(() => {
    if (!highlighterPromise) {
      highlighterPromise = createHighlighter({
        themes: ['vitesse-dark', 'vitesse-light'],
        langs: ['javascript', 'typescript', 'python', 'json', 'bash', 'markdown', 'html', 'css', 'go', 'rust']
      });
    }
    highlighterPromise.then(setHighlighter);
  }, []);

  return highlighter;
}
