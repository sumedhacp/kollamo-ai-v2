import React from 'react';
import { Badge } from '@/components/ui/badge';
import { JobStatus, AnalysisJobState } from '@/services/api/types';

interface AnalysisStatusProps {
  status: JobStatus | AnalysisJobState;
  className?: string;
}

export const AnalysisStatus: React.FC<AnalysisStatusProps> = ({
  status,
  className = '',
}) => {
  const normalized = status.toUpperCase();

  switch (normalized) {
    case 'COMPLETED':
      return (
        <Badge variant="default" size="sm" className={`bg-emerald-600 text-white hover:bg-emerald-700 ${className}`}>
          Completed
        </Badge>
      );
    case 'FAILED':
      return (
        <Badge variant="negative" size="sm" className={className}>
          Failed
        </Badge>
      );
    case 'PROCESSING':
      return (
        <Badge variant="secondary" size="sm" className={`bg-brand-50 text-brand-700 border-brand-200 ${className}`}>
          Processing
        </Badge>
      );
    case 'QUEUED':
      return (
        <Badge variant="secondary" size="sm" className={`bg-amber-50 text-amber-700 border-amber-200 ${className}`}>
          Queued
        </Badge>
      );
    case 'SUBMITTING':
      return (
        <Badge variant="secondary" size="sm" className={`bg-sky-50 text-sky-700 border-sky-200 ${className}`}>
          Submitting
        </Badge>
      );
    default:
      return (
        <Badge variant="secondary" size="sm" className={className}>
          {status}
        </Badge>
      );
  }
};
