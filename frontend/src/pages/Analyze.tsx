import React, { useState } from 'react';
import {
  Youtube,
  Settings2,
  Clock,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import {
  AnalysisForm,
  AnalysisProgress,
  AnalysisStatus,
  AnalysisResultPreview,
} from '@/components/analysis';
import { useAnalysisJob } from '@/hooks/useAnalysisJob';
import { AnalysisJobRequest } from '@/services/api/types';

interface AnalyzeProps {
  pollingIntervalMs?: number;
}

export const Analyze: React.FC<AnalyzeProps> = ({
  pollingIntervalMs = 2000,
}) => {
  const [submittedUrl, setSubmittedUrl] = useState<string>('');

  const {
    state,
    jobId,
    progress,
    result,
    error,
    isSubmitting,
    isPolling,
    isCompleted,
    isFailed,
    submitJob,
    reset,
    retry,
  } = useAnalysisJob({
    pollingIntervalMs,
  });


  const handleFormSubmit = async (request: AnalysisJobRequest) => {
    setSubmittedUrl(request.video_url);
    await submitJob(request);
  };

  const handleReset = () => {
    reset();
    setSubmittedUrl('');
  };

  const isJobActive = isSubmitting || isPolling || isCompleted || isFailed;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="secondary" className="gap-1">
            <Youtube className="w-3.5 h-3.5 text-rose-600" />
            Asynchronous Pipeline
          </Badge>
          <span className="text-xs text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-medium border border-emerald-200">
            Phase 6 Integrated
          </span>
        </div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
          YouTube Comment Analysis
        </h1>
        <p className="text-base text-slate-600 mt-1">
          Extract and analyze hundreds or thousands of Malayalam and code-mixed comments directly from any YouTube video.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Form Column */}
        <div className="lg:col-span-7 space-y-6">
          <Card>
            <CardHeader className="pb-4">
              <CardTitle>Analysis Parameters</CardTitle>
              <CardDescription>
                Configure comment sample size and ordering for the asynchronous ingestion job.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AnalysisForm
                onSubmit={handleFormSubmit}
                isSubmitting={isSubmitting}
                isDisabled={isPolling}
                initialUrl={submittedUrl}
              />
            </CardContent>
          </Card>

          {/* Result Preview (when completed) */}
          {isCompleted && result && jobId && (
            <AnalysisResultPreview
              jobId={jobId}
              result={result}
              onReset={handleReset}
            />
          )}
        </div>

        {/* Telemetry & Lifecycle Panel Column */}
        <div className="lg:col-span-5 space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Settings2 className="w-4 h-4 text-brand-600" />
                  Pipeline Execution Panel
                </span>
                {isJobActive && (
                  <AnalysisStatus status={state} />
                )}
              </CardTitle>
              <CardDescription>
                Real-time progress telemetry and asynchronous worker lifecycle.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {isJobActive ? (
                <div className="space-y-4">
                  {/* Progress Telemetry */}
                  <AnalysisProgress
                    progress={progress}
                    stageName={state}
                    isCompleted={isCompleted}
                    isFailed={isFailed}
                  />

                  {/* Failure State Notification */}
                  {isFailed && error && (
                    <div className="space-y-3" role="alert">
                      <Alert
                        variant="error"
                        title={
                          error.code === 'MODEL_NOT_READY'
                            ? 'Model Not Ready'
                            : error.code === 'NETWORK_ERROR'
                            ? 'Connection Failure'
                            : error.code || 'Job Execution Error'
                        }
                      >
                        {error.code === 'MODEL_NOT_READY'
                          ? 'The sentiment analysis model is not ready yet. Please try again after the model has been configured.'
                          : error.code === 'NETWORK_ERROR'
                          ? 'Unable to connect to the Kollamo.ai backend. Please check that the backend is running.'
                          : error.message}
                      </Alert>

                      <div className="flex items-center gap-2 pt-1">
                        <Button
                          variant="secondary"
                          size="sm"
                          className="w-full"
                          onClick={() => retry()}
                        >
                          <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                          Retry Analysis
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full"
                          onClick={handleReset}
                        >
                          Try Different Video
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                /* Information state when idle */
                <div className="space-y-4 text-xs text-slate-500 py-4">
                  <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 space-y-3">
                    <div className="flex items-center gap-2 font-medium text-slate-800">
                      <Clock className="w-4 h-4 text-brand-600" />
                      <span>Zero UI Freezing Architecture</span>
                    </div>
                    <p className="leading-relaxed">
                      Kollamo.ai processes YouTube comments asynchronously using a dedicated Celery worker pool and Redis message broker. Even for 3,500+ comments, the web interface remains instant and responsive.
                    </p>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 space-y-2">
                    <div className="flex items-center gap-2 font-medium text-slate-800">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>Official API Guarantee</span>
                    </div>
                    <p className="leading-relaxed">
                      We strictly use the official YouTube Data API v3; HTML scraping is prohibited to ensure reliability and full compliance.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
