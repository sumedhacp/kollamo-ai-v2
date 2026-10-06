import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Home } from '@/pages/Home';
import { Sandbox } from '@/pages/Sandbox';
import { Analyze } from '@/pages/Analyze';
import { Dashboard } from '@/pages/Dashboard';

describe('Frontend Pages & Flows', () => {
  it('renders Home page with hero, problem section, and CTA', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    );

    expect(screen.getByText(/Understand What Malayalam Audiences/i)).toBeInTheDocument();
    expect(screen.getByText(/Why Standard Sentiment Tools Fail on Regional Comments/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try comment sandbox/i })).toBeInTheDocument();
  });

  it('renders Sandbox page, detects script, and handles empty validation', () => {
    render(
      <BrowserRouter>
        <Sandbox />
      </BrowserRouter>
    );

    expect(screen.getByText(/Comment Sentiment Sandbox/i)).toBeInTheDocument();
    expect(screen.getByTestId('sandbox-empty-state')).toBeInTheDocument();

    const textarea = screen.getByLabelText(/comment text for sentiment analysis/i);
    fireEvent.change(textarea, { target: { value: 'തിയേറ്ററിൽ തന്നെ കാണണം' } });

    expect(screen.getByText(/Malayalam Script/i)).toBeInTheDocument();

    // Change to Manglish
    fireEvent.change(textarea, { target: { value: 'Padam kidilam aayirunnu' } });
    expect(screen.getByText(/Latin Script \(Manglish \/ English\)/i)).toBeInTheDocument();
  });

  it('renders Analyze page and validates YouTube URL input', () => {
    render(
      <BrowserRouter>
        <Analyze />
      </BrowserRouter>
    );

    expect(screen.getByText(/YouTube Comment Analysis/i)).toBeInTheDocument();
    const submitBtn = screen.getByRole('button', { name: /start ingestion & analysis/i });

    // Submit with empty url
    fireEvent.click(submitBtn);
    expect(screen.getByText(/Please enter a YouTube video URL/i)).toBeInTheDocument();

    // Submit with invalid url
    const input = screen.getByLabelText(/youtube video url/i);
    fireEvent.change(input, { target: { value: 'https://invalid-site.com/video' } });
    fireEvent.click(submitBtn);
    expect(screen.getByText(/Invalid YouTube URL/i)).toBeInTheDocument();
  });

  it('renders Dashboard with summary cards and toggles skeleton state', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    expect(screen.getByText(/Audience Analytics Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/No Sentiment Data Available/i)).toBeInTheDocument();

    // Toggle skeleton state
    const toggleBtn = screen.getByRole('button', { name: /preview skeleton state/i });
    fireEvent.click(toggleBtn);
    expect(screen.getByTestId('dashboard-table-skeleton')).toBeInTheDocument();
  });
});
