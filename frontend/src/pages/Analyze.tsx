import { useState } from 'react';
import { Youtube, CheckCircle2, PlaySquare, Settings2, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { SampleSize, SortMode } from '@/types';

export const Analyze: React.FC = () => {
  const [url, setUrl] = useState('');
  const [sampleSize, setSampleSize] = useState<SampleSize>(100);
  const [sortMode, setSortMode] = useState<SortMode>('top');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [apiNotice, setApiNotice] = useState<string | null>(null);
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
    const regExp = /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
    return regExp.test(inputUrl.trim());
  };

  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setApiNotice(null);

    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      setValidationError('Please enter a YouTube video URL.');
      return;
    }

    if (!validateYouTubeUrl(trimmedUrl)) {
      setValidationError('Invalid YouTube URL. Please provide a standard link like https://www.youtube.com/watch?v=... or https://youtu.be/...');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          youtube_url: trimmedUrl,
          sample_size: sampleSize,
          sort_mode: sortMode,
        }),
      });

      if (!response.ok) {
        throw new Error(`API responded with status ${response.status}`);
      }

      const data = await response.json();
      setActiveJobId(data.job_id);
    } catch {
      // In Phase 1 UI shell, FastAPI and Celery backend are not yet active
      setApiNotice(
        'YouTube Ingestion & Asynchronous Analysis service (/api/analyze) is scheduled for Phase 4 (YouTube Ingestion) and Phase 5 (Celery + Redis). Per AGENTS.md rules, progress is never faked.'
      );
      setActiveJobId('demo-shell-pending');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="secondary" className="gap-1">
            <Youtube className="w-3.5 h-3.5 text-rose-600" />
            Ingestion Pipeline
          </Badge>
          <span className="text-xs text-slate-500">Phase 1 UI Shell</span>
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
                    }}
                    placeholder="https://www.youtube.com/watch?v=..."
                    leftIcon={<Youtube className="w-4 h-4 text-rose-500" />}
                    error={validationError || undefined}
                    aria-label="YouTube Video URL"
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
                        }}
                        className="text-brand-600 hover:text-brand-800 underline truncate max-w-[180px]"
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
                        onClick={() => setSampleSize(size)}
                        className={`py-2 px-3 text-xs font-semibold rounded-lg border transition-all text-center select-none ${
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

                {/* Submit button */}
                <Button
                  type="submit"
                  size="lg"
                  className="w-full"
                  isLoading={isSubmitting}
                >
                  <PlaySquare className="w-4 h-4 mr-2" />
                  Start Ingestion & Analysis
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Progress & Architecture Panel */}
        <div className="lg:col-span-5 space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Settings2 className="w-4 h-4 text-brand-600" />
                Pipeline Execution Panel
              </CardTitle>
              <CardDescription>
                Real-time progress telemetry and background job lifecycle.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {/* If job submitted or triggered */}
              {activeJobId ? (
                <div className="space-y-4" data-testid="analyze-progress-panel">
                  {apiNotice && (
                    <Alert variant="info" title="Phase 1 Architectural Notice">
                      {apiNotice}
                    </Alert>
                  )}

                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-700">Pipeline Stage:</span>
                      <Badge variant="outline" size="sm">
                        Asynchronous Pipeline Scaffold
                      </Badge>
                    </div>

                    <Progress value={0} max={100} />

                    <div className="pt-2 border-t border-slate-200 text-xs text-slate-600 space-y-2">
                      <div className="font-medium text-slate-900 mb-1">Standard Lifecycle Stages:</div>
                      <div className="space-y-1.5 pl-1">
                        <div className="flex items-center gap-2 text-slate-500">
                          <div className="w-2 h-2 rounded-full bg-slate-300" />
                          <span>1. Queued in Redis</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-500">
                          <div className="w-2 h-2 rounded-full bg-slate-300" />
                          <span>2. YouTube Data API v3 Ingestion</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-500">
                          <div className="w-2 h-2 rounded-full bg-slate-300" />
                          <span>3. Malayalam Unicode Preprocessing</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-500">
                          <div className="w-2 h-2 rounded-full bg-slate-300" />
                          <span>4. Google MuRIL Neural Inference</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-500">
                          <div className="w-2 h-2 rounded-full bg-slate-300" />
                          <span>5. Metric Aggregation & Dashboard</span>
                        </div>
                      </div>
                    </div>
                  </div>
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
