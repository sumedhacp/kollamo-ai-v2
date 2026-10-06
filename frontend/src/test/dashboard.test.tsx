import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { Dashboard } from '@/pages/Dashboard';

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
});
