import React from 'react';
import { cn } from '@/lib/utils';
import { SentimentClass } from '@/types';
import { Smile, Frown, Minus, Shuffle, HelpCircle } from 'lucide-react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'outline' | 'secondary' | 'positive' | 'negative' | 'neutral' | 'mixed' | 'unsupported';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  size = 'md',
  children,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-full transition-colors';

  const sizes = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
  };

  const variants = {
    default: 'bg-slate-900 text-white',
    secondary: 'bg-slate-100 text-slate-800 border border-slate-200',
    outline: 'border border-slate-300 text-slate-700 bg-white',
    positive: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    negative: 'bg-rose-50 text-rose-700 border border-rose-200',
    neutral: 'bg-slate-100 text-slate-700 border border-slate-200',
    mixed: 'bg-amber-50 text-amber-800 border border-amber-200',
    unsupported: 'bg-zinc-100 text-zinc-600 border border-zinc-200',
  };

  return (
    <span className={cn(baseStyles, sizes[size], variants[variant], className)} {...props}>
      {children}
    </span>
  );
};

export interface SentimentBadgeProps {
  sentiment: SentimentClass;
  showIcon?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

export const SentimentBadge: React.FC<SentimentBadgeProps> = ({
  sentiment,
  showIcon = true,
  size = 'md',
  className,
}) => {
  const config: Record<
    SentimentClass,
    { label: string; variant: BadgeProps['variant']; icon: React.ReactNode }
  > = {
    positive: {
      label: 'Positive',
      variant: 'positive',
      icon: <Smile className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />,
    },
    negative: {
      label: 'Negative',
      variant: 'negative',
      icon: <Frown className="w-3.5 h-3.5 text-rose-600" aria-hidden="true" />,
    },
    neutral: {
      label: 'Neutral',
      variant: 'neutral',
      icon: <Minus className="w-3.5 h-3.5 text-slate-600" aria-hidden="true" />,
    },
    mixed: {
      label: 'Mixed',
      variant: 'mixed',
      icon: <Shuffle className="w-3.5 h-3.5 text-amber-600" aria-hidden="true" />,
    },
    unsupported: {
      label: 'Unsupported',
      variant: 'unsupported',
      icon: <HelpCircle className="w-3.5 h-3.5 text-zinc-500" aria-hidden="true" />,
    },
  };

  const item = config[sentiment] || config.unsupported;

  return (
    <Badge variant={item.variant} size={size} className={cn('capitalize select-none', className)}>
      {showIcon && item.icon}
      <span>{item.label}</span>
    </Badge>
  );
};
