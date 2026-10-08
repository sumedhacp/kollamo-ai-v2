import React from 'react';
import {
  Video,
  Eye,
  ThumbsUp,
  MessageSquare,
  Calendar,
  ExternalLink,
  Cpu,
  Clock,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import {
  AnalysisVideo,
  AnalysisModelInfo,
  AnalysisProcessingInfo,
} from '@/services/api/types';

interface VideoOverviewProps {
  video: AnalysisVideo;
  model?: AnalysisModelInfo | null;
  modelName?: string | null;
  modelVersion?: string | null;
  processing?: AnalysisProcessingInfo | null;
}

export const VideoOverview: React.FC<VideoOverviewProps> = ({
  video,
  model,
  modelName,
  modelVersion,
  processing,
}) => {
  const publishedDate = video.published_at
    ? new Date(video.published_at).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : null;

  const availableComments =
    video.comment_count_available ?? video.comment_count ?? null;

  const displayModelName = model?.name || modelName || 'kollamo-muril-5class';
  const displayModelVersion = model?.version || modelVersion || 'v1';

  const processingTimeMs = processing?.processing_time_ms ?? null;
  const processingTimeDisplay =
    processingTimeMs !== null
      ? processingTimeMs >= 1000
        ? `${(processingTimeMs / 1000).toFixed(2)}s`
        : `${Math.round(processingTimeMs)}ms`
      : null;

  const youtubeUrl = `https://www.youtube.com/watch?v=${encodeURIComponent(
    video.video_id
  )}`;

  return (
    <Card className="overflow-hidden border-slate-200 shadow-sm" data-testid="video-overview">
      <CardContent className="p-5 sm:p-6 space-y-4">
        {/* Header with Title and YouTube Link */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="flex items-start gap-3.5 min-w-0">
            <div className="w-11 h-11 rounded-xl bg-rose-50 border border-rose-100 flex items-center justify-center flex-shrink-0 text-rose-600 shadow-xs">
              <Video className="w-5 h-5" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-semibold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-md border border-rose-100">
                  YouTube Analysis Target
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  ID: {video.video_id}
                </span>
              </div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight mt-1 leading-snug">
                {video.title}
              </h2>
              <p className="text-sm font-medium text-slate-600 mt-0.5">
                {video.channel_title ? (
                  <span>Channel: <strong className="text-slate-800">{video.channel_title}</strong></span>
                ) : (
                  <span className="text-slate-400 italic">Channel unavailable</span>
                )}
              </p>
            </div>
          </div>

          <a
            href={youtubeUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 bg-slate-50 border border-slate-200 hover:bg-slate-100 transition-colors self-start sm:self-auto flex-shrink-0"
            aria-label={`Open YouTube video ${video.title} in new tab`}
          >
            <span>Watch Video</span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
          </a>
        </div>

        {/* Video Statistics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-100 text-xs">
          {/* Published At */}
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-150/70 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-medium">Published</span>
            </div>
            <div className="font-semibold text-slate-800">
              {publishedDate || <span className="text-slate-400 italic">Unavailable</span>}
            </div>
          </div>

          {/* Views */}
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-150/70 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500">
              <Eye className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-medium">Total Views</span>
            </div>
            <div className="font-semibold text-slate-800">
              {video.view_count !== null && video.view_count !== undefined ? (
                Number(video.view_count).toLocaleString()
              ) : (
                <span className="text-slate-400 italic">Unavailable</span>
              )}
            </div>
          </div>

          {/* Likes */}
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-150/70 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500">
              <ThumbsUp className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-medium">Video Likes</span>
            </div>
            <div className="font-semibold text-slate-800">
              {video.like_count !== null && video.like_count !== undefined ? (
                Number(video.like_count).toLocaleString()
              ) : (
                <span className="text-slate-400 italic">Unavailable</span>
              )}
            </div>
          </div>

          {/* Comments Available on YouTube */}
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-150/70 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-500">
              <MessageSquare className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-medium">Reported Comments</span>
            </div>
            <div className="font-semibold text-slate-800">
              {availableComments !== null && availableComments !== undefined ? (
                Number(availableComments).toLocaleString()
              ) : (
                <span className="text-slate-400 italic">Unavailable</span>
              )}
            </div>
          </div>
        </div>

        {/* Model & Processing Telemetry Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <Cpu className="w-3.5 h-3.5 text-brand-600" />
            <span>
              Engine: <strong className="font-mono text-slate-700">{displayModelName}</strong> ({displayModelVersion})
            </span>
          </div>

          {processingTimeDisplay && (
            <div className="flex items-center gap-1.5 text-slate-500">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>Processing Time: <strong className="font-mono text-slate-700">{processingTimeDisplay}</strong></span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
