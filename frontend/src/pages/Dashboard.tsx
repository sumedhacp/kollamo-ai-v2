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

export const Dashboard: React.FC = () => {
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get('job_id');

  const [activeTab, setActiveTab] = useState<'all' | SentimentClass>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showSkeleton, setShowSkeleton] = useState(false);

  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
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
      { label: 'Positive', pct: summary.sentiment_percentages.positive, color: 'bg-emerald-500', barHeight: `${Math.max(summary.sentiment_percentages.positive, 4)}%` },
      { label: 'Negative', pct: summary.sentiment_percentages.negative, color: 'bg-rose-500', barHeight: `${Math.max(summary.sentiment_percentages.negative, 4)}%` },
      { label: 'Neutral', pct: summary.sentiment_percentages.neutral, color: 'bg-slate-400', barHeight: `${Math.max(summary.sentiment_percentages.neutral, 4)}%` },
      { label: 'Mixed', pct: summary.sentiment_percentages.mixed, color: 'bg-amber-500', barHeight: `${Math.max(summary.sentiment_percentages.mixed, 4)}%` },
      { label: 'Unsupported', pct: summary.sentiment_percentages.unsupported, color: 'bg-zinc-400', barHeight: `${Math.max(summary.sentiment_percentages.unsupported, 4)}%` },
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
              {job ? `Job: ${job.job_id.slice(0, 8)}...` : 'Phase 6 Integrated'}
            </span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
            {job?.video ? job.video.title : 'Audience Analytics Dashboard'}
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            {job?.video
              ? `Channel: ${job.video.channel_title} • ${Number(job.video.view_count || 0).toLocaleString()} views`
              : 'Multilingual sentiment distributions, engagement metrics, and granular comment intelligence.'}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSkeleton(!showSkeleton)}
            title="Toggle between skeleton loading mode and active data state"
          >
            <Layers className="w-3.5 h-3.5 mr-1.5" />
            {showSkeleton ? 'Show Live View' : 'Preview Skeleton State'}
          </Button>

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

      {/* 2. Visual Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Distribution Chart Container */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center justify-between">
              <span>Sentiment Distribution</span>
              <Badge variant="outline" size="sm">5-Class Share</Badge>
            </CardTitle>
            <CardDescription>
              Proportion of positive, negative, neutral, mixed, and unsupported sentiments.
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
              <span>Sentiment vs. Engagement</span>
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

      {/* 3. Granular Comments Table */}
      <Card>
        <CardHeader className="pb-4 border-b border-slate-100">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle>Comments Intelligence Table</CardTitle>
              <CardDescription>
                Detailed comment-level classifications, script recognition, and English translations.
              </CardDescription>
            </div>

            {/* Filter toolbar */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="w-64">
                <Input
                  placeholder="Search comments..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  leftIcon={<Search className="w-3.5 h-3.5 text-slate-400" />}
                  className="h-9 text-xs"
                />
              </div>

              {/* Sentiment filter pills */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs">
                {(['all', 'positive', 'negative', 'neutral', 'mixed', 'unsupported'] as const).map((filterKey) => (
                  <button
                    key={filterKey}
                    type="button"
                    onClick={() => setActiveTab(filterKey)}
                    className={`px-2.5 py-1 rounded-md font-medium capitalize transition-all select-none ${
                      activeTab === filterKey
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {filterKey}
                  </button>
                ))}
              </div>
            </div>
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
          ) : job?.comments && job.comments.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                  <tr>
                    <th className="px-4 py-3">Author</th>
                    <th className="px-4 py-3">Comment Text</th>
                    <th className="px-4 py-3">Script</th>
                    <th className="px-4 py-3">Sentiment</th>
                    <th className="px-4 py-3">Confidence</th>
                    <th className="px-4 py-3">Likes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {job.comments
                    .filter((c) => activeTab === 'all' || c.sentiment === activeTab)
                    .filter((c) => !searchQuery || c.original_text.toLowerCase().includes(searchQuery.toLowerCase()))
                    .map((c) => (
                      <tr key={c.comment_id} className="hover:bg-slate-50/50">
                        <td className="px-4 py-3 font-medium text-slate-900 whitespace-nowrap">
                          {c.author_display_name}
                        </td>
                        <td className="px-4 py-3 text-slate-700 max-w-md">
                          <div>{c.original_text}</div>
                          {c.translated_text && (
                            <div className="text-[11px] text-brand-700 italic mt-0.5">
                              {c.translated_text}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="outline" size="sm">{c.detected_script}</Badge>
                        </td>
                        <td className="px-4 py-3">
                          <SentimentBadge sentiment={c.sentiment} />
                        </td>
                        <td className="px-4 py-3 font-mono">
                          {(c.confidence * 100).toFixed(0)}%
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-600">
                          {c.like_count}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8">
              <EmptyState
                icon={<Filter className="w-8 h-8 text-slate-400" />}
                title={job ? 'No Comments Discovered' : 'No Analyzed Comments'}
                description={
                  job
                    ? 'No comment records were found in this analysis job.'
                    : 'Analyze a YouTube video from the Analyze page to view full comment breakdowns and translations.'
                }
                action={
                  !job ? (
                    <Link to="/analyze">
                      <Button size="sm">
                        Go to Analyze
                        <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                      </Button>
                    </Link>
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
