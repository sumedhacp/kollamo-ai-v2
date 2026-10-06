import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge, SentimentBadge } from '@/components/ui/badge';
import { Alert } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Sparkles, Languages, Info, RefreshCw, Globe } from 'lucide-react';
import { SingleSentimentResult } from '@/types';
import { api, ApiError } from '@/services/api';

export const Sandbox: React.FC = () => {
  const [text, setText] = useState('');
  const [translate, setTranslate] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<{ message: string; code?: string } | null>(null);
  const [result, setResult] = useState<SingleSentimentResult | null>(null);

  // Client-side quick script preview for instantaneous input feedback
  const clientDetectedScript = useMemo(() => {
    if (!text.trim()) return 'None';
    const hasMalayalam = /[\u0D00-\u0D7F]/.test(text);
    const hasLatin = /[a-zA-Z]/.test(text);
    if (hasMalayalam && hasLatin) return 'Code-Mixed (Malayalam + Latin)';
    if (hasMalayalam) return 'Malayalam Script';
    if (hasLatin) return 'Latin Script (Manglish / English)';
    return 'Other';
  }, [text]);

  const maxChars = 1000;

  const sampleComments = [
    {
      label: 'Manglish (Positive)',
      text: 'Ee padam kidilan aayirunnu, must watch movie!',
    },
    {
      label: 'Malayalam (Positive)',
      text: 'തിയേറ്ററിൽ തന്നെ കാണേണ്ട ഒരു മികച്ച കലാസൃഷ്ടി.',
    },
    {
      label: 'Code-Mixed (Mixed)',
      text: 'First half entertaining aayirunnu pakshe climax bore aayi.',
    },
    {
      label: 'English (Neutral)',
      text: 'When is the OTT release date announced for this film?',
    },
    {
      label: 'Manglish (Negative)',
      text: 'Valare mosham direction. Total waste of time and money.',
    },
  ];

  const handleAnalyze = async () => {
    setValidationError(null);
    setApiError(null);

    const trimmed = text.trim();
    if (!trimmed) {
      setValidationError('Please enter a comment before analyzing.');
      return;
    }
    if (trimmed.length > maxChars) {
      setValidationError(`Comment exceeds maximum limit of ${maxChars} characters.`);
      return;
    }

    setIsLoading(true);

    try {
      const data = await api.analyzeSentiment(trimmed, translate);
      setResult(data);
    } catch (err: unknown) {
      // Per AGENTS.md rule: Zero fake AI results.
      // We report real connection or inference errors cleanly.
      setResult(null);
      if (err instanceof ApiError) {
        setApiError({
          message: err.message,
          code: err.code,
        });
      } else {
        setApiError({
          message: err instanceof Error ? err.message : 'An unexpected error occurred during inference.',
          code: 'UNEXPECTED_ERROR',
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setText('');
    setResult(null);
    setValidationError(null);
    setApiError(null);
  };

  // Map sentiment classes to specific progress bar colors
  const getProbabilityBarColor = (sentimentKey: string): string => {
    switch (sentimentKey) {
      case 'positive':
        return 'bg-emerald-500';
      case 'negative':
        return 'bg-rose-500';
      case 'neutral':
        return 'bg-slate-400';
      case 'mixed':
        return 'bg-amber-500';
      case 'unsupported':
        return 'bg-zinc-400';
      default:
        return 'bg-brand-500';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="secondary" className="gap-1">
            <Sparkles className="w-3.5 h-3.5 text-brand-600" />
            Live Neural Inference
          </Badge>
          <span className="text-xs text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-medium border border-emerald-200">
            Phase 6 Integrated (Live Backend)
          </span>
        </div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Comment Sentiment Sandbox</h1>
        <p className="text-base text-slate-600 mt-1">
          Test individual comments in Malayalam, Manglish, English, or code-mixed text.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Col: Input Area */}
        <div className="lg:col-span-7 space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Input Comment</CardTitle>
              <CardDescription>
                Type or paste a social media reaction below to detect script and evaluate sentiment.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Textarea with Character Counter */}
              <div>
                <Textarea
                  value={text}
                  onChange={(e) => {
                    setText(e.target.value);
                    if (validationError) setValidationError(null);
                  }}
                  placeholder="Enter a Malayalam, Manglish, or code-mixed comment (e.g., 'Padam kidilam aayirunnu, fully worth the ticket price!')..."
                  className="min-h-[160px] text-base"
                  maxLength={maxChars}
                  aria-label="Comment text for sentiment analysis"
                />
                <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-700">Detected Script:</span>
                    <Badge variant="outline" size="sm" className="bg-slate-50">
                      <Languages className="w-3 h-3 text-brand-600 mr-1" />
                      {clientDetectedScript}
                    </Badge>
                  </div>
                  <span className={text.length >= maxChars ? 'text-rose-600 font-semibold' : ''}>
                    {text.length} / {maxChars} characters
                  </span>
                </div>
              </div>

              {/* Translation Toggle */}
              <div className="flex items-center justify-between p-3 rounded-xl border border-slate-200 bg-slate-50/50">
                <div className="flex items-center gap-2.5">
                  <Globe className="w-4 h-4 text-brand-600" />
                  <div>
                    <label htmlFor="translate-toggle" className="text-xs font-semibold text-slate-800 cursor-pointer block">
                      Enable English Translation
                    </label>
                    <span className="text-[11px] text-slate-500 block">
                      Translate regional Malayalam and Manglish comments for cross-lingual insight
                    </span>
                  </div>
                </div>
                <input
                  id="translate-toggle"
                  type="checkbox"
                  checked={translate}
                  onChange={(e) => setTranslate(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 cursor-pointer"
                />
              </div>

              {/* Validation alert */}
              {validationError && (
                <Alert variant="error" title="Validation Error">
                  {validationError}
                </Alert>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleReset}
                  disabled={!text && !result && !apiError}
                >
                  <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                  Clear Input
                </Button>
                <Button
                  onClick={handleAnalyze}
                  isLoading={isLoading}
                  disabled={!text.trim()}
                  className="px-6"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Analyze Sentiment
                </Button>
              </div>

              {/* Quick sample pills */}
              <div className="pt-4 border-t border-slate-100">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-2">
                  Try Sample Comments:
                </span>
                <div className="flex flex-wrap gap-2">
                  {sampleComments.map((sample, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        setText(sample.text);
                        setValidationError(null);
                        setApiError(null);
                        setResult(null);
                      }}
                      className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 hover:border-slate-300 transition-colors text-left"
                    >
                      <span className="font-medium text-brand-700 block text-[11px]">{sample.label}</span>
                      <span className="truncate max-w-[200px] block text-slate-600">{sample.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Col: Result Panel */}
        <div className="lg:col-span-5 space-y-6">
          <Card className="h-full flex flex-col">
            <CardHeader className="pb-3 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <CardTitle>Sentiment Result</CardTitle>
                {result && <SentimentBadge sentiment={result.sentiment} />}
              </div>
              <CardDescription>
                Probabilistic 5-class distribution and confidence breakdown.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1 p-6 flex flex-col justify-center">
              {/* State 1: Loading State */}
              {isLoading && (
                <div className="space-y-4 py-4" data-testid="sandbox-loading-state">
                  <div className="flex items-center justify-between">
                    <Skeleton className="h-6 w-32" />
                    <Skeleton className="h-6 w-20" />
                  </div>
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <div className="pt-4 space-y-3">
                    <Skeleton className="h-3 w-full" />
                    <Skeleton className="h-3 w-5/6" />
                    <Skeleton className="h-3 w-4/6" />
                  </div>
                  <p className="text-xs text-center text-slate-500 pt-2 animate-pulse">
                    Evaluating comment with Google MuRIL inference pipeline...
                  </p>
                </div>
              )}

              {/* State 2: Error State */}
              {!isLoading && apiError && (
                <div className="space-y-4" data-testid="sandbox-error-state">
                  <Alert
                    variant={apiError.code === 'NETWORK_ERROR' ? 'error' : 'warning'}
                    title={apiError.code ? `API Error: ${apiError.code}` : 'Analysis Error'}
                  >
                    {apiError.message}
                  </Alert>
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-2">
                    <div className="flex items-center gap-1.5 font-semibold text-slate-800">
                      <Info className="w-4 h-4 text-brand-600" />
                      <span>Zero Fake AI Prediction Guarantee</span>
                    </div>
                    <p>
                      Kollamo.ai strictly adheres to academic rigor: we never substitute fake or randomly generated sentiments when backend services are unreachable. Ensure the FastAPI server is active at <code>http://localhost:8000</code>.
                    </p>
                  </div>
                </div>
              )}

              {/* State 3: Empty State */}
              {!isLoading && !apiError && !result && (
                <div data-testid="sandbox-empty-state">
                  <EmptyState
                    icon={<Sparkles className="w-7 h-7 text-brand-500" />}
                    title="No Analysis Yet"
                    description="Enter a comment or select a sample on the left, then click 'Analyze Sentiment' to inspect results."
                  />
                </div>
              )}

              {/* State 4: Success State (When real result is returned) */}
              {!isLoading && result && (
                <div className="space-y-6" data-testid="sandbox-result-state">
                  {/* Original Text Display */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      <span>Original Comment</span>
                      <div className="flex items-center gap-1.5">
                        <Badge variant="outline" size="sm" className="capitalize text-[11px]">
                          {result.detected_script}
                        </Badge>
                        <Badge variant="secondary" size="sm" className="font-mono text-[10px]">
                          {result.detected_language}
                        </Badge>
                      </div>
                    </div>
                    <p className="text-sm text-slate-800 italic font-serif">
                      "{result.original_text}"
                    </p>
                  </div>

                  {/* Summary Metric Badges */}
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                      <span className="text-slate-500 block">Classified Sentiment:</span>
                      <span className="font-bold text-slate-900 capitalize text-sm">
                        {result.sentiment}
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                      <span className="text-slate-500 block">Top Confidence:</span>
                      <span className="font-bold text-slate-900 text-sm">
                        {(result.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Class Probabilities Distribution */}
                  <div className="space-y-2">
                    <div className="text-xs font-semibold text-slate-700">
                      5-Class Probability Distribution
                    </div>
                    {Object.entries(result.class_probabilities).map(([key, prob]) => {
                      const percentage = (prob * 100).toFixed(1);
                      return (
                        <div key={key} className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="capitalize text-slate-600 font-medium">{key}</span>
                            <span className="font-mono text-slate-800 font-medium">
                              {percentage}%
                            </span>
                          </div>
                          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-300 ${getProbabilityBarColor(key)}`}
                              style={{ width: `${Math.max(Number(percentage), 1)}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* English Translation Section (if present) */}
                  {result.translated_text && (
                    <div className="p-3.5 rounded-xl border border-brand-200 bg-brand-50/40 space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-brand-900 flex items-center gap-1">
                          <Globe className="w-3.5 h-3.5 text-brand-600" />
                          English Translation
                        </span>
                        <Badge variant="outline" size="sm" className="bg-white text-[10px]">
                          {result.translation_status}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-800">
                        {result.translated_text}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
