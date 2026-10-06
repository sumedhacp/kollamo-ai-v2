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
  detected_language: DetectedLanguage;
  detected_script: DetectedScript;
  sentiment: SentimentClass;
  confidence: number;
  class_probabilities: ClassProbabilities;
  translation_status: 'translated' | 'untranslated' | 'not_needed' | 'failed';
  translated_text?: string;
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
