import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { api, ApiError } from '@/services/api';
import { Sandbox } from '@/pages/Sandbox';
import { Analyze } from '@/pages/Analyze';
import { Dashboard } from '@/pages/Dashboard';
import { SingleSentimentResult, AnalysisJob, AnalyzeJobCreateResponse, HealthStatus } from '@/types';

describe('Frontend/Backend API Client Layer', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('checkHealth returns HealthStatus on success', async () => {
    const mockHealth: HealthStatus = {
      status: 'healthy',
      service: 'Kollamo.ai API',
      version: '0.4.0',
      environment: 'development',
      database: 'connected',
      redis: 'connected',
      ml_model: 'muril-multilingual-v1',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
    });

    const res = await api.checkHealth();
    expect(res.status).toBe('healthy');
    expect(res.database).toBe('connected');
    expect(res.ml_model).toBe('muril-multilingual-v1');
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/health',
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('analyzeSentiment sends payload and returns prediction data', async () => {
    const mockResult: SingleSentimentResult = {
      original_text: 'Padam kidilan aayirunnu',
      detected_language: 'ml-en',
      detected_script: 'Latin',
      sentiment: 'positive',
      confidence: 0.94,
      class_probabilities: {
        positive: 0.94,
        negative: 0.02,
        neutral: 0.02,
        mixed: 0.01,
        unsupported: 0.01,
      },
      translation_status: 'translated',
      translated_text: 'The movie was awesome',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResult,
    });

    const res = await api.analyzeSentiment('Padam kidilan aayirunnu', true);
    expect(res.sentiment).toBe('positive');
    expect(res.confidence).toBe(0.94);
    expect(res.translated_text).toBe('The movie was awesome');
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/sentiment',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ text: 'Padam kidilan aayirunnu', translate: true }),
      })
    );
  });

  it('createAnalysisJob dispatches job and returns job_id', async () => {
    const mockCreated: AnalyzeJobCreateResponse = {
      job_id: 'test-job-uuid-1234',
      status: 'queued',
      message: 'Analysis job queued successfully',
      created_at: '2026-10-07T00:00:00Z',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockCreated,
    });

    const res = await api.createAnalysisJob('https://www.youtube.com/watch?v=L0yEMl8PXnw', 100, 'top');
    expect(res.job_id).toBe('test-job-uuid-1234');
    expect(res.status).toBe('queued');
  });

  it('parses standardized RFC error envelope on non-ok responses', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => ({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid YouTube URL format.',
          details: [{ loc: ['body', 'youtube_url'], msg: 'Invalid URL' }],
        },
      }),
    });

    await expect(api.createAnalysisJob('invalid-url', 100, 'top')).rejects.toThrow(
      'Invalid YouTube URL format.'
    );

    try {
      await api.createAnalysisJob('invalid-url', 100, 'top');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(422);
      expect(apiErr.code).toBe('VALIDATION_ERROR');
      expect(apiErr.details).toBeDefined();
    }
  });

  it('handles network failure cleanly as NETWORK_ERROR', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Failed to fetch'));

    await expect(api.checkHealth()).rejects.toThrow('Network connection failed');
    try {
      await api.checkHealth();
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).code).toBe('NETWORK_ERROR');
    }
  });
});

describe('Sandbox Live Inference Integration', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('submits text to API and displays classified sentiment and probability distribution', async () => {
    const mockResult: SingleSentimentResult = {
      original_text: 'തിയേറ്ററിൽ തന്നെ കാണേണ്ട ഒരു മികച്ച കലാസൃഷ്ടി.',
      detected_language: 'ml',
      detected_script: 'Malayalam',
      sentiment: 'positive',
      confidence: 0.965,
      class_probabilities: {
        positive: 0.965,
        negative: 0.01,
        neutral: 0.015,
        mixed: 0.005,
        unsupported: 0.005,
      },
      translation_status: 'translated',
      translated_text: 'A masterpiece that must be watched in theatres.',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResult,
    });

    render(
      <MemoryRouter>
        <Sandbox />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/comment text for sentiment analysis/i);
    fireEvent.change(textarea, {
      target: { value: 'തിയേറ്ററിൽ തന്നെ കാണേണ്ട ഒരു മികച്ച കലാസൃഷ്ടി.' },
    });

    const submitBtn = screen.getByRole('button', { name: /analyze sentiment/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId('sandbox-result-state')).toBeInTheDocument();
    });

    expect(screen.getAllByText('96.5%').length).toBeGreaterThan(0);
    expect(screen.getByText('A masterpiece that must be watched in theatres.')).toBeInTheDocument();
  });

  it('handles backend error response and renders error alert with zero fake predictions', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: async () => ({
        error: {
          code: 'MODEL_OFFLINE',
          message: 'MuRIL model weights are currently downloading.',
        },
      }),
    });

    render(
      <MemoryRouter>
        <Sandbox />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/comment text for sentiment analysis/i);
    fireEvent.change(textarea, { target: { value: 'Test comment' } });

    const submitBtn = screen.getByRole('button', { name: /analyze sentiment/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId('sandbox-error-state')).toBeInTheDocument();
    });

    expect(
      screen.getByText(/MuRIL model weights are currently downloading/i)
    ).toBeInTheDocument();
    expect(screen.queryByTestId('sandbox-result-state')).not.toBeInTheDocument();
  });
});

describe('Analyze Page Real-Time Job Polling Integration', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('submits YouTube URL, tracks progress lifecycle, and renders completion CTA', async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {

      if (
        (url.includes('/api/v1/analysis/jobs') || url.includes('/api/analyze')) &&
        !url.includes('job-xyz-789')
      ) {
        return Promise.resolve({
          ok: true,
          status: 202,
          json: async () => ({
            job_id: 'job-xyz-789',
            status: 'QUEUED',
            message: 'Analysis job queued successfully',
            created_at: '2026-10-07T00:00:00Z',
          }),
        });
      }
      if (url.includes('job-xyz-789')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            job_id: 'job-xyz-789',
            status: 'COMPLETED',
            progress: {
              stage: 'COMPLETED',
              completed: 100,
              total: 100,
              percentage: 100,
            },
            result: {
              video: {
                video_id: 'L0yEMl8PXnw',
                title: 'Aavesham Official Trailer',
                channel_title: 'Anand Audio',
                view_count: 5000000,
              },
              total_comments: 100,
              processed_comments: 100,
              comments: [
                {
                  comment_id: 'c1',
                  text: 'Kidilan padam!',
                  author_name: 'Rahul M',
                  sentiment: 'Positive',
                  confidence: 0.98,
                  like_count: 42,
                  probabilities: { Positive: 0.98, Negative: 0.01, Neutral: 0.01, Mixed: 0.0, Unsupported: 0.0 },
                },
              ],
            },
          }),
        });
      }
      return Promise.reject(new Error(`Unhandled url: ${url}`));
    });


    render(
      <MemoryRouter>
        <Analyze />
      </MemoryRouter>
    );

    const input = screen.getByLabelText(/youtube video url/i);
    fireEvent.change(input, {
      target: { value: 'https://www.youtube.com/watch?v=L0yEMl8PXnw' },
    });

    const submitBtn = screen.getByRole('button', { name: /start ingestion & analysis/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId('analyze-progress-panel')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Aavesham Official Trailer')).toBeInTheDocument();
      expect(screen.getByText(/100%/i)).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: /view audience dashboard/i })
      ).toBeInTheDocument();
    });
  });
});

describe('Dashboard Job Telemetry Integration', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('fetches job status when job_id query parameter is present', async () => {
    const jobData: AnalysisJob = {
      job_id: 'job-test-456',
      status: 'completed',
      progress: 1.0,
      processed_comments: 250,
      total_comments: 250,
      video: {
        video_id: '5kKq3dF3PzQ',
        title: 'Manjummel Boys Movie Review',
        channel_title: 'Cinema Reviewer',
        view_count: 850000,
      },
      summary: {
        total_analyzed: 250,
        sentiment_counts: {
          positive: 190,
          negative: 20,
          neutral: 25,
          mixed: 15,
          unsupported: 0,
        },
        sentiment_percentages: {
          positive: 76.0,
          negative: 8.0,
          neutral: 10.0,
          mixed: 6.0,
          unsupported: 0.0,
        },
        engagement_metrics: {
          total_likes: 3400,
          average_likes_per_sentiment: {
            positive: 16.5,
            negative: 4.2,
            neutral: 5.1,
            mixed: 3.0,
            unsupported: 0.0,
          },
        },
      },
      comments: [
        {
          comment_id: 'c1',
          author_display_name: 'Rahul M',
          published_at: '2026-10-07T00:00:00Z',
          like_count: 42,
          reply_count: 2,
          original_text: 'Adipoli movie, loved every minute of it!',
          detected_language: 'ml-en',
          detected_script: 'Latin',
          sentiment: 'positive',
          confidence: 0.98,
          translated_text: 'Awesome movie, loved every minute of it!',
        },
      ],
      created_at: '2026-10-07T00:00:00Z',
      completed_at: '2026-10-07T00:00:10Z',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => jobData,
    });

    render(
      <MemoryRouter initialEntries={['/dashboard?job_id=job-test-456']}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Manjummel Boys Movie Review')).toBeInTheDocument();
      expect(screen.getAllByText('76.0%').length).toBeGreaterThan(0);
      expect(screen.getByText('Adipoli movie, loved every minute of it!')).toBeInTheDocument();
      expect(screen.getByText('Rahul M')).toBeInTheDocument();
    });
  });
});
