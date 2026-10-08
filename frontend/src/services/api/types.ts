/**
 * Type definitions for Kollamo.ai Phase 6 Frontend ↔ Backend Integration Contracts.
 * Conforms strictly to FastAPI backend schemas in backend/app/schemas/analysis.py.
 */

export type CommentLimit = 50 | 100 | 250 | 500 | 'ALL';

export type SortBy = 'most_liked' | 'newest' | 'oldest';

export type Sentiment =
  | 'Positive'
  | 'Negative'
  | 'Neutral'
  | 'Mixed'
  | 'Unsupported';

export type SentimentClassFive = Sentiment;

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

export interface SentimentProbabilities {
  Positive: number;
  Negative: number;
  Neutral: number;
  Mixed: number;
  Unsupported: number;
}

export interface SentimentCounts {
  Positive: number;
  Negative: number;
  Neutral: number;
  Mixed: number;
  Unsupported: number;
}

export interface AnalysisComment {
  comment_id: string;
  text: string;
  author_name?: string | null;
  author_display_name?: string | null;
  like_count: number;
  published_at?: string | null;
  sentiment: Sentiment;
  confidence: number;
  probabilities: SentimentProbabilities | Record<string, number>;
}

export type CommentSentimentResult = AnalysisComment;

export interface AnalysisVideo {
  video_id: string;
  title: string;
  channel_title?: string | null;
  published_at?: string | null;
  comment_count_available?: number | null;
  view_count?: number | null;
  like_count?: number | null;
  comment_count?: number | null;
  description?: string | null;
  thumbnail_url?: string | null;
}

export type YouTubeVideoMetadata = AnalysisVideo;

export interface AnalysisSummary {
  requested_comment_limit: CommentLimit;
  returned_comment_count: number;
  sort_by: SortBy;
  sentiment_counts: SentimentCounts;
  comments: AnalysisComment[];
}

export interface AnalysisModelInfo {
  name: string;
  version: string;
}

export interface AnalysisProcessingInfo {
  processing_time_ms: number;
}

export interface AnalysisResult {
  video: AnalysisVideo;
  total_comments?: number;
  processed_comments?: number;
  comments?: AnalysisComment[];
  sentiment_counts?: SentimentCounts;
  analysis?: AnalysisSummary;
  model?: AnalysisModelInfo;
  processing?: AnalysisProcessingInfo;
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
