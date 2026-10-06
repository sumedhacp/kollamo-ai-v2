import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Youtube,
  CheckCircle2,
  PlaySquare,
  Settings2,
  Clock,
  BarChart3,
  RefreshCw,
  Video,
  Eye,
  Check,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { SampleSize, SortMode } from '@/types';
import { api, ApiError } from '@/services/api';
import { useJobPolling } from '@/hooks/useJobPolling';

export const Analyze: React.FC = () => {
  const navigate = useNavigate();

  const [url, setUrl] = useState('');
  const [sampleSize, setSampleSize] = useState<SampleSize>(100);
  const [sortMode, setSortMode] = useState<SortMode>('top');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<{ message: string; code?: string } | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const sampleSizes: SampleSize[] = [50, 100, 250, 500, 'ALL'];

  const sortOptions: { value: SortMode; label: string; desc: string }[] = [
    { value: 'top', label: 'Most Liked', desc: 'Analyzes high-engagement discussions first' },
    { value: 'newest', label: 'Newest', desc: 'Captures fresh reactions and real-time trends' },
    { value: 'oldest', label: 'Oldest', desc: 'Evaluates initial reactions upon release' },
  ];

  const sampleVideos = [
    {
      title: 'Aavesham Official Trailer (Malayalam)',
      url: 'https://www.youtube.com/watch?v=L0yEMl8PXnw',
    },
    {
      title: 'Manjummel Boys Movie Review (Malayalam)',
      url: 'https://www.youtube.com/watch?v=5kKq3dF3PzQ',
    },
  ];

  const validateYouTubeUrl = (inputUrl: string): boolean => {
    const regExp =
      /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
    return regExp.test(inputUrl.trim());
  };

  // Real-time polling hook
  const {
    job,
    isPolling,
    error: pollingError,
    refetch,
  } = useJobPolling(activeJobId, {
    intervalMs: 1500,
  });

  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setSubmitError(null);

    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      setValidationError('Please enter a YouTube video URL.');
      return;
    }

    if (!validateYouTubeUrl(trimmedUrl)) {
      setValidationError(
        'Invalid YouTube URL. Please provide a standard link like https://www.youtube.com/watch?v=... or https://youtu.be/...'
      );
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await api.createAnalysisJob(trimmedUrl, sampleSize, sortMode);
      setActiveJobId(response.job_id);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setSubmitError({ message: err.message, code: err.code });
      } else {
        setSubmitError({
          message: err instanceof Error ? err.message : 'Failed to initialize analysis job.',
          code: 'INITIALIZATION_ERROR',
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetForm = () => {
    setActiveJobId(null);
    setUrl('');
    setValidationError(null);
    setSubmitError(null);
  };

  // Determine stage progression
  const calculateStage = (status?: string, progress?: number): number => {
    if (!status || status === 'queued') return 1;
    if (status === 'running') {
      const p = progress || 0;
      if (p < 0.2) return 2; // Ingestion
      if (p < 0.4) return 3; // Preprocessing
      if (p < 0.9) return 4; // Inference
      return 5; // Aggregation
    }
    if (status === 'completed') return 6;
    return 1;
  };

  const currentStage = calculateStage(job?.status, job?.progress);
  const progressPercent = Math.round((job?.progress ?? 0) * 100);

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
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">YouTube Comment Analysis</h1>
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
              <form onSubmit={handleStartAnalysis} className="space-y-6">
                {/* 1. YouTube URL Input */}
                <div>
                  <label htmlFor="youtube-url-input" className="block text-sm font-semibold text-slate-900 mb-2">
                    YouTube Video URL <span className="text-rose-500">*</span>
                  </label>
                  <Input
                    id="youtube-url-input"
                    value={url}
                    onChange={(e) => {
                      setUrl(e.target.value);
                      if (validationError) setValidationError(null);
                      if (submitError) setSubmitError(null);
                    }}
                    placeholder="https://www.youtube.com/watch?v=..."
                    leftIcon={<Youtube className="w-4 h-4 text-rose-500" />}
                    error={validationError || undefined}
                    aria-label="YouTube Video URL"
                    disabled={isSubmitting || Boolean(activeJobId && isPolling)}
                  />

                  {/* Sample Video Quick Fill */}
                  <div className="mt-2.5 flex items-center gap-2 text-xs text-slate-500">
                    <span>Try sample:</span>
                    {sampleVideos.map((sample, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setUrl(sample.url);
                          setValidationError(null);
                          setSubmitError(null);
                        }}
                        disabled={isSubmitting || Boolean(activeJobId && isPolling)}
                        className="text-brand-600 hover:text-brand-800 underline truncate max-w-[180px] disabled:opacity-50"
                      >
                        {sample.title}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 2. Sample Size Selector */}
                <div>
                  <label className="block text-sm font-semibold text-slate-900 mb-2">
                    Sample Size (Comments to Extract)
                  </label>
                  <div className="grid grid-cols-5 gap-2" role="radiogroup" aria-label="Sample Size">
                    {sampleSizes.map((size) => (
                      <button
                        key={size}
                        type="button"
                        role="radio"
                        aria-checked={sampleSize === size}
                        disabled={isSubmitting || Boolean(activeJobId && isPolling)}
                        onClick={() => setSampleSize(size)}
                        className={`py-2 px-3 text-xs font-semibold rounded-lg border transition-all text-center select-none disabled:opacity-50 ${
                          sampleSize === size
                            ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
                            : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        {size}
                      </button>
                    ))}
                  </div>
                  <p className="mt-1.5 text-xs text-slate-500">
                    Larger sample sizes provide deeper demographic insight across long discussion threads.
                  </p>
                </div>

                {/* 3. Sorting Selector */}
                <div>
                  <label className="block text-sm font-semibold text-slate-900 mb-2">
                    Comment Ordering
                  </label>
                  <div className="space-y-2">
                    {sortOptions.map((opt) => (
                      <label
                        key={opt.value}
                        className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${
                          sortMode === opt.value
                            ? 'bg-brand-50/60 border-brand-300 text-slate-900'
                            : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
                        }`}
                      >
                        <input
                          type="radio"
                          name="sort_mode"
                          value={opt.value}
                          checked={sortMode === opt.value}
                          disabled={isSubmitting || Boolean(activeJobId && isPolling)}
                          onChange={() => setSortMode(opt.value)}
                          className="mt-0.5 text-brand-600 focus:ring-brand-500"
                        />
                        <div className="text-xs">
                          <span className="font-semibold block text-slate-900">{opt.label}</span>
                          <span className="text-slate-500">{opt.desc}</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Submit Error Alert */}
                {submitError && (
                  <Alert variant="error" title={submitError.code || 'Job Dispatch Error'}>
                    {submitError.message}
                  </Alert>
                )}

                {/* Submit button */}
                <Button
                  type="submit"
                  size="lg"
                  className="w-full"
                  isLoading={isSubmitting}
                  disabled={isSubmitting || (Boolean(activeJobId) && isPolling)}
                >
                  <PlaySquare className="w-4 h-4 mr-2" />
                  {isSubmitting ? 'Queueing Analysis...' : 'Start Ingestion & Analysis'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Progress & Telemetry Panel */}
        <div className="lg:col-span-5 space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Settings2 className="w-4 h-4 text-brand-600" />
                  Pipeline Execution Panel
                </span>
                {activeJobId && (
                  <Badge
                    variant={
                      job?.status === 'completed'
                        ? 'default'
                        : job?.status === 'failed'
                        ? 'negative'
                        : 'secondary'
                    }
                    size="sm"
                    className="capitalize"
                  >
                    {job?.status || 'Queued'}
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                Real-time progress telemetry and asynchronous worker lifecycle.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {/* If job active */}
              {activeJobId ? (
                <div className="space-y-4" data-testid="analyze-progress-panel">
                  {/* Video Metadata Card (when available) */}
                  {job?.video && (
                    <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/70 space-y-2">
                      <div className="flex items-start gap-2.5">
                        <Video className="w-4 h-4 text-rose-600 mt-0.5 flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                          <h4 className="text-xs font-semibold text-slate-900 truncate">
                            {job.video.title}
                          </h4>
                          <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500">
                            <span>{job.video.channel_title}</span>
                            {job.video.view_count !== undefined && (
                              <>
                                <span>•</span>
                                <span className="flex items-center gap-1">
                                  <Eye className="w-3 h-3 text-slate-400" />
                                  {Number(job.video.view_count).toLocaleString()} views
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Polling Error Alert */}
                  {pollingError && (
                    <Alert variant="error" title="Pipeline Error">
                      {pollingError.message}
                    </Alert>
                  )}

                  {/* Progress Bar & Numerical Counter */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-700">
                        {job?.status === 'completed'
                          ? 'Analysis Complete'
                          : job?.status === 'failed'
                          ? 'Job Failed'
                          : 'Processing Comments...'}
                      </span>
                      <span className="font-mono font-bold text-brand-700">
                        {progressPercent}%
                      </span>
                    </div>

                    <Progress value={progressPercent} max={100} />

                    <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
                      <span>Comments Evaluated:</span>
                      <span className="font-mono font-medium text-slate-800">
                        {job?.processed_comments || 0} / {job?.total_comments || sampleSize}
                      </span>
                    </div>

                    {/* Step-by-step lifecycle indicators */}
                    <div className="pt-3 border-t border-slate-200 text-xs text-slate-600 space-y-2">
                      <div className="font-medium text-slate-900 mb-1">Execution Stages:</div>
                      <div className="space-y-1.5 pl-1">
                        {[
                          { step: 1, label: '1. Queued in Redis / PostgreSQL' },
                          { step: 2, label: '2. YouTube Data API v3 Ingestion' },
                          { step: 3, label: '3. Unicode NFKC & Script Classification' },
                          { step: 4, label: '4. MuRIL Neural Sentiment Inference' },
                          { step: 5, label: '5. Metric Aggregation & Engagement Rollup' },
                        ].map((s) => {
                          const isDone = currentStage > s.step;
                          const isCurrent = currentStage === s.step;
                          return (
                            <div
                              key={s.step}
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
                                <RefreshCw className="w-3.5 h-3.5 text-brand-600 animate-spin" />
                              ) : (
                                <div className="w-2 h-2 rounded-full bg-slate-300 ml-1 mr-0.5" />
                              )}
                              <span>{s.label}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  {/* Actions when completed */}
                  {job?.status === 'completed' && (
                    <div className="space-y-3 pt-2">
                      <Button
                        size="lg"
                        className="w-full bg-emerald-600 hover:bg-emerald-700"
                        onClick={() => navigate(`/dashboard?job_id=${job.job_id}`)}
                      >
                        <BarChart3 className="w-4 h-4 mr-2" />
                        View Audience Dashboard
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={handleResetForm}
                      >
                        Analyze Another Video
                      </Button>
                    </div>
                  )}

                  {/* Actions when failed */}
                  {job?.status === 'failed' && (
                    <div className="space-y-3 pt-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        className="w-full"
                        onClick={() => {
                          if (job?.job_id) {
                            api.processJob(job.job_id).then(() => refetch()).catch(() => {});
                          }
                        }}
                      >
                        <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                        Retry Processing
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={handleResetForm}
                      >
                        Try Different Video
                      </Button>
                    </div>
                  )}
                </div>
              ) : (
                /* Empty state before triggering */
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
