export type SentimentClass = 'positive' | 'negative' | 'neutral' | 'mixed' | 'unsupported';

export type DetectedScript = 'Malayalam' | 'Latin' | 'Mixed' | 'Unknown';

export type DetectedLanguage = 'ml' | 'en' | 'ml-en' | 'unknown';

export interface ClassProbabilities {
  positive: number;
  negative: number;
  neutral: number;
  mixed: number;
  unsupported: number;
}

export interface SingleSentimentResult {
  original_text: string;
  detected_language: DetectedLanguage | string;
  detected_script: DetectedScript | string;
  sentiment: SentimentClass;
  confidence: number;
  class_probabilities: ClassProbabilities;
  translation_status: string;
  translated_text?: string | null;
}

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

export type SortMode = 'top' | 'newest' | 'oldest';

export type SampleSize = 50 | 100 | 250 | 500 | 'ALL';

export interface VideoMetadata {
  video_id: string;
  title: string;
  channel_title: string;
  thumbnail_url?: string;
  view_count?: number;
}

export interface CommentItem {
  comment_id: string;
  author_display_name: string;
  author_avatar_url?: string;
  published_at: string;
  like_count: number;
  reply_count: number;
  original_text: string;
  detected_language: DetectedLanguage;
  detected_script: DetectedScript;
  sentiment: SentimentClass;
  confidence: number;
  translated_text?: string;
}

export interface SentimentCounts {
  positive: number;
  negative: number;
  neutral: number;
  mixed: number;
  unsupported: number;
}

export interface SentimentPercentages {
  positive: number;
  negative: number;
  neutral: number;
  mixed: number;
  unsupported: number;
}

export interface EngagementMetrics {
  total_likes: number;
  average_likes_per_sentiment: {
    positive: number;
    negative: number;
    neutral: number;
    mixed: number;
    unsupported: number;
  };
}

export interface AudienceSummary {
  total_analyzed: number;
  sentiment_counts: SentimentCounts;
  sentiment_percentages: SentimentPercentages;
  engagement_metrics: EngagementMetrics;
}

export interface AnalysisJob {
  job_id: string;
  status: JobStatus;
  progress: number; // 0.0 to 1.0
  processed_comments: number;
  total_comments: number;
  current_stage?: string;
  video?: VideoMetadata;
  summary?: AudienceSummary;
  comments?: CommentItem[];
  created_at: string;
  completed_at?: string;
  error?: string | null;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: unknown;
}

export interface ApiErrorEnvelope {
  error: ApiErrorDetail;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  environment: string;
  database: string;
  redis: string;
  ml_model: string;
}

export interface AnalyzeJobCreateResponse {
  job_id: string;
  status: JobStatus | string;
  message: string;
  created_at: string;
}

export interface TranslationResponse {
  original_text: string;
  translated_text: string;
  source_language: string;
  target_language: string;
  confidence: number;
  detected_script?: string;
  intermediate_malayalam?: string;
  method: string;
  status: string;
}

export interface ReportVideoInfo {
  video_id: string;
  title: string;
  channel_title: string;
  url: string;
  published_at?: string;
}

export interface ReportSentimentSummary {
  counts: SentimentCounts;
  percentages: SentimentPercentages;
  dominant_sentiment: string;
  net_approval_index: number;
  consensus_label: string;
  average_confidence: number;
}

export interface ReportEngagementSummary {
  total_likes: number;
  average_likes_per_comment: number;
  average_likes_per_sentiment: Record<string, number>;
}

export interface ReportLinguisticBreakdown {
  malayalam_script_count: number;
  manglish_count: number;
  code_mixed_count: number;
  english_count: number;
  malayalam_percentage: number;
  manglish_percentage: number;
  code_mixed_percentage: number;
  english_percentage: number;
}

export interface ReportCommentItem {
  comment_id: string;
  author: string;
  original_text: string;
  translated_text?: string;
  sentiment: SentimentClass;
  confidence: number;
  like_count: number;
  detected_script: string;
}

export interface ReportMethodology {
  model_name: string;
  model_version: string;
  architecture: string;
  sentiment_classes: string[];
  translation_engine: string;
  evaluation_framework: string;
}

export interface AnalysisReportResponse {
  job_id: string;
  title: string;
  generated_at: string;
  total_comments_analyzed: number;
  video_info: ReportVideoInfo;
  sentiment_summary: ReportSentimentSummary;
  engagement_summary: ReportEngagementSummary;
  linguistic_breakdown: ReportLinguisticBreakdown;
  top_positive_comments: ReportCommentItem[];
  top_negative_comments: ReportCommentItem[];
  methodology: ReportMethodology;
  disclaimer: string;
}
