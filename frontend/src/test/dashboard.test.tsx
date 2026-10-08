import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { Dashboard } from '@/pages/Dashboard';
import {
  VideoOverview,
  MetricCards,
  SentimentDistribution,
  SentimentLegend,
} from '@/components/dashboard';

describe('Audience Intelligence Dashboard (Phase 7)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  });

  it('renders EmptyState with Explore Demo button when no job_id is provided', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/Audience Analytics Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/No Analyzed Comments/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /explore demo review dataset/i })).toBeInTheDocument();
  });

  it('renders rich video intelligence and Net Approval Index for demo job', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard?job_id=demo-aavesham-2026-sample']}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </MemoryRouter>
    );

    // Video title and channel
    expect(screen.getByText(/Aavesham Official Trailer/i)).toBeInTheDocument();
    expect(screen.getByText(/Anwar Rasheed Entertainments/i)).toBeInTheDocument();

    // Net approval index (+60%)
    expect(screen.getByText(/Audience Net Approval Index:/i)).toBeInTheDocument();
    expect(screen.getByText('+60%')).toBeInTheDocument();
    expect(screen.getByText(/Overwhelmingly Positive/i)).toBeInTheDocument();

    // Summary counts
    expect(screen.getAllByText('68.0%').length).toBeGreaterThan(0);
    expect(screen.getAllByText('8.0%').length).toBeGreaterThan(0);
  });

  it('toggles between 5-Class Share and Scripts chart views', () => {
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

    expect(screen.getByText('Malayalam Script')).toBeInTheDocument();
    expect(screen.getByText(/Latin Script \(Manglish \/ English\)/i)).toBeInTheDocument();
    expect(screen.getByText('Code-Mixed Comments')).toBeInTheDocument();
  });

  it('filters comments by sentiment category pill', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard?job_id=demo-aavesham-2026-sample']}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </MemoryRouter>
    );

    // Click negative sentiment pill
    const negativeFilter = screen.getByRole('button', { name: /negative/i });
    fireEvent.click(negativeFilter);

    // Should display negative comments from demo dataset
    expect(screen.getByText(/Valare mosham direction/i)).toBeInTheDocument();
    expect(screen.getByText(/Sreejith Menon/i)).toBeInTheDocument();
  });

  it('filters comments by search query and discussion theme pills', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard?job_id=demo-aavesham-2026-sample']}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </MemoryRouter>
    );

    // Click BGM theme button
    const bgmBtn = screen.getByRole('button', { name: /bgm \/ music/i });
    fireEvent.click(bgmBtn);

    expect(screen.getByText(/Sushin Shyam BGM vere level/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /clear theme filter/i })).toBeInTheDocument();

    // Clear filter
    fireEvent.click(screen.getByRole('button', { name: /clear theme filter/i }));
    expect(screen.getByText(/Lekshmi S/i)).toBeInTheDocument();
  });

  it('triggers CSV and JSON data exports on button click', () => {
    const createObjectURLMock = vi.fn().mockReturnValue('blob:mock-url');
    const revokeObjectURLMock = vi.fn();
    window.URL.createObjectURL = createObjectURLMock;
    window.URL.revokeObjectURL = revokeObjectURLMock;

    render(
      <MemoryRouter initialEntries={['/dashboard?job_id=demo-aavesham-2026-sample']}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </MemoryRouter>
    );

    const csvBtn = screen.getByRole('button', { name: /csv/i });
    fireEvent.click(csvBtn);
    expect(createObjectURLMock).toHaveBeenCalled();

    const jsonBtn = screen.getByRole('button', { name: /json/i });
    fireEvent.click(jsonBtn);
    expect(createObjectURLMock).toHaveBeenCalledTimes(2);
  });

  it('navigates pagination controls for large comment sets', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard?job_id=demo-aavesham-2026-sample']}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/Page 1 of 2/i)).toBeInTheDocument();
    const nextBtn = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextBtn);

    expect(screen.getByText(/Page 2 of 2/i)).toBeInTheDocument();
    expect(screen.getByText(/Devika P/i)).toBeInTheDocument();

    const prevBtn = screen.getByRole('button', { name: /previous/i });
    fireEvent.click(prevBtn);
    expect(screen.getByText(/Page 1 of 2/i)).toBeInTheDocument();
  });

  describe('VideoOverview Component (Phase 7 UI)', () => {
    it('renders all video intelligence metadata, model telemetry, and external YouTube link', () => {
      render(
        <VideoOverview
          video={{
            video_id: 'abc123xyz89',
            title: 'Sample Malayalam Movie Teaser',
            channel_title: 'SillyMonks Mollywood',
            view_count: 500000,
            like_count: 25000,
            comment_count_available: 480,
            published_at: '2026-03-15T10:00:00Z',
          }}
          model={{ name: 'kollamo-muril-v2', version: '2.1.0' }}
          processing={{ processing_time_ms: 1450 }}
        />
      );

      expect(screen.getByText('Sample Malayalam Movie Teaser')).toBeInTheDocument();
      expect(screen.getByText('SillyMonks Mollywood')).toBeInTheDocument();
      expect(screen.getByText('500,000')).toBeInTheDocument();
      expect(screen.getByText('25,000')).toBeInTheDocument();
      expect(screen.getByText('480')).toBeInTheDocument();
      expect(screen.getByText(/kollamo-muril-v2/i)).toBeInTheDocument();
      expect(screen.getByText(/1.45s/i)).toBeInTheDocument();

      const watchLink = screen.getByRole('link', { name: /open youtube video sample malayalam movie teaser in new tab/i });
      expect(watchLink).toHaveAttribute('href', 'https://www.youtube.com/watch?v=abc123xyz89');
    });

    it('handles missing optional video metadata gracefully with Unavailable', () => {
      render(
        <VideoOverview
          video={{
            video_id: 'minimal1234',
            title: 'Minimal Metadata Video',
            channel_title: null,
            view_count: null,
            like_count: null,
            comment_count_available: null,
            published_at: null,
          }}
        />
      );

      expect(screen.getByText('Minimal Metadata Video')).toBeInTheDocument();
      expect(screen.getByText(/channel unavailable/i)).toBeInTheDocument();
      expect(screen.getAllByText(/unavailable/i).length).toBeGreaterThanOrEqual(4);
    });
  });

  describe('MetricCards Component (Phase 7 UI)', () => {
    it('renders six metric cards with exact counts and calculated percentage of analyzed comments', () => {
      render(
        <MetricCards
          totalAnalyzed={200}
          sentimentCounts={{
            Positive: 100,
            Negative: 40,
            Neutral: 30,
            Mixed: 20,
            Unsupported: 10,
          }}
        />
      );

      expect(screen.getByText('Analyzed Comments')).toBeInTheDocument();
      expect(screen.getByText('200')).toBeInTheDocument();

      expect(screen.getByText('Positive')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('50.0%')).toBeInTheDocument();

      expect(screen.getByText('Negative')).toBeInTheDocument();
      expect(screen.getByText('40')).toBeInTheDocument();
      expect(screen.getByText('20.0%')).toBeInTheDocument();

      expect(screen.getByText('Neutral')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument();
      expect(screen.getByText('15.0%')).toBeInTheDocument();

      expect(screen.getByText('Mixed')).toBeInTheDocument();
      expect(screen.getByText('20')).toBeInTheDocument();
      expect(screen.getByText('10.0%')).toBeInTheDocument();

      expect(screen.getByText('Unsupported')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('5.0%')).toBeInTheDocument();

      expect(screen.getAllByText('of analyzed comments').length).toBe(5);
    });

    it('safely handles zero total analyzed comments without NaN or runtime errors', () => {
      render(
        <MetricCards
          totalAnalyzed={0}
          sentimentCounts={{
            Positive: 0,
            Negative: 0,
            Neutral: 0,
            Mixed: 0,
            Unsupported: 0,
          }}
        />
      );

      expect(screen.getByText('Analyzed Comments')).toBeInTheDocument();
      expect(screen.getAllByText('0.0%').length).toBe(5);
    });
  });

  describe('SentimentLegend Component (Phase 7 Analytics)', () => {
    it('renders all 5 semantic sentiment classes with counts and percentage shares', () => {
      const onSelectMock = vi.fn();
      render(
        <SentimentLegend
          totalAnalyzed={500}
          sentimentCounts={{
            Positive: 250,
            Negative: 100,
            Neutral: 75,
            Mixed: 50,
            Unsupported: 25,
          }}
          onSelect={onSelectMock}
        />
      );

      expect(screen.getByText('Positive')).toBeInTheDocument();
      expect(screen.getByText('250')).toBeInTheDocument();
      expect(screen.getByText('50.0%')).toBeInTheDocument();

      expect(screen.getByText('Negative')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('20.0%')).toBeInTheDocument();

      expect(screen.getByText('Neutral')).toBeInTheDocument();
      expect(screen.getByText('75')).toBeInTheDocument();
      expect(screen.getByText('15.0%')).toBeInTheDocument();

      expect(screen.getByText('Mixed')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
      expect(screen.getByText('10.0%')).toBeInTheDocument();

      expect(screen.getByText('Unsupported')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument();
      expect(screen.getByText('5.0%')).toBeInTheDocument();

      // Click on Positive class item
      const positiveItem = screen.getByText('Positive').closest('[role="listitem"]')!;
      fireEvent.click(positiveItem);
      expect(onSelectMock).toHaveBeenCalledWith('Positive');
    });

    it('safely renders zero percentages when totalAnalyzed is 0', () => {
      render(
        <SentimentLegend
          totalAnalyzed={0}
          sentimentCounts={{
            Positive: 0,
            Negative: 0,
            Neutral: 0,
            Mixed: 0,
            Unsupported: 0,
          }}
        />
      );

      expect(screen.getAllByText('0.0%').length).toBe(5);
    });
  });

  describe('SentimentDistribution Component (Phase 7 Analytics)', () => {
    it('renders distribution container, toggles Donut/Bar modes, and shows Net Approval badge', () => {
      const onSentimentClickMock = vi.fn();
      render(
        <SentimentDistribution
          totalAnalyzed={100}
          sentimentCounts={{
            Positive: 68,
            Negative: 8,
            Neutral: 14,
            Mixed: 8,
            Unsupported: 2,
          }}
          netApprovalIndex={60}
          onSentimentClick={onSentimentClickMock}
        />
      );

      expect(screen.getByText('Five-Class Sentiment Distribution')).toBeInTheDocument();
      expect(screen.getByText('Net: +60%')).toBeInTheDocument();

      // View switcher buttons
      const donutTab = screen.getByRole('tab', { name: /donut/i });
      const barTab = screen.getByRole('tab', { name: /bar/i });
      expect(donutTab).toBeInTheDocument();
      expect(barTab).toBeInTheDocument();

      // Toggle to Bar chart mode
      fireEvent.click(barTab);
      expect(barTab).toHaveAttribute('aria-selected', 'true');

      // Toggle back to Donut mode
      fireEvent.click(donutTab);
      expect(donutTab).toHaveAttribute('aria-selected', 'true');

      // Legend inside distribution
      expect(screen.getByTestId('sentiment-legend')).toBeInTheDocument();
    });

    it('renders clean empty state message when totalAnalyzed is 0', () => {
      render(
        <SentimentDistribution
          totalAnalyzed={0}
          sentimentCounts={{
            Positive: 0,
            Negative: 0,
            Neutral: 0,
            Mixed: 0,
            Unsupported: 0,
          }}
        />
      );

      expect(screen.getByText('No comments analyzed')).toBeInTheDocument();
    });
  });
});
