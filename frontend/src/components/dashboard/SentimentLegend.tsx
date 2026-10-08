import React from 'react';
import { SentimentCounts } from '@/services/api/types';

export interface SentimentLegendItem {
  id: string;
  name: string;
  count: number;
  percentage: number;
  color: string;
  bgColor: string;
  borderColor: string;
}

interface SentimentLegendProps {
  sentimentCounts: SentimentCounts;
  totalAnalyzed: number;
  activeFilter?: string | null;
  onSelect?: (sentiment: string) => void;
  className?: string;
}

export const SentimentLegend: React.FC<SentimentLegendProps> = ({
  sentimentCounts,
  totalAnalyzed,
  activeFilter,
  onSelect,
  className = '',
}) => {
  const calcPct = (count: number): number => {
    if (totalAnalyzed <= 0) return 0;
    return Number(((count / totalAnalyzed) * 100).toFixed(1));
  };

  const legendItems: SentimentLegendItem[] = [
    {
      id: 'Positive',
      name: 'Positive',
      count: sentimentCounts.Positive,
      percentage: calcPct(sentimentCounts.Positive),
      color: 'bg-emerald-500',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200',
    },
    {
      id: 'Negative',
      name: 'Negative',
      count: sentimentCounts.Negative,
      percentage: calcPct(sentimentCounts.Negative),
      color: 'bg-rose-500',
      bgColor: 'bg-rose-50',
      borderColor: 'border-rose-200',
    },
    {
      id: 'Neutral',
      name: 'Neutral',
      count: sentimentCounts.Neutral,
      percentage: calcPct(sentimentCounts.Neutral),
      color: 'bg-slate-400',
      bgColor: 'bg-slate-50',
      borderColor: 'border-slate-200',
    },
    {
      id: 'Mixed',
      name: 'Mixed',
      count: sentimentCounts.Mixed,
      percentage: calcPct(sentimentCounts.Mixed),
      color: 'bg-amber-500',
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-200',
    },
    {
      id: 'Unsupported',
      name: 'Unsupported',
      count: sentimentCounts.Unsupported,
      percentage: calcPct(sentimentCounts.Unsupported),
      color: 'bg-purple-500',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
    },
  ];

  return (
    <div
      className={`grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2.5 ${className}`}
      data-testid="sentiment-legend"
      role="list"
      aria-label="Sentiment distribution legend"
    >
      {legendItems.map((item) => {
        const isSelected = activeFilter && activeFilter.toLowerCase() === item.id.toLowerCase();
        const isInteractive = Boolean(onSelect);

        return (
          <div
            key={item.id}
            role="listitem"
            tabIndex={isInteractive ? 0 : undefined}
            onClick={() => onSelect?.(item.id)}
            onKeyDown={(e) => {
              if (isInteractive && (e.key === 'Enter' || e.key === ' ')) {
                e.preventDefault();
                onSelect?.(item.id);
              }
            }}
            className={`p-2.5 rounded-xl border text-left transition-all ${
              isSelected
                ? 'ring-2 ring-brand-500 shadow-xs ' + item.bgColor + ' ' + item.borderColor
                : 'bg-white border-slate-200 hover:border-slate-300'
            } ${isInteractive ? 'cursor-pointer hover:shadow-xs' : 'cursor-default'}`}
            title={`${item.name}: ${item.count} comments (${item.percentage}% of analyzed comments)`}
          >
            <div className="flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${item.color}`}
                aria-hidden="true"
              />
              <span className="text-xs font-semibold text-slate-700 truncate">
                {item.name}
              </span>
            </div>
            <div className="mt-1.5 flex items-baseline justify-between gap-1">
              <span className="text-sm font-bold text-slate-900 font-mono">
                {item.count.toLocaleString()}
              </span>
              <span className="text-[11px] font-medium text-slate-500 font-mono">
                {item.percentage.toFixed(1)}%
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
