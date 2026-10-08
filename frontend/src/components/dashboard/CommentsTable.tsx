import React from 'react';
import {
  ThumbsUp,
  ChevronLeft,
  ChevronRight,
  Filter,
  Eye,
  Languages,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge, SentimentBadge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { CommentItem } from '@/types';

interface CommentsTableProps {
  comments: CommentItem[];
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalFiltered: number;
  onPageChange: (page: number) => void;
  onInspectComment: (comment: CommentItem) => void;
  onTranslateComment?: (comment: CommentItem) => void;
  translatingCommentId?: string | null;
  isSkeleton?: boolean;
  onClearFilters?: () => void;
  hasActiveFilters?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyAction?: React.ReactNode;
}


export const CommentsTable: React.FC<CommentsTableProps> = ({
  comments,
  currentPage,
  totalPages,
  pageSize,
  totalFiltered,
  onPageChange,
  onInspectComment,
  onTranslateComment,
  translatingCommentId = null,
  isSkeleton = false,
  onClearFilters,
  hasActiveFilters = false,
  emptyTitle,
  emptyDescription,
  emptyAction,
}) => {
  if (isSkeleton) {
    return (
      <div className="p-6 space-y-4" data-testid="dashboard-table-skeleton">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    );
  }

  if (comments.length === 0) {
    return (
      <div className="p-8">
        <EmptyState
          icon={<Filter className="w-8 h-8 text-slate-400" />}
          title={emptyTitle || (hasActiveFilters ? 'No Matching Comments Found' : 'No Analyzed Comments')}
          description={
            emptyDescription ||
            (hasActiveFilters
              ? 'No comments matched your current keyword, sentiment, or script filter criteria.'
              : 'No comments available for this video.')
          }
          action={
            emptyAction ||
            (hasActiveFilters && onClearFilters ? (
              <Button variant="outline" size="sm" onClick={onClearFilters}>
                Clear All Filters
              </Button>
            ) : undefined)
          }
        />
      </div>
    );
  }

  const startIndex = (currentPage - 1) * pageSize + 1;
  const endIndex = Math.min(currentPage * pageSize, totalFiltered);

  return (
    <div data-testid="comments-table">
      {/* Desktop Table View */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
            <tr>
              <th className="px-4 py-3">Author</th>
              <th className="px-4 py-3">Comment Text & Translation</th>
              <th className="px-4 py-3">Script</th>
              <th className="px-4 py-3">Sentiment</th>
              <th className="px-4 py-3">Confidence</th>
              <th className="px-4 py-3">Likes</th>
              <th className="px-4 py-3 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {comments.map((c) => (
              <tr
                key={c.comment_id}
                className="hover:bg-slate-50/60 transition-colors cursor-pointer group"
                onClick={() => onInspectComment(c)}
              >
                {/* Author Info */}
                <td className="px-4 py-3 font-medium text-slate-900 whitespace-nowrap align-top">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-[10px] font-bold text-slate-700">
                      {(c.author_display_name || 'U').charAt(0).toUpperCase()}
                    </div>
                    <span className="truncate max-w-[120px]" title={c.author_display_name}>
                      {c.author_display_name}
                    </span>
                  </div>
                </td>

                {/* Verbatim Text & Optional Translation */}
                <td className="px-4 py-3 text-slate-700 max-w-md">
                  <div className="text-slate-900 font-serif text-[13px] leading-relaxed break-words font-medium">
                    {c.original_text}
                  </div>
                  {c.translated_text ? (
                    <div className="mt-1.5 p-2 rounded-lg bg-emerald-50/70 border border-emerald-200/80 text-emerald-950 text-xs leading-relaxed" data-testid={`translation-${c.comment_id}`}>
                      <div className="flex items-center gap-1.5 text-[10px] font-bold tracking-wide uppercase text-emerald-800 mb-0.5">
                        <span className="bg-emerald-200/70 px-1 py-0.5 rounded text-[9px] font-mono not-italic text-emerald-900">En:</span>
                        <span>English Translation</span>
                      </div>
                      <div className="italic font-sans text-slate-800 break-words">
                        {c.translated_text}
                      </div>
                    </div>
                  ) : (
                    <div className="mt-1">
                      {c.detected_language === 'en' || c.detected_script?.toLowerCase() === 'english' || c.translation_status === 'NOT_NEEDED' ? (
                        <span className="text-[11px] text-slate-400 italic">
                          Already in English
                        </span>
                      ) : translatingCommentId === c.comment_id || c.translation_status === 'PENDING' ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-brand-600 font-medium">
                          <Loader2 className="w-3 h-3 animate-spin text-brand-600" />
                          <span>Translating...</span>
                        </span>
                      ) : c.translation_status === 'FAILED' ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-rose-500">
                          <span>Translation unavailable.</span>
                          {onTranslateComment && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                onTranslateComment(c);
                              }}
                              className="underline hover:text-rose-700 text-[10px] font-medium ml-1"
                            >
                              Retry
                            </button>
                          )}
                        </span>
                      ) : onTranslateComment ? (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onTranslateComment(c);
                          }}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium text-brand-700 bg-brand-50 border border-brand-200/70 hover:bg-brand-100 transition-colors"
                          title="Translate comment to English"
                        >
                          <Languages className="w-3 h-3 text-brand-600" />
                          <span>Translate</span>
                        </button>
                      ) : null}
                    </div>
                  )}
                </td>

                {/* Detected Script Badge */}
                <td className="px-4 py-3 align-top whitespace-nowrap">
                  <Badge variant="outline" size="sm">
                    {c.detected_script}
                  </Badge>
                </td>

                {/* 5-Class Sentiment Badge */}
                <td className="px-4 py-3 align-top whitespace-nowrap">
                  <SentimentBadge sentiment={c.sentiment} />
                </td>

                {/* Confidence */}
                <td className="px-4 py-3 align-top font-mono whitespace-nowrap text-slate-700">
                  {(c.confidence * 100).toFixed(1)}%
                </td>

                {/* Likes */}
                <td className="px-4 py-3 align-top font-mono text-slate-700 whitespace-nowrap">
                  <div className="flex items-center gap-1">
                    <ThumbsUp className="w-3 h-3 text-slate-400" />
                    <span>{c.like_count}</span>
                  </div>
                </td>

                {/* Details Button */}
                <td className="px-4 py-3 align-top text-right whitespace-nowrap">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onInspectComment(c);
                    }}
                    className="h-7 px-2 text-slate-500 hover:text-brand-600 opacity-80 group-hover:opacity-100"
                    title="Inspect comment details and model probabilities breakdown"
                  >
                    <Eye className="w-3.5 h-3.5 mr-1" />
                    <span>Inspect</span>
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
        <div>
          Showing {startIndex} to {endIndex} of {totalFiltered} comments
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage <= 1}
            onClick={() => onPageChange(Math.max(currentPage - 1, 1))}
          >
            <ChevronLeft className="w-3.5 h-3.5 mr-1" />
            Previous
          </Button>
          <span className="px-2 font-medium">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage >= totalPages}
            onClick={() => onPageChange(Math.min(currentPage + 1, totalPages))}
          >
            Next
            <ChevronRight className="w-3.5 h-3.5 ml-1" />
          </Button>
        </div>
      </div>
    </div>
  );
};
