import { useState } from 'react';
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
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { SentimentClass } from '@/types';

export const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'all' | SentimentClass>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showSkeleton, setShowSkeleton] = useState(false);

  // Per Task 7 & AGENTS.md rule: Do NOT insert fake production numbers.
  // We use clean empty/skeleton states.
  const summaryCards = [
    {
      title: 'Total Comments',
      value: '-',
      icon: <MessageSquare className="w-4 h-4 text-brand-600" />,
      border: 'border-slate-200',
      badge: '0 Analyzed',
    },
    {
      title: 'Positive',
      value: '-',
      icon: <Smile className="w-4 h-4 text-emerald-600" />,
      border: 'border-emerald-200',
      badge: '0%',
    },
    {
      title: 'Negative',
      value: '-',
      icon: <Frown className="w-4 h-4 text-rose-600" />,
      border: 'border-rose-200',
      badge: '0%',
    },
    {
      title: 'Neutral',
      value: '-',
      icon: <Minus className="w-4 h-4 text-slate-600" />,
      border: 'border-slate-200',
      badge: '0%',
    },
    {
      title: 'Mixed',
      value: '-',
      icon: <Shuffle className="w-4 h-4 text-amber-600" />,
      border: 'border-amber-200',
      badge: '0%',
    },
    {
      title: 'Unsupported',
      value: '-',
      icon: <HelpCircle className="w-4 h-4 text-zinc-500" />,
      border: 'border-zinc-200',
      badge: '0%',
    },
  ];

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
            <span className="text-xs text-slate-500">Phase 1 Dashboard Skeleton</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Audience Analytics Dashboard</h1>
          <p className="text-sm text-slate-600 mt-1">
            Multilingual sentiment distributions, engagement metrics, and granular comment intelligence.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSkeleton(!showSkeleton)}
            title="Toggle between skeleton loading mode and empty data state"
          >
            <Layers className="w-3.5 h-3.5 mr-1.5" />
            {showSkeleton ? 'Show Empty State' : 'Preview Skeleton State'}
          </Button>

          <Button variant="secondary" size="sm" disabled title="Available after analysis runs in Phase 8">
            <Download className="w-3.5 h-3.5 mr-1.5" />
            Export PDF Report
          </Button>
        </div>
      </div>

      {/* 1. Summary Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {summaryCards.map((card, idx) => (
          <Card key={idx} className={`border ${card.border} shadow-sm`}>
            <CardContent className="p-4 space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="font-medium truncate">{card.title}</span>
                {card.icon}
              </div>
              {showSkeleton ? (
                <Skeleton className="h-7 w-16" />
              ) : (
                <div className="text-2xl font-bold text-slate-900">{card.value}</div>
              )}
              {showSkeleton ? (
                <Skeleton className="h-4 w-12" />
              ) : (
                <div className="text-[11px] text-slate-400 font-mono">{card.badge}</div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 2. Visual Charts Row (Skeleton / Empty) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Distribution Chart Container */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center justify-between">
              <span>Sentiment Distribution</span>
              <Badge variant="outline" size="sm">5-Class Breakdown</Badge>
            </CardTitle>
            <CardDescription>
              Proportion of positive, negative, neutral, mixed, and unsupported sentiments.
            </CardDescription>
          </CardHeader>
          <CardContent className="h-64 flex flex-col items-center justify-center">
            {showSkeleton ? (
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
              <Badge variant="outline" size="sm">Like Ratios</Badge>
            </CardTitle>
            <CardDescription>
              Correlation between comment polarity and community likes.
            </CardDescription>
          </CardHeader>
          <CardContent className="h-64 flex flex-col items-center justify-center">
            {showSkeleton ? (
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
          {showSkeleton ? (
            <div className="p-6 space-y-4" data-testid="dashboard-table-skeleton">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : (
            <div className="p-8">
              <EmptyState
                icon={<Filter className="w-8 h-8 text-slate-400" />}
                title="No Analyzed Comments"
                description="Comments extracted via YouTube Data API v3 will appear here with detected script, MuRIL sentiment, and English translations in Phase 7."
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
