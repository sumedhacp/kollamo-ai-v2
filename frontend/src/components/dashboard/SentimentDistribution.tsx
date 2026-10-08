import React, { useState } from 'react';
import {
  PieChart as PieChartIcon,
  BarChart3,
  TrendingUp,
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip as RechartsTooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { SentimentCounts } from '@/services/api/types';
import { SentimentLegend } from './SentimentLegend';

interface SentimentDistributionProps {
  sentimentCounts: SentimentCounts;
  totalAnalyzed: number;
  netApprovalIndex?: number;
  onSentimentClick?: (sentiment: string) => void;
  activeFilter?: string | null;
}

interface ChartDataPoint {
  name: string;
  count: number;
  percentage: number;
  color: string;
  fill: string;
}

const CLASS_CONFIG = [
  { name: 'Positive', key: 'Positive' as const, color: '#10b981', tailwind: 'bg-emerald-500' },
  { name: 'Negative', key: 'Negative' as const, color: '#f43f5e', tailwind: 'bg-rose-500' },
  { name: 'Neutral', key: 'Neutral' as const, color: '#64748b', tailwind: 'bg-slate-500' },
  { name: 'Mixed', key: 'Mixed' as const, color: '#f59e0b', tailwind: 'bg-amber-500' },
  { name: 'Unsupported', key: 'Unsupported' as const, color: '#a855f7', tailwind: 'bg-purple-500' },
];

export const SentimentDistribution: React.FC<SentimentDistributionProps> = ({
  sentimentCounts,
  totalAnalyzed,
  netApprovalIndex,
  onSentimentClick,
  activeFilter,
}) => {
  const [chartMode, setChartMode] = useState<'donut' | 'bar'>('donut');

  const calcPct = (count: number): number => {
    if (totalAnalyzed <= 0) return 0;
    return Number(((count / totalAnalyzed) * 100).toFixed(1));
  };

  const chartData: ChartDataPoint[] = CLASS_CONFIG.map((cfg) => ({
    name: cfg.name,
    count: sentimentCounts[cfg.key] || 0,
    percentage: calcPct(sentimentCounts[cfg.key] || 0),
    color: cfg.tailwind,
    fill: cfg.color,
  }));

  // Recharts custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as ChartDataPoint;
      return (
        <div className="bg-white p-3 rounded-xl shadow-lg border border-slate-200 text-xs space-y-1">
          <div className="flex items-center gap-2">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: data.fill }}
            />
            <span className="font-semibold text-slate-800">{data.name}</span>
          </div>
          <div className="text-slate-600 font-mono">
            <strong>{data.count.toLocaleString()}</strong> comments
          </div>
          <div className="text-slate-500 text-[11px]">
            {data.percentage.toFixed(1)}% of analyzed comments
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="border-slate-200 shadow-sm" data-testid="sentiment-distribution">
      <CardHeader className="pb-3 border-b border-slate-100">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-brand-600" />
              <span>Five-Class Sentiment Distribution</span>
            </CardTitle>
            <CardDescription className="text-xs text-slate-500 mt-0.5">
              Aggregated distribution across Positive, Negative, Neutral, Mixed, and Unsupported classes
            </CardDescription>
          </div>

          <div className="flex items-center gap-2.5 self-start sm:self-auto">
            {netApprovalIndex !== undefined && (
              <span
                className={`hidden md:inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold font-mono border ${
                  netApprovalIndex >= 0
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    : 'bg-rose-50 text-rose-800 border-rose-200'
                }`}
                title="Spread between positive and negative comments"
              >
                <TrendingUp className="w-3.5 h-3.5" />
                <span>
                  Net: {netApprovalIndex >= 0 ? `+${netApprovalIndex}%` : `${netApprovalIndex}%`}
                </span>
              </span>
            )}

            {/* View Mode Switcher */}
            <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={chartMode === 'donut'}
                onClick={() => setChartMode('donut')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all ${
                  chartMode === 'donut'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <PieChartIcon className="w-3.5 h-3.5" />
                <span>Donut</span>
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={chartMode === 'bar'}
                onClick={() => setChartMode('bar')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all ${
                  chartMode === 'bar'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                <span>Bar</span>
              </button>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-5 sm:p-6 space-y-5">
        {/* Visual Chart Area */}
        <div className="w-full h-64 min-h-[256px] relative flex items-center justify-center">
          {totalAnalyzed > 0 ? (
            chartMode === 'donut' ? (
              <div className="w-full h-full relative">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                  minWidth={100}
                  minHeight={100}
                  initialDimension={{ width: 400, height: 256 }}
                >
                  <PieChart>
                    <Pie
                      data={chartData}
                      dataKey="count"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={65}
                      outerRadius={95}
                      paddingAngle={3}
                      onClick={(entry) => onSentimentClick?.(entry.name)}
                    >
                      {chartData.map((entry) => (
                        <Cell
                          key={`cell-${entry.name}`}
                          fill={entry.fill}
                          cursor={onSentimentClick ? 'pointer' : 'default'}
                          stroke={
                            activeFilter && activeFilter.toLowerCase() === entry.name.toLowerCase()
                              ? '#0f172a'
                              : '#ffffff'
                          }
                          strokeWidth={
                            activeFilter && activeFilter.toLowerCase() === entry.name.toLowerCase()
                              ? 2
                              : 1
                          }
                        />
                      ))}
                    </Pie>
                    <RechartsTooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>

                {/* Donut Center Display */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <span className="text-2xl font-bold text-slate-900 tracking-tight">
                    {totalAnalyzed.toLocaleString()}
                  </span>
                  <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
                    Comments
                  </span>
                </div>
              </div>
            ) : (
              <ResponsiveContainer
                width="100%"
                height="100%"
                minWidth={100}
                minHeight={100}
                initialDimension={{ width: 400, height: 256 }}
              >
                <BarChart
                  data={chartData}
                  margin={{ top: 15, right: 10, left: -15, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 11, fill: '#64748b' }}
                    axisLine={{ stroke: '#e2e8f0' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: '#64748b' }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <RechartsTooltip content={<CustomTooltip />} />
                  <Bar
                    dataKey="count"
                    radius={[6, 6, 0, 0]}
                    onClick={(entry) => onSentimentClick?.(entry.name)}
                  >
                    {chartData.map((entry) => (
                      <Cell
                        key={`bar-${entry.name}`}
                        fill={entry.fill}
                        cursor={onSentimentClick ? 'pointer' : 'default'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )
          ) : (
            <div className="text-center p-6 space-y-1.5 text-slate-400">
              <p className="text-sm font-medium">No comments analyzed</p>
              <p className="text-xs">Sentiment chart will populate when comments are processed.</p>
            </div>
          )}
        </div>

        {/* Five-Class Interactive Legend */}
        <SentimentLegend
          sentimentCounts={sentimentCounts}
          totalAnalyzed={totalAnalyzed}
          activeFilter={activeFilter}
          onSelect={onSentimentClick}
        />
      </CardContent>
    </Card>
  );
};
