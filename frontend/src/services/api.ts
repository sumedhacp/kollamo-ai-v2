import {
  SingleSentimentResult,
  SampleSize,
  SortMode,
  AnalysisJob,
  CommentItem,
  HealthStatus,
  AnalyzeJobCreateResponse,
  ApiErrorEnvelope,
  TranslationResponse,
  AnalysisReportResponse,
} from '@/types';

/**
 * Standard API error class carrying status code, machine-readable error code,
 * and optional validation or diagnostic details.
 */
export class ApiError extends Error {
  public status: number;
  public code: string;
  public details?: unknown;

  constructor(message: string, status: number, code: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

// Configurable base URL, defaulting to '/api' (which is proxied by Vite dev server or reverse proxy)
const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '');

/**
 * Generic JSON request handler with standard RFC error envelope parsing.
 */
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Network request failed';
    throw new ApiError(
      `Network connection failed: ${message}. Please check if the FastAPI backend is running.`,
      0,
      'NETWORK_ERROR'
    );
  }

  if (!response.ok) {
    let errorCode = 'HTTP_ERROR';
    let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
    let errorDetails: unknown = undefined;

    try {
      const errorJson = (await response.json()) as ApiErrorEnvelope;
      if (errorJson && errorJson.error) {
        errorCode = errorJson.error.code || errorCode;
        errorMessage = errorJson.error.message || errorMessage;
        errorDetails = errorJson.error.details;
      }
    } catch {
      // Body was not JSON; use status text fallback
    }

    throw new ApiError(errorMessage, response.status, errorCode, errorDetails);
  }

  return response.json() as Promise<T>;
}

/**
 * API client service for Kollamo.ai backend.
 */
export const api = {
  /**
   * Health check: GET /api/health
   */
  async checkHealth(): Promise<HealthStatus> {
    return request<HealthStatus>('/health', {
      method: 'GET',
    });
  },

  /**
   * Single-comment sentiment inference: POST /api/sentiment
   */
  async analyzeSentiment(text: string, translate: boolean = true): Promise<SingleSentimentResult> {
    return request<SingleSentimentResult>('/sentiment', {
      method: 'POST',
      body: JSON.stringify({
        text,
        translate,
      }),
    });
  },

  /**
   * Create an asynchronous YouTube comment analysis job: POST /api/analyze
   */
  async createAnalysisJob(
    youtubeUrl: string,
    sampleSize: SampleSize = 250,
    sortMode: SortMode = 'top'
  ): Promise<AnalyzeJobCreateResponse> {
    const formattedSampleSize = sampleSize === 'ALL' ? 'all' : sampleSize;

    return request<AnalyzeJobCreateResponse>('/analyze', {
      method: 'POST',
      body: JSON.stringify({
        youtube_url: youtubeUrl,
        sample_size: formattedSampleSize,
        sort_mode: sortMode,
      }),
    });
  },

  /**
   * Poll/retrieve the current state and results of an analysis job: GET /api/analyze/{job_id}
   */
  async getJobStatus(jobId: string): Promise<AnalysisJob> {
    return request<AnalysisJob>(`/analyze/${encodeURIComponent(jobId)}`, {
      method: 'GET',
    });
  },

  /**
   * Manually trigger analysis processing on an existing job (worker fallback): POST /api/analyze/{job_id}/process
   */
  async processJob(jobId: string): Promise<{ job_id: string; status: string; message: string }> {
    return request<{ job_id: string; status: string; message: string }>(
      `/analyze/${encodeURIComponent(jobId)}/process`,
      {
        method: 'POST',
      }
    );
  },

  /**
   * Retrieve comments for an analysis job with optional filters: GET /api/analyze/{job_id}/comments
   */
  async getJobComments(
    jobId: string,
    params: {
      sentiment?: string;
      script?: string;
      search?: string;
      limit?: number;
      offset?: number;
    } = {}
  ): Promise<CommentItem[]> {
    const searchParams = new URLSearchParams();
    if (params.sentiment) searchParams.set('sentiment', params.sentiment);
    if (params.script) searchParams.set('script', params.script);
    if (params.search) searchParams.set('search', params.search);
    if (params.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params.offset !== undefined) searchParams.set('offset', String(params.offset));

    const qs = searchParams.toString();
    const endpoint = `/analyze/${encodeURIComponent(jobId)}/comments${qs ? `?${qs}` : ''}`;
    return request<CommentItem[]>(endpoint, { method: 'GET' });
  },

  /**
   * Translate Malayalam or Manglish text: POST /api/translate
   */
  async translateText(
    text: string,
    sourceLanguage: string = 'auto',
    targetLanguage: string = 'en'
  ): Promise<TranslationResponse> {
    return request<TranslationResponse>('/translate', {
      method: 'POST',
      body: JSON.stringify({
        text,
        source_language: sourceLanguage,
        target_language: targetLanguage,
      }),
    });
  },

  /**
   * Retrieve structured report data for export: GET /api/analyze/{job_id}/report
   */
  async getJobReport(jobId: string): Promise<AnalysisReportResponse> {
    return request<AnalysisReportResponse>(`/analyze/${encodeURIComponent(jobId)}/report`, {
      method: 'GET',
    });
  },

  /**
   * Download server-compiled PDF document: GET /api/analyze/{job_id}/report/pdf
   */
  async downloadJobPdf(jobId: string): Promise<Blob> {
    const url = `${BASE_URL}/analyze/${encodeURIComponent(jobId)}/report/pdf`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new ApiError('Failed to download PDF report', response.status, 'DOWNLOAD_FAILED');
    }
    return response.blob();
  },

  /**
   * Trigger comment translations for job: POST /api/analyze/{job_id}/translate-comments
   */
  async translateJobComments(
    jobId: string,
    limit: number = 25
  ): Promise<{ job_id: string; translated_count: number; remaining_untranslated: number }> {
    return request<{ job_id: string; translated_count: number; remaining_untranslated: number }>(
      `/analyze/${encodeURIComponent(jobId)}/translate-comments?limit=${limit}`,
      { method: 'POST' }
    );
  },
};
