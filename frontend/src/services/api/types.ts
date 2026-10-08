/**
 * Type definitions for Kollamo.ai Phase 6 Frontend ↔ Backend Integration Contracts.
 * Conforms strictly to FastAPI backend schemas in backend/app/schemas/analysis.py.
 */

export type CommentLimit = 50 | 100 | 250 | 500 | 'ALL';

export type SortBy = 'most_liked' | 'newest' | 'oldest';

export type JobStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface JobProgress {
  stage: string;
  completed: number;
  total: number | null;
  percentage: number | null;
}

export interface AnalysisJobRequest {
  video_url: string;
  comment_limit: CommentLimit;
  sort_by: SortBy;
}

export interface JobCreatedResponse {
  job_id: string;
  status: 'QUEUED';
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: unknown;
}

export interface ApiErrorEnvelope {
  error: ApiErrorDetail;
}

export type SentimentClassFive =
  | 'Positive'
  | 'Negative'
  | 'Neutral'
  | 'Mixed'
  | 'Unsupported';

export interface CommentSentimentResult {
  comment_id: string;
  text: string;
  author_name?: string | null;
  like_count: number;
  published_at?: string | null;
  sentiment: SentimentClassFive;
  confidence: number;
  probabilities: Record<string, number>;
}

export interface YouTubeVideoMetadata {
  video_id: string;
  title: string;
  channel_title: string;
  description?: string | null;
  published_at?: string | null;
  view_count?: number | null;
  like_count?: number | null;
  comment_count?: number | null;
  thumbnail_url?: string | null;
}

export interface AnalysisResult {
  video: YouTubeVideoMetadata;
  total_comments: number;
  processed_comments: number;
  comments: CommentSentimentResult[];
  model_name?: string | null;
  model_version?: string | null;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress?: JobProgress | null;
  result?: AnalysisResult | null;
  error?: ApiErrorDetail | null;
}

export type AnalysisJobState =
  | 'IDLE'
  | 'SUBMITTING'
  | 'QUEUED'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'FAILED';
