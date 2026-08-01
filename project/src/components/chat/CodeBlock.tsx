import { useState } from 'react';
import { Check, Copy } from 'lucide-react';
import { useShiki } from '@/hooks/useShiki';
import { useUIStore } from '@/store/uiStore';
import { cn } from '@/utils/cn';

interface CodeBlockProps {
  language: string;
  value: string;
  className?: string;
}

const langMap: Record<string, string> = {
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  python: 'Python',
  html: 'HTML',
  css: 'CSS',
  json: 'JSON',
  bash: 'Bash',
  sh: 'Shell',
  go: 'Go',
  rust: 'Rust',
};

export function CodeBlock({ language, value, className }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const highlighter = useShiki();
  const { theme } = useUIStore();
  
  const displayLang = langMap[language?.toLowerCase()] || language || 'text';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  const actualTheme = theme === 'light' ? 'vitesse-light' : 'vitesse-dark';
  const html = highlighter?.codeToHtml(value, {
    lang: language || 'text',
    theme: actualTheme,
  });

  return (
    <div className={cn('group relative my-4 overflow-hidden rounded-xl border border-white/[0.08] shadow-sm', className)}>
      <div className="flex items-center justify-between border-b border-black/[0.05] dark:border-white/[0.08] bg-black/[0.02] dark:bg-white/[0.03] px-4 py-2 text-xs font-mono">
        <span className="font-semibold text-muted-foreground">{displayLang}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-success" />
              <span className="text-success">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              <span>Copy code</span>
            </>
          )}
        </button>
      </div>
      <div className="overflow-x-auto text-[13px] leading-relaxed">
        {html ? (
          <div dangerouslySetInnerHTML={{ __html: html }} className="p-4" />
        ) : (
          <pre className="p-4 opacity-50"><code className="font-mono">{value}</code></pre>
        )}
      </div>
    </div>
  );
}
