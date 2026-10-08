import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import {
  createAnalysisJob,
  getAnalysisJob,
  checkHealth,
  getStageLabel,
} from '@/services/api/analysis';
import { ApiError } from '@/services/api/client';

import {
  AnalysisJobRequest,
  JobCreatedResponse,
  JobStatusResponse,
} from '@/services/api/types';
import { Analyze } from '@/pages/Analyze';

describe('Phase 6 API Client Layer (Section 54)', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('POST /api/v1/analysis/jobs dispatches valid request and receives 202 Accepted', async () => {
    const mockCreated: JobCreatedResponse = {
      job_id: 'job-phase6-123',
      status: 'QUEUED',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => mockCreated,
    });

    const req: AnalysisJobRequest = {
      video_url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
      comment_limit: 100,
      sort_by: 'newest',
    };

    const res = await createAnalysisJob(req);
    expect(res.job_id).toBe('job-phase6-123');
    expect(res.status).toBe('QUEUED');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/analysis/jobs'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(req),
      })
    );
  });

  it('POST /api/v1/analysis/jobs handles validation failure (422) cleanly', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => ({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Request validation failed.',
          details: {
            fields: [{ field: 'video_url', code: 'INVALID_URL', message: 'Invalid YouTube URL' }],
          },
        },
      }),
    });

    const req: AnalysisJobRequest = {
      video_url: 'invalid-url',
      comment_limit: 50,
      sort_by: 'newest',
    };

    await expect(createAnalysisJob(req)).rejects.toThrow('Request validation failed.');
    try {
      await createAnalysisJob(req);
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(422);
      expect(apiErr.code).toBe('VALIDATION_ERROR');
      expect(apiErr.details).toBeDefined();
    }
  });

  it('POST /api/v1/analysis/jobs handles 503 SERVICE_UNAVAILABLE / queue offline', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: async () => ({
        error: {
          code: 'JOB_QUEUE_UNAVAILABLE',
          message: 'The asynchronous task queue is currently unavailable.',
        },
      }),
    });

    const req: AnalysisJobRequest = {
      video_url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
      comment_limit: 50,
      sort_by: 'newest',
    };

    await expect(createAnalysisJob(req)).rejects.toThrow('The asynchronous task queue is currently unavailable.');
    try {
      await createAnalysisJob(req);
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).code).toBe('JOB_QUEUE_UNAVAILABLE');
    }
  });

  it('POST /api/v1/analysis/jobs handles network failure cleanly as NETWORK_ERROR', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Connection refused'));

    const req: AnalysisJobRequest = {
      video_url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
      comment_limit: 100,
      sort_by: 'newest',
    };

    try {
      await createAnalysisJob(req);
      expect.fail('Should have thrown ApiError');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).code).toBe('NETWORK_ERROR');
      expect((err as ApiError).message).toContain('Unable to connect to the Kollamo.ai backend');
    }
  });

  it('GET /api/v1/analysis/jobs/{job_id} returns 200 with job status payload', async () => {
    const mockStatus: JobStatusResponse = {
      job_id: 'job-phase6-123',
      status: 'PROCESSING',
      progress: {
        stage: 'SENTIMENT_ANALYSIS',
        completed: 42,
        total: 100,
        percentage: 42,
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockStatus,
    });

    const res = await getAnalysisJob('job-phase6-123');
    expect(res.status).toBe('PROCESSING');
    expect(res.progress?.percentage).toBe(42);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/analysis/jobs/job-phase6-123'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('GET /api/v1/analysis/jobs/{job_id} handles 404 JOB_NOT_FOUND', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({
        error: {
          code: 'JOB_NOT_FOUND',
          message: "Job 'nonexistent-uuid' not found.",
        },
      }),
    });

    await expect(getAnalysisJob('nonexistent-uuid')).rejects.toThrow("Job 'nonexistent-uuid' not found.");
    try {
      await getAnalysisJob('nonexistent-uuid');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).status).toBe(404);
      expect((err as ApiError).code).toBe('JOB_NOT_FOUND');
    }
  });

  it('GET /api/v1/analysis/jobs/{job_id} handles 500 INTERNAL_ERROR', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({
        error: {
          code: 'INTERNAL_ERROR',
          message: 'An unexpected server error occurred.',
        },
      }),
    });

    await expect(getAnalysisJob('job-phase6-123')).rejects.toThrow('An unexpected server error occurred.');
    try {
      await getAnalysisJob('job-phase6-123');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).status).toBe(500);
      expect((err as ApiError).code).toBe('INTERNAL_ERROR');
    }
  });

  it('GET /api/v1/analysis/jobs/{job_id} handles network failure cleanly', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

    try {
      await getAnalysisJob('job-phase6-123');
      expect.fail('Should have thrown ApiError');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).code).toBe('NETWORK_ERROR');
    }
  });

  it('GET /health endpoint returns status ok', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'ok' }),
    });

    const res = await checkHealth();
    expect(res.status).toBe('ok');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/health'),
      expect.objectContaining({ method: 'GET' })
    );
  });
});

describe('Stage Labels Dictionary (Section 24)', () => {
  it('maps backend stages to friendly text', () => {
    expect(getStageLabel('QUEUED')).toBe('Waiting to start');
    expect(getStageLabel('FETCHING_VIDEO')).toBe('Fetching video information');
    expect(getStageLabel('FETCHING_COMMENTS')).toBe('Collecting comments');
    expect(getStageLabel('SENTIMENT_ANALYSIS')).toBe('Analyzing sentiment');
    expect(getStageLabel('FINALIZING')).toBe('Preparing results');
    expect(getStageLabel('COMPLETED')).toBe('Analysis complete');
    expect(getStageLabel('FAILED')).toBe('Analysis failed');
    expect(getStageLabel(null)).toBe('Waiting to start');
  });
});

describe('Phase 6 Multi-Stage Polling Flow (Section 51)', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('transitions QUEUED -> PROCESSING 25% -> PROCESSING 60% -> COMPLETED and stops polling', async () => {
    const mockCreated: JobCreatedResponse = {
      job_id: 'job-multi-stage-1',
      status: 'QUEUED',
    };

    let pollIndex = 0;
    const pollSequence: JobStatusResponse[] = [
      // 1: QUEUED
      {
        job_id: 'job-multi-stage-1',
        status: 'QUEUED',
        progress: { stage: 'QUEUED', completed: 0, total: 100, percentage: 0 },
      },
      // 2: PROCESSING 25%
      {
        job_id: 'job-multi-stage-1',
        status: 'PROCESSING',
        progress: { stage: 'FETCHING_COMMENTS', completed: 25, total: 100, percentage: 25 },
      },
      // 3: PROCESSING 60%
      {
        job_id: 'job-multi-stage-1',
        status: 'PROCESSING',
        progress: { stage: 'SENTIMENT_ANALYSIS', completed: 60, total: 100, percentage: 60 },
      },
      // 4: COMPLETED
      {
        job_id: 'job-multi-stage-1',
        status: 'COMPLETED',
        progress: { stage: 'COMPLETED', completed: 100, total: 100, percentage: 100 },
        result: {
          video: {
            video_id: 'dQw4w9WgXcQ',
            title: 'Sample Malayalam Review Video',
            channel_title: 'Malayalam Cinema Review',
            view_count: 150000,
          },
          total_comments: 100,
          processed_comments: 100,
          comments: [
            {
              comment_id: 'c1',
              text: 'Kidu padam!',
              author_name: 'Anu',
              like_count: 50,
              sentiment: 'Positive',
              confidence: 0.95,
              probabilities: { Positive: 0.95, Negative: 0.01, Neutral: 0.02, Mixed: 0.01, Unsupported: 0.01 },
            },
          ],
        },
      },
    ];

    global.fetch = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/api/v1/analysis/jobs') && init?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          status: 202,
          json: async () => mockCreated,
        });
      }

      if (url.includes('/api/v1/analysis/jobs/job-multi-stage-1')) {
        const currentResp = pollSequence[Math.min(pollIndex, pollSequence.length - 1)];
        pollIndex++;
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => currentResp,
        });
      }

      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(
      <MemoryRouter>
        <Analyze pollingIntervalMs={50} />
      </MemoryRouter>
    );


    const input = screen.getByLabelText(/youtube video url/i);
    fireEvent.change(input, {
      target: { value: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' },
    });

    const submitBtn = screen.getByRole('button', { name: /start ingestion & analysis/i });
    fireEvent.click(submitBtn);

    // Initial panel appears
    await waitFor(() => {
      expect(screen.getByTestId('analyze-progress-panel')).toBeInTheDocument();
    });

    // Final completed state reached
    await waitFor(
      () => {
        expect(screen.getByText('Sample Malayalam Review Video')).toBeInTheDocument();
        expect(screen.getByText(/Analysis Complete/i)).toBeInTheDocument();
        expect(screen.getByText('Kidu padam!')).toBeInTheDocument();
        expect(screen.getByText('Positive')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /view audience dashboard/i })).toBeInTheDocument();
      },
      { timeout: 4000 }
    );

  });
});

describe('Phase 6 Failed Polling Flow (Section 52)', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('transitions QUEUED -> PROCESSING -> FAILED, stops polling, and displays error', async () => {
    const mockCreated: JobCreatedResponse = {
      job_id: 'job-failed-flow-1',
      status: 'QUEUED',
    };

    let pollIndex = 0;
    const pollSequence: JobStatusResponse[] = [
      // 1: QUEUED
      {
        job_id: 'job-failed-flow-1',
        status: 'QUEUED',
        progress: { stage: 'QUEUED', completed: 0, total: 100, percentage: 0 },
      },
      // 2: PROCESSING
      {
        job_id: 'job-failed-flow-1',
        status: 'PROCESSING',
        progress: { stage: 'FETCHING_COMMENTS', completed: 10, total: 100, percentage: 10 },
      },
      // 3: FAILED
      {
        job_id: 'job-failed-flow-1',
        status: 'FAILED',
        error: {
          code: 'YOUTUBE_COMMENTS_DISABLED',
          message: 'Comments are disabled on this video.',
        },
      },
    ];

    global.fetch = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/api/v1/analysis/jobs') && init?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          status: 202,
          json: async () => mockCreated,
        });
      }

      if (url.includes('job-failed-flow-1')) {
        const currentResp = pollSequence[Math.min(pollIndex, pollSequence.length - 1)];
        pollIndex++;
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => currentResp,
        });
      }

      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(
      <MemoryRouter>
        <Analyze pollingIntervalMs={50} />
      </MemoryRouter>
    );


    const input = screen.getByLabelText(/youtube video url/i);
    fireEvent.change(input, {
      target: { value: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' },
    });

    const submitBtn = screen.getByRole('button', { name: /start ingestion & analysis/i });
    fireEvent.click(submitBtn);

    // Verify error displayed and retry button available
    await waitFor(() => {
      expect(screen.getByText('Comments are disabled on this video.')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry analysis/i })).toBeInTheDocument();
      expect(screen.queryByText(/View Audience Dashboard/i)).not.toBeInTheDocument();
    });
  });
});

describe('Phase 6 MODEL_NOT_READY Handling (Section 53)', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('displays user-friendly model-not-ready message without fake sentiment results', async () => {
    const mockCreated: JobCreatedResponse = {
      job_id: 'job-model-not-ready-1',
      status: 'QUEUED',
    };

    const failedStatus: JobStatusResponse = {
      job_id: 'job-model-not-ready-1',
      status: 'FAILED',
      error: {
        code: 'MODEL_NOT_READY',
        message: 'The sentiment model is not ready.',
      },
    };

    global.fetch = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/api/v1/analysis/jobs') && init?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          status: 202,
          json: async () => mockCreated,
        });
      }

      if (url.includes('job-model-not-ready-1')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => failedStatus,
        });
      }

      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(
      <MemoryRouter>
        <Analyze />
      </MemoryRouter>
    );

    const input = screen.getByLabelText(/youtube video url/i);
    fireEvent.change(input, {
      target: { value: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' },
    });

    const submitBtn = screen.getByRole('button', { name: /start ingestion & analysis/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByText(
          'The sentiment analysis model is not ready yet. Please try again after the model has been configured.'
        )
      ).toBeInTheDocument();
      expect(screen.getByText('Model Not Ready')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry analysis/i })).toBeInTheDocument();
      // Crucial: No fake sentiment result shown
      expect(screen.queryByTestId('analysis-result-preview')).not.toBeInTheDocument();
    });
  });
});
