import { useState, useEffect, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  BarChart3,
  ThumbsUp,
  Search,
  Layers,
  ArrowRight,
  ExternalLink,
  Sparkles,
  TrendingUp,
  FileSpreadsheet,
  FileCode,
  Tag,
  Loader2,
  Languages,
  FileText,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Alert } from '@/components/ui/alert';
import { SentimentClass, AnalysisJob, CommentItem } from '@/types';
import { api, ApiError, getJobV1, AnalysisResult } from '@/services/api';
import { DEMO_SAMPLE_JOB } from '@/data/sampleJob';
import { generateAudienceIntelligencePdf, getAnalysisReportFilename } from '@/utils/pdfGenerator';
import {
  VideoOverview,
  MetricCards,
  SentimentDistribution,
  CommentsTable,
  CommentDetailsModal,
} from '@/components/dashboard';

export const Dashboard: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const jobId = searchParams.get('job_id');

  const [activeTab, setActiveTab] = useState<'all' | SentimentClass>('all');
  const [activeScriptFilter, setActiveScriptFilter] = useState<'all' | 'Malayalam' | 'Latin' | 'Mixed'>('all');
  const [activeChartTab, setActiveChartTab] = useState<'distribution' | 'engagement' | 'scripts'>('distribution');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'likes' | 'confidence' | 'newest'>('likes');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const [inspectedComment, setInspectedComment] = useState<CommentItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [showSkeleton, setShowSkeleton] = useState(false);
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Adapter function to transform Phase 6 AnalysisResult into dashboard state
  const adaptAnalysisResultToJob = (id: string, result: AnalysisResult): AnalysisJob => {
    const commentsList = result.analysis?.comments || result.comments || [];
    const totalAnalyzed =
      result.total_comments ?? result.analysis?.returned_comment_count ?? commentsList.length;

    const counts = result.analysis?.sentiment_counts || result.sentiment_counts || {
      Positive: commentsList.filter((c) => c.sentiment === 'Positive').length,
      Negative: commentsList.filter((c) => c.sentiment === 'Negative').length,
      Neutral: commentsList.filter((c) => c.sentiment === 'Neutral').length,
      Mixed: commentsList.filter((c) => c.sentiment === 'Mixed').length,
      Unsupported: commentsList.filter((c) => c.sentiment === 'Unsupported').length,
    };

    const posCount = (counts as any).Positive ?? (counts as any).positive ?? 0;
    const negCount = (counts as any).Negative ?? (counts as any).negative ?? 0;
    const neuCount = (counts as any).Neutral ?? (counts as any).neutral ?? 0;
    const mixCount = (counts as any).Mixed ?? (counts as any).mixed ?? 0;
    const unsCount = (counts as any).Unsupported ?? (counts as any).unsupported ?? 0;

    const calcPct = (cnt: number) => (totalAnalyzed > 0 ? (cnt / totalAnalyzed) * 100 : 0);

    const mappedComments = commentsList.map((c) => ({
      comment_id: c.comment_id,
      author_display_name: c.author_display_name || c.author_name || 'Anonymous User',
      published_at: c.published_at || '',
      like_count: c.like_count || 0,
      reply_count: 0,
      original_text: c.text,
      detected_language: (c as any).detected_language || 'ml',
      detected_script: (c as any).detected_script || 'Latin',
      sentiment: ((c.sentiment ? c.sentiment.toLowerCase() : 'neutral') as SentimentClass),
      confidence: c.confidence || 0.9,
      probabilities: c.probabilities,
      translated_text: (c as any).translated_text,
    }));

    return {
      job_id: id,
      status: 'completed',
      progress: 1.0,
      processed_comments: totalAnalyzed,
      total_comments: totalAnalyzed,
      created_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      video: {
        video_id: result.video.video_id,
        title: result.video.title,
        channel_title: result.video.channel_title || '',
        view_count: result.video.view_count || 0,
        thumbnail_url: result.video.thumbnail_url || '',
        published_at: result.video.published_at,
        like_count: result.video.like_count,
        comment_count: result.video.comment_count,
        comment_count_available: result.video.comment_count_available,
      },
      summary: {
        total_analyzed: totalAnalyzed,
        sentiment_counts: {
          positive: posCount,
          negative: negCount,
          neutral: neuCount,
          mixed: mixCount,
          unsupported: unsCount,
        },
        sentiment_percentages: {
          positive: calcPct(posCount),
          negative: calcPct(negCount),
          neutral: calcPct(neuCount),
          mixed: calcPct(mixCount),
          unsupported: calcPct(unsCount),
        },
        engagement_metrics: {
          total_likes: commentsList.reduce((acc, c) => acc + (c.like_count || 0), 0),
          average_likes_per_sentiment: {
            positive:
              posCount > 0
                ? commentsList
                    .filter((c) => c.sentiment === 'Positive')
                    .reduce((s, c) => s + (c.like_count || 0), 0) / posCount
                : 0,
            negative:
              negCount > 0
                ? commentsList
                    .filter((c) => c.sentiment === 'Negative')
                    .reduce((s, c) => s + (c.like_count || 0), 0) / negCount
                : 0,
            neutral:
              neuCount > 0
                ? commentsList
                    .filter((c) => c.sentiment === 'Neutral')
                    .reduce((s, c) => s + (c.like_count || 0), 0) / neuCount
                : 0,
            mixed:
              mixCount > 0
                ? commentsList
                    .filter((c) => c.sentiment === 'Mixed')
                    .reduce((s, c) => s + (c.like_count || 0), 0) / mixCount
                : 0,
            unsupported:
              unsCount > 0
                ? commentsList
                    .filter((c) => c.sentiment === 'Unsupported')
                    .reduce((s, c) => s + (c.like_count || 0), 0) / unsCount
                : 0,
          },
        },
      },
      comments: mappedComments,
      model: result.model,
      processing: result.processing,
      model_name: result.model_name || result.model?.name,
      model_version: result.model_version || result.model?.version,
    } as any;
  };

  // Load job data
  useEffect(() => {
    if (!jobId) {
      setJob(null);
      return;
    }

    if (jobId === 'demo-aavesham-2026-sample') {
      setJob(DEMO_SAMPLE_JOB);
      return;
    }

    let isMounted = true;
    setIsLoading(true);
    setFetchError(null);

    // Try Phase 6 getJobV1 (/api/v1/analysis/jobs/{job_id}) first
    getJobV1(jobId)
      .then((statusRes) => {
        if (!isMounted) return;
        if (statusRes.result) {
          setJob(adaptAnalysisResultToJob(jobId, statusRes.result));
        } else if ((statusRes as any).summary && (statusRes as any).video) {
          setJob(statusRes as any);
        } else if (statusRes.status === 'FAILED') {
          setFetchError(statusRes.error?.message || 'Analysis job failed');
        } else {
          // If in progress or empty result, try legacy endpoint
          api
            .getJobStatus(jobId)
            .then((legacyJob) => {
              if (isMounted) setJob(legacyJob);
            })
            .catch(() => {
              if (isMounted) setFetchError(`Job is currently ${statusRes.status.toLowerCase()}`);
            });
        }
      })
      .catch((_err: unknown) => {
        // Fallback to legacy getJobStatus
        api
          .getJobStatus(jobId)
          .then((data) => {
            if (isMounted) {
              setJob(data);
            }
          })
          .catch((err: unknown) => {
            if (isMounted) {
              const msg =
                err instanceof ApiError
                  ? `${err.code}: ${err.message}`
                  : err instanceof Error
                  ? err.message
                  : 'Failed to load analysis results';
              setFetchError(msg);
            }
          });
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [jobId]);

  const summary = job?.summary;
  const comments = job?.comments || [];

  // Net Sentiment Approval Index: (Positive - Negative)
  const netApprovalIndex = useMemo(() => {
    if (!summary) return 0;
    return Math.round(summary.sentiment_percentages.positive - summary.sentiment_percentages.negative);
  }, [summary]);

  // Linguistic script breakdown from comments
  const scriptBreakdown = useMemo(() => {
    if (!comments.length) {
      return { malayalam: 0, latin: 0, mixed: 0, unknown: 0 };
    }
    const counts = { malayalam: 0, latin: 0, mixed: 0, unknown: 0 };
    comments.forEach((c) => {
      const s = (c.detected_script || '').toLowerCase();
      if (s.includes('malayalam')) counts.malayalam++;
      else if (s.includes('latin')) counts.latin++;
      else if (s.includes('mixed')) counts.mixed++;
      else counts.unknown++;
    });
    const total = comments.length;
    return {
      malayalam: Math.round((counts.malayalam / total) * 100),
      latin: Math.round((counts.latin / total) * 100),
      mixed: Math.round((counts.mixed / total) * 100),
      unknown: Math.round((counts.unknown / total) * 100),
    };
  }, [comments]);

  // Discussion theme keywords
  const discussionTopics = useMemo(() => {
    return [
      { label: 'BGM / Music', term: 'bgm' },
      { label: 'Direction', term: 'direction' },
      { label: 'FaFa / Acting', term: 'fafa' },
      { label: 'First Half', term: 'first half' },
      { label: 'Second Half', term: 'second half' },
      { label: 'Theatres / Hit', term: 'theatre' },
      { label: 'Story', term: 'story' },
      { label: 'Comedy', term: 'fun' },
    ];
  }, []);

  // Filter and sort comments
  const filteredComments = useMemo(() => {
    let result = [...comments];

    // Filter by sentiment
    if (activeTab !== 'all') {
      result = result.filter((c) => c.sentiment === activeTab);
    }

    // Filter by script
    if (activeScriptFilter !== 'all') {
      result = result.filter((c) =>
        (c.detected_script || '').toLowerCase().includes(activeScriptFilter.toLowerCase())
      );
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      result = result.filter(
        (c) =>
          c.original_text.toLowerCase().includes(q) ||
          c.author_display_name.toLowerCase().includes(q) ||
          (c.translated_text && c.translated_text.toLowerCase().includes(q))
      );
    }

    // Sort comments
    result.sort((a, b) => {
      if (sortBy === 'likes') return (b.like_count || 0) - (a.like_count || 0);
      if (sortBy === 'confidence') return (b.confidence || 0) - (a.confidence || 0);
      if (sortBy === 'newest') {
        const da = a.published_at ? new Date(a.published_at).getTime() : 0;
        const db = b.published_at ? new Date(b.published_at).getTime() : 0;
        return db - da;
      }
      return 0;
    });

    return result;
  }, [comments, activeTab, activeScriptFilter, searchQuery, sortBy]);

  // Paginated slice
  const paginatedComments = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredComments.slice(start, start + pageSize);
  }, [filteredComments, currentPage]);

  const totalPages = Math.max(Math.ceil(filteredComments.length / pageSize), 1);

  // Export JSON
  const handleExportJSON = () => {
    if (!job) return;
    const blob = new Blob([JSON.stringify(job, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kollamo-audience-data-${job.job_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Export CSV
  const handleExportCSV = () => {
    if (!job || !comments.length) return;
    const headers = ['Comment ID', 'Author', 'Sentiment', 'Confidence', 'Script', 'Likes', 'Original Text', 'English Translation'];
    const rows = comments.map((c) => [
      `"${c.comment_id}"`,
      `"${(c.author_display_name || '').replace(/"/g, '""')}"`,
      `"${c.sentiment}"`,
      `"${(c.confidence * 100).toFixed(1)}%"`,
      `"${c.detected_script}"`,
      c.like_count || 0,
      `"${(c.original_text || '').replace(/"/g, '""')}"`,
      `"${(c.translated_text || '').replace(/"/g, '""')}"`,
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kollamo-comments-${job.job_id}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [translatingCommentId, setTranslatingCommentId] = useState<string | null>(null);
  const [pdfNotice, setPdfNotice] = useState<string | null>(null);

  // Export PDF Report (Client jsPDF with Server Fallback)
  const handleExportPDF = async () => {
    if (!job) return;
    setIsGeneratingPdf(true);
    setPdfNotice(null);
    const videoId = job.video?.video_id || (job as { video_id?: string }).video_id || job.job_id;
    const filename = getAnalysisReportFilename(videoId);
    try {
      const doc = generateAudienceIntelligencePdf(job, {
        includeMethodology: true,
        includeComments: true,
        maxComments: 15,
      });
      doc.save(filename);
      setPdfNotice('Academic PDF report compiled and downloaded successfully!');
      setTimeout(() => setPdfNotice(null), 4000);
    } catch (err) {
      console.error('Client PDF export failed, falling back to server compilation:', err);
      try {
        const blob = await api.downloadJobPdf(job.job_id);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        setPdfNotice('Server-rendered PDF report downloaded successfully!');
        setTimeout(() => setPdfNotice(null), 4000);
      } catch (serverErr) {
        console.error('Server PDF download failed:', serverErr);
        setPdfNotice('Unable to generate the PDF report. Please try again.');
        setTimeout(() => setPdfNotice(null), 4000);
      }
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  // Trigger individual comment translation on demand
  const handleTranslateSingleComment = async (commentToTranslate: CommentItem) => {
    if (!job || !commentToTranslate) return;
    if (commentToTranslate.translated_text) return;

    if (
      commentToTranslate.detected_language === 'en' ||
      commentToTranslate.detected_script?.toLowerCase() === 'english' ||
      commentToTranslate.translation_status === 'NOT_NEEDED'
    ) {
      return;
    }

    setTranslatingCommentId(commentToTranslate.comment_id);
    try {
      const res = await api.translateText(commentToTranslate.original_text, 'auto', 'en');
      const isEnglish = res.status === 'NOT_NEEDED';
      const newStatus = isEnglish ? 'NOT_NEEDED' : 'COMPLETED';
      const translated = isEnglish ? undefined : res.translated_text;

      setJob((prevJob) => {
        if (!prevJob || !prevJob.comments) return prevJob;
        return {
          ...prevJob,
          comments: prevJob.comments.map((c) =>
            c.comment_id === commentToTranslate.comment_id
              ? {
                  ...c,
                  translated_text: translated,
                  translation_status: newStatus,
                  translation_error: undefined,
                }
              : c
          ),
        };
      });

      setInspectedComment((prev) => {
        if (!prev || prev.comment_id !== commentToTranslate.comment_id) return prev;
        return {
          ...prev,
          translated_text: translated,
          translation_status: newStatus,
          translation_error: undefined,
        };
      });
    } catch (err) {
      console.error('Individual comment translation failed:', err);
      setJob((prevJob) => {
        if (!prevJob || !prevJob.comments) return prevJob;
        return {
          ...prevJob,
          comments: prevJob.comments.map((c) =>
            c.comment_id === commentToTranslate.comment_id
              ? {
                  ...c,
                  translation_status: 'FAILED',
                  translation_error: 'Translation unavailable.',
                }
              : c
          ),
        };
      });
      setInspectedComment((prev) => {
        if (!prev || prev.comment_id !== commentToTranslate.comment_id) return prev;
        return {
          ...prev,
          translation_status: 'FAILED',
          translation_error: 'Translation unavailable.',
        };
      });
    } finally {
      setTranslatingCommentId(null);
    }
  };

  // Trigger translation of comments in this job
  const handleTranslateComments = async () => {
    if (!job) return;
    if (job.job_id === 'demo-aavesham-2026-sample') {
      setPdfNotice('Demo dataset already includes pre-translated English mappings.');
      setTimeout(() => setPdfNotice(null), 3000);
      return;
    }
    setIsTranslating(true);
    try {
      await api.translateJobComments(job.job_id, 25);
      const updated = await api.getJobStatus(job.job_id);
      setJob(updated);
      setPdfNotice('Comment translations updated successfully!');
      setTimeout(() => setPdfNotice(null), 3000);
    } catch (err) {
      console.error('Translation error:', err);
      setPdfNotice('Comment translation encountered an issue.');
    } finally {
      setIsTranslating(false);
    }
  };

  const sentimentChartData = useMemo(() => {
    if (!summary) return [];
    return [
      { label: 'Positive', pct: summary.sentiment_percentages.positive, count: summary.sentiment_counts.positive, color: 'bg-emerald-500', barHeight: `${Math.max(summary.sentiment_percentages.positive, 4)}%` },
      { label: 'Negative', pct: summary.sentiment_percentages.negative, count: summary.sentiment_counts.negative, color: 'bg-rose-500', barHeight: `${Math.max(summary.sentiment_percentages.negative, 4)}%` },
      { label: 'Neutral', pct: summary.sentiment_percentages.neutral, count: summary.sentiment_counts.neutral, color: 'bg-slate-400', barHeight: `${Math.max(summary.sentiment_percentages.neutral, 4)}%` },
      { label: 'Mixed', pct: summary.sentiment_percentages.mixed, count: summary.sentiment_counts.mixed, color: 'bg-amber-500', barHeight: `${Math.max(summary.sentiment_percentages.mixed, 4)}%` },
      { label: 'Unsupported', pct: summary.sentiment_percentages.unsupported, count: summary.sentiment_counts.unsupported, color: 'bg-zinc-400', barHeight: `${Math.max(summary.sentiment_percentages.unsupported, 4)}%` },
    ];
  }, [summary]);

  const engagementChartData = useMemo(() => {
    if (!summary) return [];
    const avgLikes = summary.engagement_metrics.average_likes_per_sentiment;
    const maxLikes = Math.max(...Object.values(avgLikes), 1);
    return [
      { label: 'Positive', avg: avgLikes.positive, pctHeight: `${Math.max((avgLikes.positive / maxLikes) * 100, 6)}%`, color: 'bg-emerald-400' },
      { label: 'Negative', avg: avgLikes.negative, pctHeight: `${Math.max((avgLikes.negative / maxLikes) * 100, 6)}%`, color: 'bg-rose-400' },
      { label: 'Neutral', avg: avgLikes.neutral, pctHeight: `${Math.max((avgLikes.neutral / maxLikes) * 100, 6)}%`, color: 'bg-slate-400' },
      { label: 'Mixed', avg: avgLikes.mixed, pctHeight: `${Math.max((avgLikes.mixed / maxLikes) * 100, 6)}%`, color: 'bg-amber-400' },
      { label: 'Unsupported', avg: avgLikes.unsupported, pctHeight: `${Math.max((avgLikes.unsupported / maxLikes) * 100, 6)}%`, color: 'bg-zinc-400' },
    ];
  }, [summary]);

  const isDisplayingSkeleton = showSkeleton || isLoading;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Dashboard Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="secondary" className="gap-1">
              <BarChart3 className="w-3.5 h-3.5 text-brand-600" />
              Audience Intelligence
            </Badge>
            <span className="text-xs text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-medium border border-emerald-200">
              {job ? `Job: ${job.job_id.slice(0, 8)}...` : 'Phase 7 Intelligence'}
            </span>
            {job?.video && (
              <a
                href={`https://www.youtube.com/watch?v=${job.video.video_id}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-rose-600 transition-colors"
              >
                <span>YouTube</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
            Audience Analytics Dashboard
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            {job?.video
              ? `${Number(job.video.view_count || 0).toLocaleString()} views • ${comments.length} comments classified`
              : 'Multilingual sentiment distributions, engagement metrics, and granular comment intelligence.'}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSkeleton(!showSkeleton)}
            title="Toggle between skeleton loading mode and active data state"
          >
            <Layers className="w-3.5 h-3.5 mr-1.5" />
            {showSkeleton ? 'Show Live View' : 'Preview Skeleton State'}
          </Button>

          {job && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportCSV}
                title="Export classified comments as CSV"
              >
                <FileSpreadsheet className="w-3.5 h-3.5 mr-1.5 text-emerald-600" />
                CSV
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportJSON}
                title="Export entire audience intelligence payload as JSON"
              >
                <FileCode className="w-3.5 h-3.5 mr-1.5 text-brand-600" />
                JSON
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleTranslateComments}
                disabled={isTranslating}
                title="Translate regional and Manglish comments for this analysis job"
              >
                {isTranslating ? (
                  <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin text-brand-600" />
                ) : (
                  <Languages className="w-3.5 h-3.5 mr-1.5 text-brand-600" />
                )}
                Translate Comments
              </Button>
            </>
          )}

          <Button
            variant="primary"
            size="sm"
            onClick={handleExportPDF}
            disabled={!job || isGeneratingPdf}
            className="bg-brand-600 hover:bg-brand-700 text-white shadow-sm"
            title="Download publication-quality multi-page PDF audience intelligence report"
          >
            {isGeneratingPdf ? (
              <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
            ) : (
              <FileText className="w-3.5 h-3.5 mr-1.5" />
            )}
            {isGeneratingPdf ? 'Generating PDF...' : 'Export PDF Report'}
          </Button>
        </div>
      </div>

      {/* PDF Generation or Action Feedback Alert */}
      {pdfNotice && (
        <Alert variant="info" title="Report Notification">
          {pdfNotice}
        </Alert>
      )}

      {/* Fetch Error Alert */}
      {fetchError && (
        <Alert variant="error" title="Job Data Fetch Failed">
          {fetchError}
        </Alert>
      )}

      {/* Loading Skeleton */}
      {isDisplayingSkeleton && (
        <div className="space-y-4" data-testid="dashboard-loading-skeleton">
          <Skeleton className="h-44 w-full rounded-xl" />
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-xl" />
            ))}
          </div>
        </div>
      )}

      {/* Video Overview (Phase 7) */}
      {job?.video && !isDisplayingSkeleton && (
        <VideoOverview
          video={job.video as any}
          model={(job as any).model}
          modelName={(job as any).model_name}
          modelVersion={(job as any).model_version}
          processing={(job as any).processing}
        />
      )}

      {/* Metric Cards (Phase 7) */}
      {summary && !isDisplayingSkeleton && (
        <MetricCards
          totalAnalyzed={summary.total_analyzed}
          sentimentCounts={{
            Positive: summary.sentiment_counts.positive,
            Negative: summary.sentiment_counts.negative,
            Neutral: summary.sentiment_counts.neutral,
            Mixed: summary.sentiment_counts.mixed,
            Unsupported: summary.sentiment_counts.unsupported,
          }}
        />
      )}

      {/* Net Sentiment Approval Index Banner */}
      {summary && !isDisplayingSkeleton && (
        <div className="p-4 rounded-xl border border-brand-200 bg-gradient-to-r from-brand-50/60 to-white flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-lg bg-brand-100 text-brand-700 mt-0.5">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-slate-900">
                  Audience Net Approval Index:
                </h3>
                <span
                  className={`text-sm font-mono font-bold px-2 py-0.5 rounded-full ${
                    netApprovalIndex >= 0
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  {netApprovalIndex >= 0 ? `+${netApprovalIndex}%` : `${netApprovalIndex}%`}
                </span>
                <Badge variant="outline" size="sm" className="bg-white text-[11px]">
                  {netApprovalIndex >= 50
                    ? 'Overwhelmingly Positive'
                    : netApprovalIndex >= 15
                    ? 'Predominantly Favorable'
                    : netApprovalIndex >= -15
                    ? 'Mixed / Divided Consensus'
                    : 'Predominantly Critical'}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                Calculated as the spread between positive ({summary.sentiment_percentages.positive.toFixed(1)}%) and negative ({summary.sentiment_percentages.negative.toFixed(1)}%) reactions across all classified comments.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono text-slate-600 border-t md:border-t-0 md:border-l border-brand-200/60 pt-3 md:pt-0 md:pl-5">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-sans">Total Likes</span>
              <span className="font-bold text-slate-900 text-base">
                {summary.engagement_metrics.total_likes.toLocaleString()}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-sans">Avg Likes / Comment</span>
              <span className="font-bold text-slate-900 text-base">
                {(summary.engagement_metrics.total_likes / Math.max(summary.total_analyzed, 1)).toFixed(1)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Five-Class Sentiment Distribution Analytics (Phase 7) */}
      {summary && !isDisplayingSkeleton && (
        <SentimentDistribution
          sentimentCounts={{
            Positive: summary.sentiment_counts.positive,
            Negative: summary.sentiment_counts.negative,
            Neutral: summary.sentiment_counts.neutral,
            Mixed: summary.sentiment_counts.mixed,
            Unsupported: summary.sentiment_counts.unsupported,
          }}
          totalAnalyzed={summary.total_analyzed}
          netApprovalIndex={netApprovalIndex}
          activeFilter={activeTab === 'all' ? null : activeTab}
          onSentimentClick={(s) => setActiveTab(s.toLowerCase() as SentimentClass)}
        />
      )}

      {/* 2. Visual Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Distribution Chart Container */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-brand-600" />
                Sentiment Distribution
              </CardTitle>
              <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg text-[11px]">
                <button
                  type="button"
                  onClick={() => setActiveChartTab('distribution')}
                  className={`px-2 py-0.5 rounded font-medium transition-all ${
                    activeChartTab === 'distribution'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  5-Class Share
                </button>
                <button
                  type="button"
                  onClick={() => setActiveChartTab('scripts')}
                  className={`px-2 py-0.5 rounded font-medium transition-all ${
                    activeChartTab === 'scripts'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Scripts
                </button>
              </div>
            </div>
            <CardDescription>
              {activeChartTab === 'distribution'
                ? 'Proportion of positive, negative, neutral, mixed, and unsupported sentiments.'
                : 'Linguistic breakdown between Malayalam script, Latin script (Manglish), and Code-Mixed.'}
            </CardDescription>
          </CardHeader>
          <CardContent className="h-64 flex flex-col items-center justify-center">
            {isDisplayingSkeleton ? (
              <div className="w-full h-full flex flex-col justify-end space-y-3 p-4">
                <div className="flex items-end justify-between h-40 gap-4">
                  <Skeleton className="w-1/5 h-3/4 rounded-t-lg" />
                  <Skeleton className="w-1/5 h-1/2 rounded-t-lg" />
                  <Skeleton className="w-1/5 h-2/3 rounded-t-lg" />
                  <Skeleton className="w-1/5 h-1/3 rounded-t-lg" />
                  <Skeleton className="w-1/5 h-1/4 rounded-t-lg" />
                </div>
                <div className="flex justify-between">
                  <Skeleton className="h-3 w-12" />
                  <Skeleton className="h-3 w-12" />
                  <Skeleton className="h-3 w-12" />
                  <Skeleton className="h-3 w-12" />
                  <Skeleton className="h-3 w-12" />
                </div>
              </div>
            ) : summary ? (
              activeChartTab === 'distribution' ? (
                <div className="w-full h-full flex flex-col justify-end p-4">
                  <div className="flex items-end justify-between h-40 gap-4">
                    {sentimentChartData.map((d) => (
                      <div key={d.label} className="w-1/5 flex flex-col items-center h-full justify-end">
                        <span className="text-[11px] font-mono font-medium text-slate-700 mb-1">
                          {d.pct.toFixed(1)}%
                        </span>
                        <div
                          className={`w-full rounded-t-lg transition-all duration-500 ${d.color}`}
                          style={{ height: d.barHeight }}
                        />
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between pt-2 border-t border-slate-100 mt-2 text-[11px] text-slate-600 font-medium">
                    {sentimentChartData.map((d) => (
                      <span key={d.label} className="w-1/5 text-center truncate">
                        {d.label}
                      </span>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="w-full h-full flex flex-col justify-center p-4 space-y-3">
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-slate-700">Malayalam Script</span>
                      <span className="font-mono text-slate-900">{scriptBreakdown.malayalam}%</span>
                    </div>
                    <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-brand-600 rounded-full" style={{ width: `${scriptBreakdown.malayalam}%` }} />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-slate-700">Latin Script (Manglish / English)</span>
                      <span className="font-mono text-slate-900">{scriptBreakdown.latin}%</span>
                    </div>
                    <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${scriptBreakdown.latin}%` }} />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-slate-700">Code-Mixed Comments</span>
                      <span className="font-mono text-slate-900">{scriptBreakdown.mixed}%</span>
                    </div>
                    <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-amber-500 rounded-full" style={{ width: `${scriptBreakdown.mixed}%` }} />
                    </div>
                  </div>
                </div>
              )
            ) : (
              <EmptyState
                icon={<BarChart3 className="w-8 h-8 text-slate-400" />}
                title="No Sentiment Data Available"
                description="Run a video analysis from the Analyze page to populate sentiment distribution metrics."
              />
            )}
          </CardContent>
        </Card>

        {/* Engagement Correlation Chart Container */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center justify-between">
              <span className="flex items-center gap-2">
                <ThumbsUp className="w-4 h-4 text-emerald-600" />
                Sentiment vs. Engagement
              </span>
              <Badge variant="outline" size="sm">Average Likes</Badge>
            </CardTitle>
            <CardDescription>
              Correlation between comment polarity and community likes.
            </CardDescription>
          </CardHeader>
          <CardContent className="h-64 flex flex-col items-center justify-center">
            {isDisplayingSkeleton ? (
              <div className="w-full h-full flex flex-col justify-end space-y-3 p-4">
                <div className="flex items-end justify-between h-40 gap-4">
                  <Skeleton className="w-1/5 h-2/3 rounded-t-lg bg-emerald-100" />
                  <Skeleton className="w-1/5 h-1/4 rounded-t-lg bg-rose-100" />
                  <Skeleton className="w-1/5 h-1/3 rounded-t-lg bg-slate-100" />
                  <Skeleton className="w-1/5 h-1/2 rounded-t-lg bg-amber-100" />
                  <Skeleton className="w-1/5 h-1/6 rounded-t-lg bg-zinc-100" />
                </div>
                <div className="flex justify-between">
                  <Skeleton className="h-3 w-12" />
                  <Skeleton className="h-3 w-12" />
                  <Skeleton className="h-3 w-12" />
                  <Skeleton className="h-3 w-12" />
                  <Skeleton className="h-3 w-12" />
                </div>
              </div>
            ) : summary ? (
              <div className="w-full h-full flex flex-col justify-end p-4">
                <div className="flex items-end justify-between h-40 gap-4">
                  {engagementChartData.map((d) => (
                    <div key={d.label} className="w-1/5 flex flex-col items-center h-full justify-end">
                      <span className="text-[11px] font-mono font-medium text-slate-700 mb-1">
                        {d.avg.toFixed(1)}
                      </span>
                      <div
                        className={`w-full rounded-t-lg transition-all duration-500 ${d.color}`}
                        style={{ height: d.pctHeight }}
                      />
                    </div>
                  ))}
                </div>
                <div className="flex justify-between pt-2 border-t border-slate-100 mt-2 text-[11px] text-slate-600 font-medium">
                  {engagementChartData.map((d) => (
                    <span key={d.label} className="w-1/5 text-center truncate">
                      {d.label}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <EmptyState
                icon={<ThumbsUp className="w-8 h-8 text-slate-400" />}
                title="No Engagement Data Available"
                description="Audience likes and engagement ratios will populate once comment data is fetched."
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Discussion Topics & Keyword Filters */}
      {comments.length > 0 && (
        <Card className="border-slate-200">
          <CardHeader className="py-3 px-5 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Tag className="w-4 h-4 text-brand-600" />
              <CardTitle className="text-xs uppercase tracking-wider text-slate-700">
                Key Discussion Themes & High-Frequency Topics
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-4 flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-500 mr-1">Filter by theme:</span>
            {discussionTopics.map((topic) => (
              <button
                key={topic.term}
                type="button"
                onClick={() => {
                  setSearchQuery(topic.term);
                  setCurrentPage(1);
                }}
                className={`text-xs px-2.5 py-1 rounded-lg border transition-all ${
                  searchQuery.toLowerCase() === topic.term
                    ? 'bg-brand-600 text-white border-brand-600'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                {topic.label}
              </button>
            ))}
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="text-xs text-rose-600 hover:text-rose-800 underline ml-2"
              >
                Clear Theme Filter
              </button>
            )}
          </CardContent>
        </Card>
      )}

      {/* 3. Granular Comments Table */}
      <Card>
        <CardHeader className="pb-4 border-b border-slate-100">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <span>Comments Intelligence Explorer</span>
                <Badge variant="outline" size="sm">
                  {filteredComments.length} {filteredComments.length === 1 ? 'Comment' : 'Comments'}
                </Badge>
              </CardTitle>
              <CardDescription>
                Detailed comment-level classifications, script recognition, and English translations.
              </CardDescription>
            </div>

            {/* Filter toolbar */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Search input */}
              <div className="w-60">
                <Input
                  placeholder="Search comments or author..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setCurrentPage(1);
                  }}
                  leftIcon={<Search className="w-3.5 h-3.5 text-slate-400" />}
                  className="h-9 text-xs"
                />
              </div>

              {/* Script filter */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs">
                {(['all', 'Malayalam', 'Latin', 'Mixed'] as const).map((scriptKey) => (
                  <button
                    key={scriptKey}
                    type="button"
                    onClick={() => {
                      setActiveScriptFilter(scriptKey);
                      setCurrentPage(1);
                    }}
                    className={`px-2 py-1 rounded-md font-medium text-[11px] transition-all select-none ${
                      activeScriptFilter === scriptKey
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {scriptKey}
                  </button>
                ))}
              </div>

              {/* Sort selector */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'likes' | 'confidence' | 'newest')}
                className="h-9 text-xs rounded-lg border border-slate-300 bg-white px-2.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
                aria-label="Sort comments"
              >
                <option value="likes">Most Liked</option>
                <option value="confidence">Highest Confidence</option>
                <option value="newest">Most Recent</option>
              </select>
            </div>
          </div>

          {/* Sentiment category chips */}
          <div className="flex flex-wrap items-center gap-1.5 pt-3 border-t border-slate-100 mt-3 text-xs">
            {(['all', 'positive', 'negative', 'neutral', 'mixed', 'unsupported'] as const).map((filterKey) => {
              const count =
                filterKey === 'all'
                  ? comments.length
                  : summary?.sentiment_counts[filterKey] ?? 0;
              return (
                <button
                  key={filterKey}
                  type="button"
                  onClick={() => {
                    setActiveTab(filterKey);
                    setCurrentPage(1);
                  }}
                  className={`px-3 py-1 rounded-md font-medium capitalize transition-all select-none flex items-center gap-1.5 ${
                    activeTab === filterKey
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  <span>{filterKey}</span>
                  {summary && (
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                        activeTab === filterKey
                          ? 'bg-slate-800 text-slate-200'
                          : 'bg-white text-slate-600'
                      }`}
                    >
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <CommentsTable
            comments={paginatedComments}
            currentPage={currentPage}
            totalPages={totalPages}
            pageSize={pageSize}
            totalFiltered={filteredComments.length}
            onPageChange={setCurrentPage}
            onInspectComment={(c) => {
              setInspectedComment(c);
              setIsModalOpen(true);
            }}
            onTranslateComment={handleTranslateSingleComment}
            translatingCommentId={translatingCommentId}
            isSkeleton={isDisplayingSkeleton}
            hasActiveFilters={Boolean(searchQuery || activeTab !== 'all' || activeScriptFilter !== 'all')}
            onClearFilters={() => {
              setSearchQuery('');
              setActiveTab('all');
              setActiveScriptFilter('all');
            }}
            emptyTitle={job ? 'No Matching Comments Found' : 'No Analyzed Comments'}
            emptyDescription={
              job
                ? 'No comments matched your current keyword or script filter criteria.'
                : 'Analyze a YouTube video from the Analyze page to view full comment breakdowns and translations.'
            }
            emptyAction={
              !job ? (
                <div className="flex flex-col sm:flex-row items-center gap-3 mt-4">
                  <Link to="/analyze">
                    <Button size="sm">
                      Go to Analyze
                      <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                    </Button>
                  </Link>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSearchParams({ job_id: 'demo-aavesham-2026-sample' });
                    }}
                  >
                    <Sparkles className="w-3.5 h-3.5 mr-1.5 text-brand-600" />
                    Explore Demo Review Dataset
                  </Button>
                </div>
              ) : undefined
            }
          />
        </CardContent>
      </Card>

      {/* Comment Details & Class Probabilities Breakdown Modal (Phase 7 & 8) */}
      <CommentDetailsModal
        comment={inspectedComment}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setInspectedComment(null);
        }}
        onTranslateComment={handleTranslateSingleComment}
        isTranslating={translatingCommentId === inspectedComment?.comment_id}
      />
    </div>
  );
};
