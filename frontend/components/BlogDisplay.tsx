"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check, FileText } from "lucide-react";
import { useState } from "react";

interface BlogDisplayProps {
  content: string;
  wordCount?: number;
}

export default function BlogDisplay({ content, wordCount }: BlogDisplayProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  if (!content) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-3 text-center py-16">
        <FileText className="w-10 h-10 text-frost-dim opacity-30" />
        <p className="text-sm text-frost-dim font-display">
          Your generated blog will appear here
        </p>
        <p className="text-[11px] text-frost-dim opacity-50">
          Markdown preview with live formatting
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[#1e1e2a] flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-acid" />
          <span className="text-[10px] font-mono text-frost-dim uppercase tracking-widest">
            Markdown Preview
          </span>
        </div>
        <div className="flex items-center gap-3">
          {wordCount && (
            <span className="text-[10px] font-mono text-frost-dim">
              {wordCount.toLocaleString()} words
            </span>
          )}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 text-[10px] text-frost-dim hover:text-acid transition-colors font-mono"
          >
            {copied ? (
              <><Check className="w-3 h-3 text-signal-green" /><span className="text-signal-green">Copied</span></>
            ) : (
              <><Copy className="w-3 h-3" /><span>Copy MD</span></>
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5">
        <div className="markdown-output">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}