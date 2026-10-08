import React from 'react';
import {
  MessageSquare,
  Smile,
  Frown,
  Minus,
  Shuffle,
  HelpCircle,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { SentimentCounts } from '@/services/api/types';

interface MetricCardsProps {
  totalAnalyzed: number;
  sentimentCounts: SentimentCounts;
}

export const MetricCards: React.FC<MetricCardsProps> = ({
  totalAnalyzed,
  sentimentCounts,
}) => {
  // Safe percentage calculation handling totalAnalyzed = 0 without errors (Section 15)
  const calcPct = (count: number): string => {
    if (totalAnalyzed <= 0) return '0.0%';
    return `${((count / totalAnalyzed) * 100).toFixed(1)}%`;
  };

  const metrics = [
    {
      id: 'total',
      label: 'Analyzed Comments',
      count: totalAnalyzed,
      pct: null,
      sublabel: 'Total sample analyzed',
      icon: MessageSquare,
      iconColor: 'text-brand-600',
      bgColor: 'bg-brand-50/60',
      borderColor: 'border-slate-200',
      textColor: 'text-slate-900',
      badgeColor: 'bg-slate-100 text-slate-700',
    },
    {
      id: 'positive',
      label: 'Positive',
      count: sentimentCounts.Positive,
      pct: calcPct(sentimentCounts.Positive),
      sublabel: 'of analyzed comments',
      icon: Smile,
      iconColor: 'text-emerald-600',
      bgColor: 'bg-emerald-50/50',
      borderColor: 'border-emerald-200/70',
      textColor: 'text-emerald-950',
      badgeColor: 'bg-emerald-100 text-emerald-800',
    },
    {
      id: 'negative',
      label: 'Negative',
      count: sentimentCounts.Negative,
      pct: calcPct(sentimentCounts.Negative),
      sublabel: 'of analyzed comments',
      icon: Frown,
      iconColor: 'text-rose-600',
      bgColor: 'bg-rose-50/50',
      borderColor: 'border-rose-200/70',
      textColor: 'text-rose-950',
      badgeColor: 'bg-rose-100 text-rose-800',
    },
    {
      id: 'neutral',
      label: 'Neutral',
      count: sentimentCounts.Neutral,
      pct: calcPct(sentimentCounts.Neutral),
      sublabel: 'of analyzed comments',
      icon: Minus,
      iconColor: 'text-slate-600',
      bgColor: 'bg-slate-50/60',
      borderColor: 'border-slate-200',
      textColor: 'text-slate-900',
      badgeColor: 'bg-slate-100 text-slate-700',
    },
    {
      id: 'mixed',
      label: 'Mixed',
      count: sentimentCounts.Mixed,
      pct: calcPct(sentimentCounts.Mixed),
      sublabel: 'of analyzed comments',
      icon: Shuffle,
      iconColor: 'text-amber-600',
      bgColor: 'bg-amber-50/50',
      borderColor: 'border-amber-200/70',
      textColor: 'text-amber-950',
      badgeColor: 'bg-amber-100 text-amber-800',
    },
    {
      id: 'unsupported',
      label: 'Unsupported',
      count: sentimentCounts.Unsupported,
      pct: calcPct(sentimentCounts.Unsupported),
      sublabel: 'of analyzed comments',
      icon: HelpCircle,
      iconColor: 'text-purple-600',
      bgColor: 'bg-purple-50/50',
      borderColor: 'border-purple-200/70',
      textColor: 'text-purple-950',
      badgeColor: 'bg-purple-100 text-purple-800',
    },
  ];

  return (
    <div className="space-y-3" data-testid="metric-cards">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800 uppercase tracking-wider text-xs">
          Key Analysis Metrics
        </h3>
        <span className="text-xs text-slate-500 font-medium">
          Five-Class Taxonomy
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {metrics.map((m) => {
          const Icon = m.icon;
          return (
            <Card
              key={m.id}
              className={`border ${m.borderColor} shadow-xs transition-all hover:shadow-sm`}
            >
              <CardContent className="p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-600 truncate">
                    {m.label}
                  </span>
                  <div
                    className={`w-7 h-7 rounded-lg ${m.bgColor} flex items-center justify-center flex-shrink-0 ${m.iconColor}`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                </div>

                <div>
                  <div className={`text-2xl font-bold tracking-tight ${m.textColor}`}>
                    {Number(m.count).toLocaleString()}
                  </div>
                  <div className="text-[11px] text-slate-500 font-medium truncate mt-0.5" title={m.pct ? `${m.pct} ${m.sublabel}` : m.sublabel}>
                    {m.pct ? (
                      <>
                        <span className="font-semibold text-slate-700 mr-1">{m.pct}</span>
                        <span>{m.sublabel}</span>
                      </>
                    ) : (
                      <span>{m.sublabel}</span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
