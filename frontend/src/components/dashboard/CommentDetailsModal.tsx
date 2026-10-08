import React from 'react';
import {
  X,
  ThumbsUp,
  Calendar,
  Cpu,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge, SentimentBadge } from '@/components/ui/badge';
import { CommentItem } from '@/types';

interface CommentDetailsModalProps {
  comment: CommentItem | null;
  isOpen: boolean;
  onClose: () => void;
}

const CLASS_COLORS: Record<string, { bar: string; text: string; bg: string }> = {
  positive: { bar: 'bg-emerald-500', text: 'text-emerald-700', bg: 'bg-emerald-50' },
  negative: { bar: 'bg-rose-500', text: 'text-rose-700', bg: 'bg-rose-50' },
  neutral: { bar: 'bg-slate-400', text: 'text-slate-700', bg: 'bg-slate-50' },
  mixed: { bar: 'bg-amber-500', text: 'text-amber-700', bg: 'bg-amber-50' },
  unsupported: { bar: 'bg-purple-500', text: 'text-purple-700', bg: 'bg-purple-50' },
};

export const CommentDetailsModal: React.FC<CommentDetailsModalProps> = ({
  comment,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !comment) return null;

  const formattedDate = comment.published_at
    ? new Date(comment.published_at).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : null;

  // Normalize probabilities if present
  const probs = comment.probabilities || {};
  const probEntries = Object.entries(probs).map(([k, v]) => ({
    label: k,
    normalizedKey: k.toLowerCase(),
    value: typeof v === 'number' ? v : Number(v) || 0,
    pctDisplay: `${((typeof v === 'number' ? v : Number(v) || 0) * 100).toFixed(1)}%`,
  }));

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150"
      data-testid="comment-details-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="comment-modal-title"
    >
      <div
        className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-brand-100 text-brand-700 font-bold flex items-center justify-center text-sm">
              {(comment.author_display_name || 'U').charAt(0).toUpperCase()}
            </div>
            <div>
              <h3 id="comment-modal-title" className="text-sm font-bold text-slate-900 leading-tight">
                {comment.author_display_name || 'Anonymous User'}
              </h3>
              <div className="flex items-center gap-2 mt-0.5 text-[11px] text-slate-500">
                {formattedDate && (
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-slate-400" />
                    {formattedDate}
                  </span>
                )}
                {comment.like_count > 0 && (
                  <span className="flex items-center gap-1 text-slate-600 font-medium">
                    <ThumbsUp className="w-3 h-3 text-slate-400" />
                    {comment.like_count} likes
                  </span>
                )}
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            aria-label="Close comment details modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-5 space-y-4 overflow-y-auto">
          {/* Sentiment & Script Tags */}
          <div className="flex flex-wrap items-center gap-2">
            <SentimentBadge sentiment={comment.sentiment} />
            <span className="text-xs font-mono font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md">
              Confidence: {(comment.confidence * 100).toFixed(1)}%
            </span>
            {comment.detected_script && (
              <Badge variant="outline" size="sm">
                Script: {comment.detected_script}
              </Badge>
            )}
          </div>

          {/* Verbatim Comment Text */}
          <div className="space-y-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Verbatim Comment
            </span>
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-sm text-slate-900 leading-relaxed font-sans whitespace-pre-wrap break-words">
              {comment.original_text}
            </div>
          </div>

          {/* English Translation if Available */}
          {comment.translated_text && (
            <div className="space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-brand-600">
                English Translation
              </span>
              <div className="p-3 rounded-xl bg-brand-50/40 border border-brand-100 text-xs text-brand-950 italic leading-relaxed">
                {comment.translated_text}
              </div>
            </div>
          )}

          {/* Model Class Probabilities Breakdown */}
          {probEntries.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
                <Cpu className="w-3.5 h-3.5 text-brand-600" />
                <span>Model Probabilities Breakdown</span>
              </div>
              <div className="space-y-2">
                {probEntries.map((p) => {
                  const colorConfig = CLASS_COLORS[p.normalizedKey] || {
                    bar: 'bg-brand-500',
                    text: 'text-slate-700',
                    bg: 'bg-slate-50',
                  };
                  const pctVal = Math.max(Math.min(p.value * 100, 100), 0);

                  return (
                    <div key={p.label} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium text-slate-700">{p.label}</span>
                        <span className={`font-mono font-semibold ${colorConfig.text}`}>
                          {p.pctDisplay}
                        </span>
                      </div>
                      <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${colorConfig.bar}`}
                          style={{ width: `${pctVal}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex justify-end">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};
