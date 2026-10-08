import React, { useState } from 'react';
import { Youtube, PlaySquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert } from '@/components/ui/alert';
import {
  AnalysisJobRequest,
  CommentLimit,
  SortBy,
} from '@/services/api/types';

interface AnalysisFormProps {
  onSubmit: (request: AnalysisJobRequest) => void;
  isSubmitting: boolean;
  isDisabled?: boolean;
  initialUrl?: string;
  externalError?: string | null;
}

export const AnalysisForm: React.FC<AnalysisFormProps> = ({
  onSubmit,
  isSubmitting,
  isDisabled = false,
  initialUrl = '',
  externalError = null,
}) => {
  const [url, setUrl] = useState(initialUrl);
  const [commentLimit, setCommentLimit] = useState<CommentLimit>(100);
  const [sortBy, setSortBy] = useState<SortBy>('most_liked');
  const [validationError, setValidationError] = useState<string | null>(null);

  const sampleSizes: CommentLimit[] = [50, 100, 250, 500, 'ALL'];

  const sortOptions: { value: SortBy; label: string; desc: string }[] = [
    { value: 'most_liked', label: 'Most Liked', desc: 'Analyzes high-engagement discussions first' },
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
    const trimmed = inputUrl.trim();
    if (!trimmed) return false;
    const regExp =
      /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
    return regExp.test(trimmed);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

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

    onSubmit({
      video_url: trimmedUrl,
      comment_limit: commentLimit,
      sort_by: sortBy,
    });
  };

  const isFormLocked = isSubmitting || isDisabled;

  return (
    <form onSubmit={handleSubmit} className="space-y-6" data-testid="analysis-form">
      {/* 1. YouTube URL Input */}
      <div>
        <label
          htmlFor="youtube-url-input"
          className="block text-sm font-semibold text-slate-900 mb-2"
        >
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
          disabled={isFormLocked}
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
                if (validationError) setValidationError(null);
              }}
              disabled={isFormLocked}
              className="text-brand-600 hover:text-brand-800 underline truncate max-w-[180px] disabled:opacity-50"
            >
              {sample.title}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Comment Limit Selection */}
      <div>
        <label className="block text-sm font-semibold text-slate-900 mb-2">
          Comment Limit
        </label>
        <div
          className="grid grid-cols-5 gap-2"
          role="radiogroup"
          aria-label="Comment Limit"
        >
          {sampleSizes.map((size) => (
            <button
              key={size}
              type="button"
              role="radio"
              aria-checked={commentLimit === size}
              disabled={isFormLocked}
              onClick={() => setCommentLimit(size)}
              className={`py-2 px-3 text-xs font-semibold rounded-lg border transition-all text-center select-none disabled:opacity-50 ${
                commentLimit === size
                  ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
                  : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {size}
            </button>
          ))}
        </div>
        <p className="mt-1.5 text-xs text-slate-500">
          Configurable comment sampling limits: 50, 100, 250, 500, or ALL available comments.
        </p>
      </div>

      {/* 3. Comment Sorting Strategy */}
      <div>
        <label className="block text-sm font-semibold text-slate-900 mb-2">
          Comment Ordering
        </label>
        <div className="space-y-2">
          {sortOptions.map((opt) => (
            <label
              key={opt.value}
              className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${
                sortBy === opt.value
                  ? 'bg-brand-50/60 border-brand-300 text-slate-900'
                  : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
              } ${isFormLocked ? 'opacity-60 cursor-not-allowed' : ''}`}
            >
              <input
                type="radio"
                name="sort_by"
                value={opt.value}
                checked={sortBy === opt.value}
                disabled={isFormLocked}
                onChange={() => setSortBy(opt.value)}
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

      {/* External / Submit Error Alert */}
      {externalError && (
        <Alert variant="error" title="Analysis Error">
          {externalError}
        </Alert>
      )}

      {/* Submit button */}
      <Button
        type="submit"
        size="lg"
        className="w-full"
        isLoading={isSubmitting}
        disabled={isFormLocked}
      >
        <PlaySquare className="w-4 h-4 mr-2" />
        {isSubmitting ? 'Starting Analysis...' : 'Start Ingestion & Analysis'}
      </Button>
    </form>
  );
};

