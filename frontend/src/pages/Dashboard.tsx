import { useState, useEffect, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  BarChart3,
  MessageSquare,
  ThumbsUp,
  Smile,
  Frown,
  Minus,
  Shuffle,
  HelpCircle,
  Search,
  Filter,
  Download,
  Layers,
  ArrowRight,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  TrendingUp,
  FileSpreadsheet,
  FileCode,
  Tag,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge, SentimentBadge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Alert } from '@/components/ui/alert';
import { SentimentClass, AnalysisJob } from '@/types';
import { api, ApiError } from '@/services/api';
import { DEMO_SAMPLE_JOB } from '@/data/sampleJob';

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

  const [showSkeleton, setShowSkeleton] = useState(false);
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

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

  const summaryCards = [
    {
      title: 'Total Comments',
      value: summary ? summary.total_analyzed.toLocaleString() : '-',
      icon: <MessageSquare className="w-4 h-4 text-brand-600" />,
      border: 'border-slate-200',
      badge: summary ? `${summary.total_analyzed} Analyzed` : '0 Analyzed',
    },
    {
      title: 'Positive',
      value: summary ? `${summary.sentiment_percentages.positive.toFixed(1)}%` : '-',
      icon: <Smile className="w-4 h-4 text-emerald-600" />,
      border: 'border-emerald-200',
      badge: summary ? `${summary.sentiment_counts.positive} comments` : '0%',
    },
    {
      title: 'Negative',
      value: summary ? `${summary.sentiment_percentages.negative.toFixed(1)}%` : '-',
      icon: <Frown className="w-4 h-4 text-rose-600" />,
      border: 'border-rose-200',
      badge: summary ? `${summary.sentiment_counts.negative} comments` : '0%',
    },
    {
      title: 'Neutral',
      value: summary ? `${summary.sentiment_percentages.neutral.toFixed(1)}%` : '-',
      icon: <Minus className="w-4 h-4 text-slate-600" />,
      border: 'border-slate-200',
      badge: summary ? `${summary.sentiment_counts.neutral} comments` : '0%',
    },
    {
      title: 'Mixed',
      value: summary ? `${summary.sentiment_percentages.mixed.toFixed(1)}%` : '-',
      icon: <Shuffle className="w-4 h-4 text-amber-600" />,
      border: 'border-amber-200',
      badge: summary ? `${summary.sentiment_counts.mixed} comments` : '0%',
    },
    {
      title: 'Unsupported',
      value: summary ? `${summary.sentiment_percentages.unsupported.toFixed(1)}%` : '-',
      icon: <HelpCircle className="w-4 h-4 text-zinc-500" />,
      border: 'border-zinc-200',
      badge: summary ? `${summary.sentiment_counts.unsupported} comments` : '0%',
    },
  ];

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
            {job?.video ? job.video.title : 'Audience Analytics Dashboard'}
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            {job?.video
              ? `Channel: ${job.video.channel_title} • ${Number(job.video.view_count || 0).toLocaleString()} views • ${comments.length} comments classified`
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
            </>
          )}

          <Button variant="secondary" size="sm" disabled title="PDF reporting scheduled for Phase 8">
            <Download className="w-3.5 h-3.5 mr-1.5" />
            Export PDF Report
          </Button>
        </div>
      </div>

      {/* Fetch Error Alert */}
      {fetchError && (
        <Alert variant="error" title="Job Data Fetch Failed">
          {fetchError}
        </Alert>
      )}

      {/* 1. Summary Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {summaryCards.map((card, idx) => (
          <Card key={idx} className={`border ${card.border} shadow-sm`}>
            <CardContent className="p-4 space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="font-medium truncate">{card.title}</span>
                {card.icon}
              </div>
              {isDisplayingSkeleton ? (
                <Skeleton className="h-7 w-16" />
              ) : (
                <div className="text-2xl font-bold text-slate-900">{card.value}</div>
              )}
              {isDisplayingSkeleton ? (
                <Skeleton className="h-4 w-12" />
              ) : (
                <div className="text-[11px] text-slate-400 font-mono">{card.badge}</div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

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
          {isDisplayingSkeleton ? (
            <div className="p-6 space-y-4" data-testid="dashboard-table-skeleton">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : paginatedComments.length > 0 ? (
            <div>
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
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {paginatedComments.map((c) => (
                      <tr key={c.comment_id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-4 py-3 font-medium text-slate-900 whitespace-nowrap align-top">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-[10px] font-bold text-slate-700">
                              {(c.author_display_name || 'U').charAt(0).toUpperCase()}
                            </div>
                            <span className="truncate max-w-[120px]">{c.author_display_name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-slate-700 max-w-md">
                          <div className="text-slate-900 font-serif text-[13px] leading-relaxed">
                            {c.original_text}
                          </div>
                          {c.translated_text && (
                            <div className="mt-1 p-2 rounded-lg bg-slate-50 border border-slate-200 text-brand-900 text-xs italic">
                              <span className="font-semibold text-slate-500 mr-1 not-italic text-[10px] uppercase">
                                En:
                              </span>
                              {c.translated_text}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3 align-top whitespace-nowrap">
                          <Badge variant="outline" size="sm">
                            {c.detected_script}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 align-top whitespace-nowrap">
                          <SentimentBadge sentiment={c.sentiment} />
                        </td>
                        <td className="px-4 py-3 align-top font-mono whitespace-nowrap">
                          {(c.confidence * 100).toFixed(1)}%
                        </td>
                        <td className="px-4 py-3 align-top font-mono text-slate-700 whitespace-nowrap">
                          <div className="flex items-center gap-1">
                            <ThumbsUp className="w-3 h-3 text-slate-400" />
                            <span>{c.like_count}</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination controls */}
              <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                <div>
                  Showing {(currentPage - 1) * pageSize + 1} to{' '}
                  {Math.min(currentPage * pageSize, filteredComments.length)} of{' '}
                  {filteredComments.length} comments
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={currentPage <= 1}
                    onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
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
                    onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                  >
                    Next
                    <ChevronRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8">
              <EmptyState
                icon={<Filter className="w-8 h-8 text-slate-400" />}
                title={job ? 'No Matching Comments Found' : 'No Analyzed Comments'}
                description={
                  job
                    ? 'No comments matched your current keyword or script filter criteria.'
                    : 'Analyze a YouTube video from the Analyze page to view full comment breakdowns and translations.'
                }
                action={
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
                  ) : searchQuery || activeTab !== 'all' || activeScriptFilter !== 'all' ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSearchQuery('');
                        setActiveTab('all');
                        setActiveScriptFilter('all');
                      }}
                    >
                      Clear All Filters
                    </Button>
                  ) : undefined
                }
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
