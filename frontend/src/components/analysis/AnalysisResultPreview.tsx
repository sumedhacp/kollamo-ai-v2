import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Video,
  Eye,
  BarChart3,
  RefreshCw,
  MessageSquare,
  Cpu,
  ChevronDown,
  ChevronUp,
  ThumbsUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AnalysisResult, SentimentClassFive, SentimentCounts } from '@/services/api/types';

interface AnalysisResultPreviewProps {
  jobId: string;
  result: AnalysisResult;
  onReset: () => void;
}

export const AnalysisResultPreview: React.FC<AnalysisResultPreviewProps> = ({
  jobId,
  result,
  onReset,
}) => {
  const navigate = useNavigate();
  const [showAllComments, setShowAllComments] = useState(false);

  const comments = result.analysis?.comments || result.comments || [];
  const totalComments = result.total_comments ?? result.analysis?.returned_comment_count ?? comments.length;
  const processedComments = result.processed_comments ?? result.analysis?.returned_comment_count ?? comments.length;
  const video = result.video;
  const modelName = result.model?.name || result.model_name;
  const modelVersion = result.model?.version || result.model_version;

  const sentimentCounts: SentimentCounts = result.analysis?.sentiment_counts || result.sentiment_counts || {
    Positive: comments.filter((c) => c.sentiment === 'Positive').length,
    Negative: comments.filter((c) => c.sentiment === 'Negative').length,
    Neutral: comments.filter((c) => c.sentiment === 'Neutral').length,
    Mixed: comments.filter((c) => c.sentiment === 'Mixed').length,
    Unsupported: comments.filter((c) => c.sentiment === 'Unsupported').length,
  };

  const getSentimentBadge = (sentiment: SentimentClassFive) => {
    switch (sentiment) {
      case 'Positive':
        return (
          <Badge variant="default" size="sm" className="bg-emerald-600 text-white">
            Positive
          </Badge>
        );
      case 'Negative':
        return (
          <Badge variant="negative" size="sm">
            Negative
          </Badge>
        );
      case 'Neutral':
        return (
          <Badge variant="secondary" size="sm" className="bg-slate-100 text-slate-700 border-slate-300">
            Neutral
          </Badge>
        );
      case 'Mixed':
        return (
          <Badge variant="secondary" size="sm" className="bg-amber-100 text-amber-800 border-amber-300">
            Mixed
          </Badge>
        );
      case 'Unsupported':
        return (
          <Badge variant="secondary" size="sm" className="bg-purple-100 text-purple-800 border-purple-300">
            Unsupported
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary" size="sm">
            {sentiment}
          </Badge>
        );
    }
  };

  const displayedComments = showAllComments ? comments : comments.slice(0, 10);

  return (
    <div className="space-y-6" data-testid="analysis-result-preview">
      {/* Video Metadata Card */}
      <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm space-y-3">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-rose-50 flex items-center justify-center flex-shrink-0 text-rose-600">
            <Video className="w-5 h-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="text-base font-semibold text-slate-900 leading-tight">
              {video.title}
            </h3>
            <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs text-slate-500">
              <span className="font-medium text-slate-700">{video.channel_title}</span>
              {video.view_count !== undefined && video.view_count !== null && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Eye className="w-3.5 h-3.5 text-slate-400" />
                    {Number(video.view_count).toLocaleString()} views
                  </span>
                </>
              )}
              <span>•</span>
              <span className="flex items-center gap-1">
                <MessageSquare className="w-3.5 h-3.5 text-slate-400" />
                {processedComments} of {totalComments} comments analyzed
              </span>
            </div>
          </div>
        </div>

        {/* Model Meta Footer */}
        {(modelName || modelVersion) && (
          <div className="pt-2.5 border-t border-slate-100 flex items-center gap-2 text-xs text-slate-500">
            <Cpu className="w-3.5 h-3.5 text-brand-600" />
            <span>
              Model: <span className="font-mono text-slate-700">{modelName || 'kollamo-muril-5class'}</span>
              {modelVersion && ` (${modelVersion})`}
            </span>
          </div>
        )}
      </div>

      {/* Sentiment Counts Summary (Section 11, 34) */}
      <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm space-y-3">
        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Sentiment Distribution Summary
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-center">
            <div className="text-xs font-medium text-emerald-800">Positive</div>
            <div className="text-lg font-bold text-emerald-900 mt-0.5">{sentimentCounts.Positive}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-center">
            <div className="text-xs font-medium text-rose-800">Negative</div>
            <div className="text-lg font-bold text-rose-900 mt-0.5">{sentimentCounts.Negative}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
            <div className="text-xs font-medium text-slate-700">Neutral</div>
            <div className="text-lg font-bold text-slate-900 mt-0.5">{sentimentCounts.Neutral}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-center">
            <div className="text-xs font-medium text-amber-800">Mixed</div>
            <div className="text-lg font-bold text-amber-900 mt-0.5">{sentimentCounts.Mixed}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-purple-50 border border-purple-200 text-center col-span-2 sm:col-span-1">
            <div className="text-xs font-medium text-purple-800">Unsupported</div>
            <div className="text-lg font-bold text-purple-900 mt-0.5">{sentimentCounts.Unsupported}</div>
          </div>
        </div>
      </div>

      {/* Primary Action Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Button
          size="lg"
          className="w-full bg-emerald-600 hover:bg-emerald-700"
          onClick={() => navigate(`/dashboard?job_id=${encodeURIComponent(jobId)}`)}
        >
          <BarChart3 className="w-4 h-4 mr-2" />
          View Audience Dashboard
        </Button>
        <Button
          variant="outline"
          size="lg"
          className="w-full"
          onClick={onReset}
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Analyze Another Video
        </Button>
      </div>

      {/* Comment Predictions Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <span>Classified Comments Sample</span>
            <span className="text-xs font-normal text-slate-500">
              ({comments.length} results)
            </span>
          </h4>
        </div>

        {comments.length === 0 ? (
          <div className="p-6 text-center rounded-xl border border-dashed border-slate-200 bg-slate-50 text-xs text-slate-500">
            No comments were available for this video.
          </div>
        ) : (
          <div className="space-y-2.5">
            {displayedComments.map((comment) => (
              <div
                key={comment.comment_id}
                className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-xs space-y-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 truncate max-w-[240px]">
                    <span className="text-xs font-medium text-slate-700 truncate">
                      {comment.author_display_name || comment.author_name || 'Anonymous User'}
                    </span>
                    {comment.like_count > 0 && (
                      <span className="flex items-center gap-0.5 text-[10px] text-slate-400 font-medium">
                        <ThumbsUp className="w-2.5 h-2.5" />
                        {comment.like_count}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {getSentimentBadge(comment.sentiment)}
                    <span className="text-[11px] font-mono text-slate-500" title="Model confidence">
                      {(comment.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Safe plain text comment rendering (NO dangerouslySetInnerHTML) */}
                <p className="text-xs text-slate-800 leading-relaxed whitespace-pre-wrap break-words">
                  {comment.text}
                </p>

                {/* Model Probabilities Breakdown */}
                {comment.probabilities && (
                  <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] text-slate-500">
                    <span className="font-semibold text-slate-600">Model confidence:</span>
                    {Object.entries(comment.probabilities).map(([cls, prob]) => (
                      <span key={cls}>
                        {cls}: {(prob * 100).toFixed(1)}%
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {comments.length > 10 && (
              <div className="text-center pt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAllComments(!showAllComments)}
                  className="text-xs text-brand-600 hover:text-brand-800"
                >
                  {showAllComments ? (
                    <>
                      <ChevronUp className="w-3.5 h-3.5 mr-1" />
                      Show Less
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-3.5 h-3.5 mr-1" />
                      Show All {comments.length} Comments
                    </>
                  )}
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
