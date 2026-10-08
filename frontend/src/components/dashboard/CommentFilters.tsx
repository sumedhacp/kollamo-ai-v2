import React from 'react';
import { X, Tag } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { SentimentClass } from '@/types';

interface CommentFiltersProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  activeTab: 'all' | SentimentClass;
  onTabChange: (tab: 'all' | SentimentClass) => void;
  activeScriptFilter: 'all' | 'Malayalam' | 'Latin' | 'Mixed';
  onScriptFilterChange: (script: 'all' | 'Malayalam' | 'Latin' | 'Mixed') => void;
  sortBy: 'likes' | 'confidence' | 'newest';
  onSortByChange: (sortBy: 'likes' | 'confidence' | 'newest') => void;
  selectedTheme: string | null;
  onSelectTheme: (theme: string | null) => void;
  discussionTopics?: Array<{ label: string; term: string }>;
  countsBySentiment?: Record<string, number>;
}

export const CommentFilters: React.FC<CommentFiltersProps> = ({
  searchQuery,
  onSearchChange,
  activeTab,
  onTabChange,
  activeScriptFilter,
  onScriptFilterChange,
  sortBy,
  onSortByChange,
  selectedTheme,
  onSelectTheme,
  discussionTopics = [],
  countsBySentiment,
}) => {
  const sentimentTabs: Array<{ id: 'all' | SentimentClass; label: string }> = [
    { id: 'all', label: 'All' },
    { id: 'positive', label: 'Positive' },
    { id: 'negative', label: 'Negative' },
    { id: 'neutral', label: 'Neutral' },
    { id: 'mixed', label: 'Mixed' },
    { id: 'unsupported', label: 'Unsupported' },
  ];

  const scriptOptions: Array<'all' | 'Malayalam' | 'Latin' | 'Mixed'> = [
    'all',
    'Malayalam',
    'Latin',
    'Mixed',
  ];

  return (
    <div className="space-y-4" data-testid="comment-filters">
      {/* Top Filter Controls: Search & Sort */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Input
            placeholder="Search comments, authors, or translations..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full text-xs"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => onSearchChange('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              aria-label="Clear search input"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Sort:
          </span>
          <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs">
            <button
              type="button"
              onClick={() => onSortByChange('likes')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                sortBy === 'likes'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Most Liked
            </button>
            <button
              type="button"
              onClick={() => onSortByChange('confidence')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                sortBy === 'confidence'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Confidence
            </button>
            <button
              type="button"
              onClick={() => onSortByChange('newest')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                sortBy === 'newest'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Newest
            </button>
          </div>
        </div>
      </div>

      {/* Sentiment Filter Pills */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider mr-1">
          Sentiment:
        </span>
        {sentimentTabs.map((tab) => {
          const isSelected = activeTab === tab.id;
          const count = countsBySentiment?.[tab.id];

          return (
            <Button
              key={tab.id}
              variant={isSelected ? 'primary' : 'outline'}
              size="sm"
              onClick={() => onTabChange(tab.id)}
              className="text-xs py-1 h-7"
            >
              <span>{tab.label}</span>
              {count !== undefined && (
                <span className={`ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                  isSelected ? 'bg-brand-700 text-white' : 'bg-slate-100 text-slate-600'
                }`}>
                  {count}
                </span>
              )}
            </Button>
          );
        })}
      </div>

      {/* Script Filter Bar */}
      <div className="flex items-center gap-1.5 flex-wrap text-xs">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider mr-1">
          Script:
        </span>
        {scriptOptions.map((script) => (
          <button
            key={script}
            type="button"
            onClick={() => onScriptFilterChange(script)}
            className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
              activeScriptFilter === script
                ? 'bg-slate-800 text-white shadow-xs'
                : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            {script === 'all' ? 'All Scripts' : script}
          </button>
        ))}
      </div>

      {/* Discussion Topics / Themes */}
      {discussionTopics.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap pt-1 border-t border-slate-100 text-xs">
          <div className="flex items-center gap-1 text-slate-500 font-semibold uppercase tracking-wider text-[11px] mr-1">
            <Tag className="w-3 h-3 text-brand-600" />
            <span>Themes:</span>
          </div>
          {discussionTopics.map((topic) => (
            <Button
              key={topic.term}
              variant={selectedTheme === topic.term ? 'primary' : 'outline'}
              size="sm"
              onClick={() => onSelectTheme(selectedTheme === topic.term ? null : topic.term)}
              className="text-xs py-0.5 h-6 rounded-full"
            >
              {topic.label}
            </Button>
          ))}
          {selectedTheme && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onSelectTheme(null)}
              className="text-xs py-0.5 h-6 text-rose-600 hover:text-rose-800"
            >
              <X className="w-3 h-3 mr-1" />
              Clear theme filter
            </Button>
          )}
        </div>
      )}
    </div>
  );
};
