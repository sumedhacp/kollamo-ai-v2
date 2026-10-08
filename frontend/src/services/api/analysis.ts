/**
 * Dedicated Analysis API Service for Kollamo.ai Phase 6.
 * Implements createAnalysisJob and getAnalysisJob targeting Phase 5 FastAPI endpoints.
 */

import { request } from './client';
import {
  AnalysisJobRequest,
  JobCreatedResponse,
  JobStatusResponse,
} from './types';

/**
 * Stage labels dictionary mapping backend identifiers to friendly user-facing labels.
 */
export const STAGE_LABELS: Record<string, string> = {
  QUEUED: 'Waiting to start',
  FETCHING_VIDEO: 'Fetching video information',
  FETCHING_COMMENTS: 'Collecting comments',
  SENTIMENT_ANALYSIS: 'Analyzing sentiment',
  FINALIZING: 'Preparing results',
  COMPLETED: 'Analysis complete',
  FAILED: 'Analysis failed',
};

/**
 * Returns user-facing friendly stage label.
 */
export function getStageLabel(stage?: string | null): string {
  if (!stage) return 'Waiting to start';
  const upper = stage.toUpperCase();
  return STAGE_LABELS[upper] || stage.replace(/_/g, ' ');
}

/**
 * Creates an asynchronous YouTube sentiment analysis job.
 * Dispatches POST /api/v1/analysis/jobs and receives HTTP 202 with job_id.
 */
export async function createAnalysisJob(
  req: AnalysisJobRequest
): Promise<JobCreatedResponse> {
  return request<JobCreatedResponse>('/api/v1/analysis/jobs', {
    method: 'POST',
    body: JSON.stringify({
      video_url: req.video_url,
      comment_limit: req.comment_limit,
      sort_by: req.sort_by,
    }),
  });
}

/**
 * Queries current execution status and live progress indicators for an analysis job.
 * Dispatches GET /api/v1/analysis/jobs/{job_id}.
 */
export async function getAnalysisJob(
  jobId: string,
  options?: { signal?: AbortSignal; timeoutMs?: number }
): Promise<JobStatusResponse> {
  return request<JobStatusResponse>(
    `/api/v1/analysis/jobs/${encodeURIComponent(jobId)}`,
    {
      method: 'GET',
      signal: options?.signal,
      timeoutMs: options?.timeoutMs,
    }
  );
}

/**
 * Basic health check endpoint: GET /health
 */
export async function checkHealth(): Promise<{ status: string }> {
  return request<{ status: string }>('/health', {
    method: 'GET',
  });
}
