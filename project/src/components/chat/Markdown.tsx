import { memo, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import DOMPurify from 'dompurify';
import { CodeBlock } from './CodeBlock';
import { cn } from '@/utils/cn';

interface MarkdownProps {
  content: string;
  className?: string;
}

export const Markdown = memo(function Markdown({ content, className }: MarkdownProps) {
  const sanitizedContent = useMemo(() => {
    return DOMPurify.sanitize(content, {
      ALLOWED_TAGS: [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'p', 'a', 'ul', 'ol',
        'nl', 'li', 'b', 'i', 'strong', 'em', 'strike', 'code', 'hr', 'br', 'div',
        'table', 'thead', 'caption', 'tbody', 'tr', 'th', 'td', 'pre', 'span',
        'img', 'details', 'summary'
      ],
      ALLOWED_ATTR: ['href', 'name', 'target', 'class', 'src', 'alt', 'title', 'rel'],
    });
  }, [content]);

  return (
    <div
      className={cn(
        'prose prose-invert prose-sm max-w-none',
        'prose-p:my-2 prose-p:leading-relaxed',
        'prose-headings:font-semibold prose-headings:text-foreground',
        'prose-h1:text-xl prose-h2:text-lg prose-h3:text-base',
        'prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5',
        'prose-strong:text-foreground prose-em:text-foreground',
        'prose-code:rounded prose-code:bg-white/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:text-xs prose-code:text-primary prose-code:before:content-none prose-code:after:content-none',
        'prose-pre:bg-transparent prose-pre:p-0 prose-pre:my-0',
        'prose-blockquote:border-l-primary prose-blockquote:border-l-2 prose-blockquote:pl-3 prose-blockquote:italic prose-blockquote:text-muted-foreground',
        'prose-a:text-primary prose-a:underline prose-a:underline-offset-2',
        'prose-table:text-sm prose-table:border-collapse',
        'prose-th:border prose-th:border-white/10 prose-th:px-3 prose-th:py-1.5 prose-th:text-left prose-th:font-semibold',
        'prose-td:border prose-td:border-white/10 prose-td:px-3 prose-td:py-1.5',
        'prose-hr:border-white/10',
        className,
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          code({ className: codeClassName, children, ...props }) {
            const match = /language-(\w+)/.exec(codeClassName || '');
            const value = String(children).replace(/\n$/, '');
            const isBlock = codeClassName?.includes('language-') || value.includes('\n');
            if (isBlock && match) {
              return <CodeBlock language={match[1]} value={value} />;
            }
            if (isBlock) {
              return <CodeBlock language="" value={value} />;
            }
            return (
              <code className={codeClassName} {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {sanitizedContent}
      </ReactMarkdown>
    </div>
  );
});
