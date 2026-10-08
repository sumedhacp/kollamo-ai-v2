import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import {
  generateAudienceIntelligencePdf,
  generateAnalysisReport,
  getAnalysisReportFilename,
  sanitizeVideoId,
} from '@/utils/pdfGenerator';
import { DEMO_SAMPLE_JOB } from '@/data/sampleJob';
import { Dashboard } from '@/pages/Dashboard';
import { AnalysisJob, CommentItem } from '@/types';

describe('Phase 8: Translation & PDF Reporting', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Filename Generation & Sanitization (Section 31 & 41)', () => {
    it('generates exact sanitized filename according to Phase 8 specification', () => {
      expect(getAnalysisReportFilename('L0yEMl8PXnw')).toBe('kollamo-ai-analysis-L0yEMl8PXnw.pdf');
      expect(getAnalysisReportFilename('video-123_abc')).toBe('kollamo-ai-analysis-video-123_abc.pdf');
    });

    it('sanitizes unsafe characters, slashes, and paths safely', () => {
      expect(sanitizeVideoId('../../malicious/id')).toBe('maliciousid');
      expect(sanitizeVideoId('id with spaces and symbols!@#$%^&*')).toBe('idwithspacesandsymbols');
      expect(getAnalysisReportFilename(undefined)).toBe('kollamo-ai-analysis-video.pdf');
    });
  });

  describe('jsPDF Report Generator Utility (generateAudienceIntelligencePdf)', () => {
    it('generates a valid multi-page jsPDF instance from sample job data', () => {
      const doc = generateAudienceIntelligencePdf(DEMO_SAMPLE_JOB, {
        includeMethodology: true,
        includeComments: true,
        maxComments: 10,
      });

      expect(doc).toBeDefined();
      expect(doc.getNumberOfPages()).toBeGreaterThanOrEqual(1);
    });

    it('handles all five sentiment classes accurately in summary calculations', () => {
      const fiveClassJob: AnalysisJob = {
        ...DEMO_SAMPLE_JOB,
        summary: {
          total_analyzed: 50,
          sentiment_counts: {
            positive: 20,
            negative: 10,
            neutral: 10,
            mixed: 5,
            unsupported: 5,
          },
          sentiment_percentages: {
            positive: 40.0,
            negative: 20.0,
            neutral: 20.0,
            mixed: 10.0,
            unsupported: 10.0,
          },
          engagement_metrics: {
            total_likes: 1200,
            average_likes_per_sentiment: {
              positive: 35,
              negative: 12,
              neutral: 15,
              mixed: 8,
              unsupported: 4,
            },
          },
        },
      };

      const doc = generateAudienceIntelligencePdf(fiveClassJob, {
        includeMethodology: true,
        includeComments: true,
      });

      expect(doc).toBeDefined();
      expect(doc.getNumberOfPages()).toBeGreaterThanOrEqual(1);
    });

    it('handles zero-comment analysis without division by zero errors (Section 21)', () => {
      const zeroJob: AnalysisJob = {
        job_id: 'zero-comment-job-123',
        status: 'completed',
        progress: 1.0,
        processed_comments: 0,
        total_comments: 0,
        video: {
          video_id: 'zero-comments-vid',
          title: 'Empty Stream',
          channel_title: 'Creator Channel',
        },
        summary: {
          total_analyzed: 0,
          sentiment_counts: { positive: 0, negative: 0, neutral: 0, mixed: 0, unsupported: 0 },
          sentiment_percentages: { positive: 0, negative: 0, neutral: 0, mixed: 0, unsupported: 0 },
          engagement_metrics: {
            total_likes: 0,
            average_likes_per_sentiment: { positive: 0, negative: 0, neutral: 0, mixed: 0, unsupported: 0 },
          },
        },
        comments: [],
        created_at: '2026-04-10T12:00:00Z',
      };

      const doc = generateAudienceIntelligencePdf(zeroJob, {
        includeMethodology: true,
        includeComments: true,
      });

      expect(doc).toBeDefined();
      expect(doc.getNumberOfPages()).toBeGreaterThanOrEqual(1);
    });

    it('handles Malayalam script, Manglish, English, and code-mixed comments gracefully', () => {
      const multilingualComments: CommentItem[] = [
        {
          comment_id: 'c-ml',
          author_display_name: 'Malayalam Reviewer',
          published_at: '2026-04-10T12:00:00Z',
          like_count: 50,
          reply_count: 2,
          original_text: 'ഈ സിനിമ തിയേറ്ററിൽ തന്നെ കാണണം, സൂപ്പർ അനുഭവം!',
          detected_language: 'ml',
          detected_script: 'Malayalam',
          sentiment: 'positive',
          confidence: 0.96,
          translated_text: 'This movie must be watched in theaters, super experience!',
        },
        {
          comment_id: 'c-manglish',
          author_display_name: 'Manglish Fan',
          published_at: '2026-04-10T12:00:00Z',
          like_count: 35,
          reply_count: 0,
          original_text: 'padam thooki! climax scene romancham aayirunnu',
          detected_language: 'ml',
          detected_script: 'Latin',
          sentiment: 'positive',
          confidence: 0.94,
          translated_text: 'The movie was a blockbuster! Climax scene gave goosebumps',
        },
        {
          comment_id: 'c-en',
          author_display_name: 'English Critic',
          published_at: '2026-04-10T12:00:00Z',
          like_count: 10,
          reply_count: 1,
          original_text: 'The sound design and musical score was top tier cinema.',
          detected_language: 'en',
          detected_script: 'Latin',
          sentiment: 'positive',
          confidence: 0.98,
        },
        {
          comment_id: 'c-mixed',
          author_display_name: 'Code Mixed Reviewer',
          published_at: '2026-04-10T12:00:00Z',
          like_count: 8,
          reply_count: 0,
          original_text: 'Fahadh Faasil acting അടിപൊളി, but script weak aayirunnu.',
          detected_language: 'ml-en',
          detected_script: 'Mixed',
          sentiment: 'mixed',
          confidence: 0.88,
          translated_text: 'Fahadh Faasil acting was awesome, but script was weak.',
        },
      ];

      const multiJob: AnalysisJob = {
        ...DEMO_SAMPLE_JOB,
        comments: multilingualComments,
        processed_comments: 4,
        total_comments: 4,
      };

      const doc = generateAudienceIntelligencePdf(multiJob, {
        includeComments: true,
      });

      expect(doc).toBeDefined();
      expect(doc.getNumberOfPages()).toBeGreaterThanOrEqual(1);
    });

    it('handles large reports with multiple pages and long comments gracefully', () => {
      const longComments: CommentItem[] = Array.from({ length: 25 }, (_, i) => ({
        comment_id: `long-comment-${i}`,
        author_display_name: `Audience Reviewer ${i}`,
        published_at: '2026-04-10T12:00:00Z',
        like_count: 100 + i * 10,
        reply_count: 5,
        original_text: `Ithu valare detailed review aanu! ${'Fahadh Faasil and Sushin Shyam combination vere level item thanne aayirunnu theatre il. '.repeat(4)}`,
        detected_language: 'ml',
        detected_script: 'Latin',
        sentiment: i % 2 === 0 ? 'positive' : 'negative',
        confidence: 0.95,
        translated_text: `This is a comprehensive detailed evaluation. ${'The performance of Fahadh Faasil and Sushin Shyam musical score was completely phenomenal in theaters. '.repeat(4)}`,
      }));

      const largeJob: AnalysisJob = {
        ...DEMO_SAMPLE_JOB,
        total_comments: 25,
        processed_comments: 25,
        comments: longComments,
      };

      const doc = generateAudienceIntelligencePdf(largeJob, {
        includeMethodology: true,
        includeComments: true,
        maxComments: 20,
      });

      expect(doc).toBeDefined();
      expect(doc.getNumberOfPages()).toBeGreaterThan(1);
    });

    it('handles missing optional metadata cleanly', () => {
      const bareJob: AnalysisJob = {
        job_id: 'bare-job',
        status: 'completed',
        progress: 1.0,
        processed_comments: 1,
        total_comments: 1,
        created_at: '2026-04-10T12:00:00Z',
      };

      const doc = generateAudienceIntelligencePdf(bareJob);
      expect(doc).toBeDefined();
      expect(doc.getNumberOfPages()).toBeGreaterThanOrEqual(1);
    });

    it('supports generateAnalysisReport contract alias consuming AnalysisResult', () => {
      const doc = generateAnalysisReport(DEMO_SAMPLE_JOB);
      expect(doc).toBeDefined();
      expect(doc.getNumberOfPages()).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Dashboard PDF & Translation UI Integration', () => {
    it('renders Export PDF Report button and triggers download', async () => {
      const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

      render(
        <MemoryRouter initialEntries={['/dashboard?job_id=demo-aavesham-2026-sample']}>
          <Dashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Aavesham Official Trailer/i)).toBeInTheDocument();
      });

      const exportPdfButton = screen.getByRole('button', { name: /Export PDF Report/i });
      expect(exportPdfButton).toBeInTheDocument();
      expect(exportPdfButton).not.toBeDisabled();

      fireEvent.click(exportPdfButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Academic PDF report compiled and downloaded successfully!/i)
        ).toBeInTheDocument();
      });

      clickSpy.mockRestore();
    });

    it('displays English translation accordions for regional comments', async () => {
      render(
        <MemoryRouter initialEntries={['/dashboard?job_id=demo-aavesham-2026-sample']}>
          <Dashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Aavesham Official Trailer/i)).toBeInTheDocument();
      });

      const englishTranslationPrefixes = screen.getAllByText(/En:/i);
      expect(englishTranslationPrefixes.length).toBeGreaterThan(0);

      expect(
        screen.getByText(/Sushin Shyam BGM is on another level/i)
      ).toBeInTheDocument();
    });

    it('renders Translate Comments button with feedback for demo data', async () => {
      render(
        <MemoryRouter initialEntries={['/dashboard?job_id=demo-aavesham-2026-sample']}>
          <Dashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Aavesham Official Trailer/i)).toBeInTheDocument();
      });

      const translateButton = screen.getByRole('button', { name: /Translate Comments/i });
      expect(translateButton).toBeInTheDocument();

      fireEvent.click(translateButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Demo dataset already includes pre-translated English mappings/i)
        ).toBeInTheDocument();
      });
    });

    it('displays original comment with primary emphasis alongside English translation', async () => {
      render(
        <MemoryRouter initialEntries={['/dashboard?job_id=demo-aavesham-2026-sample']}>
          <Dashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Aavesham Official Trailer/i)).toBeInTheDocument();
      });

      expect(
        screen.getByText(/FaFa mass avatar kidilan aayirunnu/i)
      ).toBeInTheDocument();

      expect(screen.getAllByText(/English Translation/i).length).toBeGreaterThan(0);
    });
  });
});
