import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { generateAudienceIntelligencePdf } from '@/utils/pdfGenerator';
import { DEMO_SAMPLE_JOB } from '@/data/sampleJob';
import { Dashboard } from '@/pages/Dashboard';
import { AnalysisJob, CommentItem } from '@/types';

describe('Phase 8: Translation & PDF Reporting', () => {
  beforeEach(() => {
    vi.clearAllMocks();
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

    it('handles short reports with few or zero comments cleanly', () => {
      const shortJob: AnalysisJob = {
        ...DEMO_SAMPLE_JOB,
        total_comments: 2,
        processed_comments: 2,
        comments: DEMO_SAMPLE_JOB.comments?.slice(0, 2) || [],
      };

      const doc = generateAudienceIntelligencePdf(shortJob, {
        includeMethodology: true,
        includeComments: true,
      });

      expect(doc).toBeDefined();
      expect(doc.getNumberOfPages()).toBeGreaterThanOrEqual(1);
    });

    it('handles large reports with multiple pages and long comments gracefully', () => {
      // Create artificial long comments to test pagination and text wrapping
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
      // Should break cleanly into multiple pages without throwing errors
      expect(doc.getNumberOfPages()).toBeGreaterThan(1);
    });

    it('respects optional flag to omit methodology or comments sections', () => {
      const docNoMethod = generateAudienceIntelligencePdf(DEMO_SAMPLE_JOB, {
        includeMethodology: false,
        includeComments: false,
      });

      expect(docNoMethod).toBeDefined();
      expect(docNoMethod.getNumberOfPages()).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Dashboard PDF & Translation UI Integration', () => {
    it('renders Export PDF Report button and triggers download', async () => {
      // Mock anchor click to prevent jsdom navigation error
      const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

      render(
        <MemoryRouter initialEntries={['/dashboard?job_id=demo-aavesham-2026-sample']}>
          <Dashboard />
        </MemoryRouter>
      );

      // Wait for demo job data to load
      await waitFor(() => {
        expect(screen.getByText(/Aavesham Official Trailer/i)).toBeInTheDocument();
      });

      // Verify Export PDF button is enabled and clickable
      const exportPdfButton = screen.getByRole('button', { name: /Export PDF Report/i });
      expect(exportPdfButton).toBeInTheDocument();
      expect(exportPdfButton).not.toBeDisabled();

      // Trigger export
      fireEvent.click(exportPdfButton);

      // Verify success feedback notification appears
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

      // Check for translation prefix "En:" and English translation text in comment row
      const englishTranslationPrefixes = screen.getAllByText(/En:/i);
      expect(englishTranslationPrefixes.length).toBeGreaterThan(0);

      // Verify translated text from demo dataset
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
  });
});
