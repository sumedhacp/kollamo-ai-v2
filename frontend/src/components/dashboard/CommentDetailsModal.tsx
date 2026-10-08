import React from 'react';
import {
  X,
  ThumbsUp,
  Calendar,
  Cpu,
  Languages,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge, SentimentBadge } from '@/components/ui/badge';
import { CommentItem } from '@/types';

interface CommentDetailsModalProps {
  comment: CommentItem | null;
  isOpen: boolean;
  onClose: () => void;
  onTranslateComment?: (comment: CommentItem) => void;
  isTranslating?: boolean;
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
  onTranslateComment,
  isTranslating = false,
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

          {/* English Translation Section */}
          {comment.translated_text ? (
            <div className="space-y-1">
              <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-emerald-800">
                <span className="bg-emerald-100 text-emerald-800 px-1 py-0.2 rounded text-[9px] font-mono not-italic">En:</span>
                <span>English Translation</span>
              </div>
              <div className="p-3.5 rounded-xl bg-emerald-50/50 border border-emerald-200/80 text-xs text-slate-900 italic leading-relaxed font-sans">
                {comment.translated_text}
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              {comment.detected_language === 'en' || comment.detected_script?.toLowerCase() === 'english' || comment.translation_status === 'NOT_NEEDED' ? (
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-500 italic">
                  Comment is already in English.
                </div>
              ) : isTranslating ? (
                <div className="p-2.5 rounded-lg bg-brand-50 border border-brand-200 text-xs text-brand-700 font-medium flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Translating comment to English...</span>
                </div>
              ) : comment.translation_status === 'FAILED' ? (
                <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center justify-between">
                  <span>Translation unavailable.</span>
                  {onTranslateComment && (
                    <button
                      type="button"
                      onClick={() => onTranslateComment(comment)}
                      className="text-xs font-semibold underline hover:text-rose-900"
                    >
                      Retry
                    </button>
                  )}
                </div>
              ) : onTranslateComment ? (
                <div className="pt-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onTranslateComment(comment)}
                    className="w-full text-xs text-brand-700 border-brand-200 hover:bg-brand-50"
                  >
                    <Languages className="w-3.5 h-3.5 mr-1.5 text-brand-600" />
                    Translate to English
                  </Button>
                </div>
              ) : null}
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
