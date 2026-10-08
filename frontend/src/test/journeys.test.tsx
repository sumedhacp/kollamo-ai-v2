import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { Sandbox } from '@/pages/Sandbox';
import { Analyze } from '@/pages/Analyze';
import { Dashboard } from '@/pages/Dashboard';
import { SingleSentimentResult } from '@/types';


describe('End-to-End User Journeys (Phase 9 Hardening)', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
    global.fetch = vi.fn();
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  // =========================================================================
  // JOURNEY A: Sandbox Single Comment Inference & Multilingual Analysis
  // =========================================================================
  describe('Journey A: Sandbox Live Inference Journey', () => {
    it('executes full interactive flow: input entry, inference, probability breakdown, and translation', async () => {
      const mockResult: SingleSentimentResult = {
        original_text: 'Padam kidilan aayirunnu, Fahadh Faasil vere level performance!',
        detected_language: 'ml-en',
        detected_script: 'Latin',
        sentiment: 'positive',
        confidence: 0.96,
        class_probabilities: {
          positive: 0.96,
          negative: 0.01,
          neutral: 0.01,
          mixed: 0.01,
          unsupported: 0.01,
        },
        translation_status: 'translated',
        translated_text: 'The movie was amazing, Fahadh Faasil gave a next-level performance!',
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResult,
      });

      render(
        <MemoryRouter initialEntries={['/sandbox']}>
          <Routes>
            <Route path="/sandbox" element={<Sandbox />} />
          </Routes>
        </MemoryRouter>
      );

      // Verify page title and header
      expect(screen.getByText(/Comment Sentiment Sandbox/i)).toBeInTheDocument();
      expect(screen.getByText(/Live Neural Inference/i)).toBeInTheDocument();

      // Find textarea and enter Manglish comment
      const textarea = screen.getByLabelText(/Comment text for sentiment analysis/i);
      fireEvent.change(textarea, {
        target: { value: 'Padam kidilan aayirunnu, Fahadh Faasil vere level performance!' },
      });
      expect(textarea).toHaveValue('Padam kidilan aayirunnu, Fahadh Faasil vere level performance!');

      // Ensure translate checkbox is checked
      const translateCheckbox = screen.getByLabelText(/Enable English Translation/i);
      if (!(translateCheckbox as HTMLInputElement).checked) {
        fireEvent.click(translateCheckbox);
      }

      // Click "Analyze Sentiment" button
      const analyzeBtn = screen.getByRole('button', { name: /Analyze Sentiment/i });
      fireEvent.click(analyzeBtn);

      // Verify API was called with proper payload
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/sentiment',
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({
              text: 'Padam kidilan aayirunnu, Fahadh Faasil vere level performance!',
              translate: true,
            }),
          })
        );
      });

      // Verify inference output rendered in UI
      await waitFor(() => {
        expect(screen.getByTestId('sandbox-result-state')).toBeInTheDocument();
      });
      expect(screen.getAllByText('96.0%').length).toBeGreaterThanOrEqual(1);

      // Verify detected script & language
      expect(screen.getByText(/ml-en/i)).toBeInTheDocument();

      // Verify English translation card rendered
      expect(
        screen.getByText(/The movie was amazing, Fahadh Faasil gave a next-level performance!/i)
      ).toBeInTheDocument();
    });

    it('disables submit button on empty input and populates input when clicking sample pills', async () => {
      render(
        <MemoryRouter initialEntries={['/sandbox']}>
          <Routes>
            <Route path="/sandbox" element={<Sandbox />} />
          </Routes>
        </MemoryRouter>
      );

      const analyzeBtn = screen.getByRole('button', { name: /Analyze Sentiment/i });
      expect(analyzeBtn).toBeDisabled();

      // Click the first sample comment pill
      const samplePills = screen.getAllByRole('button').filter((b) =>
        b.getAttribute('class')?.includes('rounded-full')
      );
      if (samplePills.length > 0) {
        fireEvent.click(samplePills[0]);
        expect(analyzeBtn).not.toBeDisabled();
      }
    });

    it('handles backend error gracefully with error alert message', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({
          error: { code: 'INTERNAL_SERVER_ERROR', message: 'Model inference temporarily unavailable' },
        }),
      });

      render(
        <MemoryRouter initialEntries={['/sandbox']}>
          <Routes>
            <Route path="/sandbox" element={<Sandbox />} />
          </Routes>
        </MemoryRouter>
      );

      const textarea = screen.getByLabelText(/Comment text for sentiment analysis/i);
      fireEvent.change(textarea, { target: { value: 'Kollam bro' } });

      const analyzeBtn = screen.getByRole('button', { name: /Analyze Sentiment/i });
      fireEvent.click(analyzeBtn);

      await waitFor(() => {
        expect(screen.getByText(/Model inference temporarily unavailable/i)).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // JOURNEY B: YouTube URL Ingestion, Processing, and Progress Tracking
  // =========================================================================
  describe('Journey B: YouTube Ingestion & Analysis Workflow', () => {
    it('executes end-to-end ingestion: URL input, configuration, polling progress, and completion navigation', async () => {
      let pollCount = 0;
      global.fetch = vi.fn().mockImplementation((url: string, init?: RequestInit) => {

        if (
          typeof url === 'string' &&
          (url.includes('/api/v1/analysis/jobs') || url.includes('/api/analyze')) &&
          init?.method === 'POST'
        ) {
          return Promise.resolve({
            ok: true,
            status: 202,
            json: async () => ({
              job_id: 'job-phase9-test-123',
              status: 'QUEUED',
            }),
          });
        }
        if (typeof url === 'string' && url.includes('job-phase9-test-123')) {
          pollCount++;
          if (pollCount === 1) {
            return Promise.resolve({
              ok: true,
              status: 200,
              json: async () => ({
                job_id: 'job-phase9-test-123',
                status: 'PROCESSING',
                progress: {
                  stage: 'SENTIMENT_ANALYSIS',
                  completed: 25,
                  total: 50,
                  percentage: 50,
                },
              }),
            });
          }
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              job_id: 'job-phase9-test-123',
              status: 'COMPLETED',
              progress: {
                stage: 'COMPLETED',
                completed: 50,
                total: 50,
                percentage: 100,
              },
              result: {
                video: {
                  video_id: 'L0yEMl8PXnw',
                  title: 'Aavesham Official Trailer',
                  channel_title: 'Anwar Rasheed Entertainments',
                },
                total_comments: 50,
                processed_comments: 50,
                comments: [],
              },
            }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({}),
        });
      });

      render(
        <MemoryRouter initialEntries={['/analyze']}>
          <Routes>
            <Route path="/analyze" element={<Analyze />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </MemoryRouter>
      );

      // Verify Analyze page rendered
      expect(screen.getByText(/YouTube Comment Analysis/i)).toBeInTheDocument();

      // Enter YouTube URL
      const urlInput = screen.getByLabelText(/YouTube Video URL/i);
      fireEvent.change(urlInput, {
        target: { value: 'https://www.youtube.com/watch?v=L0yEMl8PXnw' },
      });

      // Submit ingestion form
      const submitBtn = screen.getByRole('button', { name: /Start Ingestion & Analysis/i });
      fireEvent.submit(submitBtn.closest('form')!);

      // Verify POST call was dispatched
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/analysis/jobs'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({
              video_url: 'https://www.youtube.com/watch?v=L0yEMl8PXnw',
              comment_limit: 100,
              sort_by: 'most_liked',
            }),
          })
        );
      });


      // Verify polling progress and final completion state
      await waitFor(
        () => {
          expect(screen.getByText(/Analysis Complete/i)).toBeInTheDocument();
        },
        { timeout: 4000 }
      );

      // Verify "View Audience Dashboard" button is available
      const viewDashboardBtn = screen.getByRole('button', { name: /View Audience Dashboard/i });
      expect(viewDashboardBtn).toBeInTheDocument();
    });

    it('validates invalid YouTube URLs client-side before dispatching', async () => {
      render(
        <MemoryRouter initialEntries={['/analyze']}>
          <Routes>
            <Route path="/analyze" element={<Analyze />} />
          </Routes>
        </MemoryRouter>
      );

      const urlInput = screen.getByLabelText(/YouTube Video URL/i);
      fireEvent.change(urlInput, {
        target: { value: 'https://not-youtube.com/video/12345' },
      });

      const submitBtn = screen.getByRole('button', { name: /Start Ingestion & Analysis/i });
      fireEvent.submit(submitBtn.closest('form')!);

      await waitFor(() => {
        expect(screen.getByText(/Invalid YouTube URL/i)).toBeInTheDocument();
      });
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  // =========================================================================
  // JOURNEY C: Dashboard Exploration, Filtering, Translation, and PDF Export
  // =========================================================================
  describe('Journey C: Audience Dashboard Filtering, Translation & PDF Export', () => {
    it('executes full analytical journey: KPI review, sentiment filtering, search, and PDF generation', async () => {
      render(
        <MemoryRouter initialEntries={['/dashboard?job_id=demo-aavesham-2026-sample']}>
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </MemoryRouter>
      );

      // 1. Verify Video Header & Net Approval Index
      expect(screen.getByText(/Aavesham Official Trailer/i)).toBeInTheDocument();
      expect(screen.getByText(/Audience Net Approval Index:/i)).toBeInTheDocument();
      expect(screen.getByText('+60%')).toBeInTheDocument();
      expect(screen.getByText(/Overwhelmingly Positive/i)).toBeInTheDocument();

      // 2. Test Sentiment Filter Chip selection
      const negativeFilter = screen.getByRole('button', { name: /negative/i });
      fireEvent.click(negativeFilter);
      expect(screen.getByText(/Valare mosham direction/i)).toBeInTheDocument();

      // 3. Test Comment Search Input
      const searchInput = screen.getByPlaceholderText(/Search comments or author\.\.\./i);
      fireEvent.change(searchInput, { target: { value: 'Sreejith' } });
      expect(searchInput).toHaveValue('Sreejith');

      // 4. Test Sorting Dropdown
      const sortSelect = screen.getByRole('combobox', { name: /Sort comments/i });
      fireEvent.change(sortSelect, { target: { value: 'confidence' } });
      expect(sortSelect).toHaveValue('confidence');

      // 5. Trigger PDF Report Export
      const exportPdfBtn = screen.getByRole('button', { name: /Export PDF Report/i });
      expect(exportPdfBtn).toBeInTheDocument();
      fireEvent.click(exportPdfBtn);

      // Verify the PDF download success notice appears in UI
      await waitFor(() => {
        expect(
          screen.getByText(/Academic PDF report compiled and downloaded successfully!/i)
        ).toBeInTheDocument();
      });
    });

    it('switches between 5-Class Share and Scripts distribution charts seamlessly', () => {
      render(
        <MemoryRouter initialEntries={['/dashboard?job_id=demo-aavesham-2026-sample']}>
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('5-Class Share')).toBeInTheDocument();
      const scriptsTab = screen.getByRole('button', { name: 'Scripts' });
      fireEvent.click(scriptsTab);

      // Scripts breakdown view should be active
      expect(screen.getByText(/Linguistic breakdown between Malayalam script/i)).toBeInTheDocument();
      expect(screen.getByText('Malayalam Script')).toBeInTheDocument();
      expect(screen.getByText(/Latin Script \(Manglish \/ English\)/i)).toBeInTheDocument();
      expect(screen.getByText('Code-Mixed Comments')).toBeInTheDocument();
    });
  });
});
