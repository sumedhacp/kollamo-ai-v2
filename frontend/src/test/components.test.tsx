import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { SentimentBadge } from '@/components/ui/badge';
import { Alert } from '@/components/ui/alert';

describe('UI Primitives', () => {
  it('renders Button with text and handles loading state', () => {
    const { rerender } = render(<Button>Click Me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();

    rerender(<Button isLoading>Click Me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('renders Input with error and helper text', () => {
    render(<Input placeholder="Type here" error="Required field" helperText="Help text" />);
    expect(screen.getByPlaceholderText('Type here')).toBeInTheDocument();
    expect(screen.getByText('Required field')).toBeInTheDocument();
  });

  it('renders SentimentBadge for all 5 semantic sentiment classes', () => {
    const { rerender } = render(<SentimentBadge sentiment="positive" />);
    expect(screen.getByText(/positive/i)).toBeInTheDocument();

    rerender(<SentimentBadge sentiment="negative" />);
    expect(screen.getByText(/negative/i)).toBeInTheDocument();

    rerender(<SentimentBadge sentiment="neutral" />);
    expect(screen.getByText(/neutral/i)).toBeInTheDocument();

    rerender(<SentimentBadge sentiment="mixed" />);
    expect(screen.getByText(/mixed/i)).toBeInTheDocument();

    rerender(<SentimentBadge sentiment="unsupported" />);
    expect(screen.getByText(/unsupported/i)).toBeInTheDocument();
  });

  it('renders Alert component with proper role and message', () => {
    render(<Alert variant="warning" title="Warning Header">Notice text</Alert>);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Warning Header')).toBeInTheDocument();
    expect(screen.getByText('Notice text')).toBeInTheDocument();
  });
});
