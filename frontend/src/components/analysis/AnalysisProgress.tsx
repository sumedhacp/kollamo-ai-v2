import React from 'react';
import { RefreshCw, Check, Loader2 } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { JobProgress } from '@/services/api/types';
import { getStageLabel } from '@/services/api/analysis';

interface AnalysisProgressProps {
  progress: JobProgress | null;
  stageName?: string;
  isCompleted?: boolean;
  isFailed?: boolean;
}

export const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  progress,
  stageName,
  isCompleted = false,
  isFailed = false,
}) => {
  const currentStage = progress?.stage || stageName || 'QUEUED';
  const stageFriendly = getStageLabel(currentStage);

  const hasPercentage = progress?.percentage !== null && progress?.percentage !== undefined;
  const percentageValue = hasPercentage ? Math.min(100, Math.max(0, progress!.percentage!)) : null;

  // Discrete stages in execution pipeline
  const pipelineStages = [
    { key: 'QUEUED', label: '1. Waiting to start (Queue)' },
    { key: 'FETCHING_VIDEO', label: '2. Fetching video information' },
    { key: 'FETCHING_COMMENTS', label: '3. Collecting comments' },
    { key: 'SENTIMENT_ANALYSIS', label: '4. Analyzing sentiment' },
    { key: 'FINALIZING', label: '5. Preparing results' },
  ];

  const getStageOrder = (stageKey: string): number => {
    const upper = stageKey.toUpperCase();
    if (upper === 'QUEUED') return 1;
    if (upper === 'FETCHING_VIDEO') return 2;
    if (upper === 'FETCHING_COMMENTS') return 3;
    if (upper === 'SENTIMENT_ANALYSIS') return 4;
    if (upper === 'FINALIZING') return 5;
    if (upper === 'COMPLETED') return 6;
    return 1;
  };

  const activeStageOrder = isCompleted ? 6 : getStageOrder(currentStage);

  return (
    <div
      className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-4"
      data-testid="analyze-progress-panel"
    >

      {/* Current Stage Headline and Percentage */}
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-slate-800 flex items-center gap-2">
          {!isCompleted && !isFailed && (
            <RefreshCw className="w-3.5 h-3.5 text-brand-600 animate-spin" />
          )}
          {isCompleted
            ? 'Analysis Complete'
            : isFailed
            ? 'Analysis Failed'
            : stageFriendly}
        </span>
        {percentageValue !== null ? (
          <span className="font-mono font-bold text-brand-700">
            {percentageValue}%
          </span>
        ) : (
          !isCompleted && !isFailed && (
            <span className="text-[11px] text-slate-500 font-medium">In progress</span>
          )
        )}
      </div>

      {/* Progress Bar (determinate or indeterminate) */}
      {percentageValue !== null ? (
        <Progress value={percentageValue} max={100} />
      ) : !isCompleted && !isFailed ? (
        <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden relative">
          <div className="bg-brand-600 h-full w-1/3 rounded-full animate-pulse" />
        </div>
      ) : null}

      {/* Progress Counters when available */}
      {progress && (progress.completed > 0 || progress.total !== null) && (
        <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
          <span>Items Processed:</span>
          <span className="font-mono font-medium text-slate-800">
            {progress.completed}
            {progress.total !== null ? ` / ${progress.total}` : ''}
          </span>
        </div>
      )}

      {/* Step-by-Step Lifecycle Stage Indicators */}
      <div className="pt-3 border-t border-slate-200 text-xs text-slate-600 space-y-2">
        <div className="font-medium text-slate-900 mb-1">Execution Pipeline:</div>
        <div className="space-y-1.5 pl-1">
          {pipelineStages.map((stage, idx) => {
            const stageStep = idx + 1;
            const isDone = activeStageOrder > stageStep;
            const isCurrent = activeStageOrder === stageStep && !isCompleted && !isFailed;

            return (
              <div
                key={stage.key}
                className={`flex items-center gap-2 ${
                  isDone
                    ? 'text-emerald-700 font-medium'
                    : isCurrent
                    ? 'text-brand-700 font-semibold'
                    : 'text-slate-400'
                }`}
              >
                {isDone ? (
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                ) : isCurrent ? (
                  <Loader2 className="w-3.5 h-3.5 text-brand-600 animate-spin" />
                ) : (
                  <div className="w-2 h-2 rounded-full bg-slate-300 ml-1 mr-0.5" />
                )}
                <span>{stage.label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
