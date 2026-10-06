import { useState, useEffect, useRef, useCallback } from 'react';
import { AnalysisJob } from '@/types';
import { api, ApiError } from '@/services/api';

export interface UseJobPollingOptions {
  intervalMs?: number;
  enabled?: boolean;
  onComplete?: (job: AnalysisJob) => void;
  onError?: (error: ApiError) => void;
}

export interface UseJobPollingResult {
  job: AnalysisJob | null;
  isLoading: boolean;
  isPolling: boolean;
  error: ApiError | null;
  refetch: () => Promise<void>;
  stopPolling: () => void;
}

export function useJobPolling(
  jobId: string | null,
  options: UseJobPollingOptions = {}
): UseJobPollingResult {
  const { intervalMs = 1500, enabled = true, onComplete, onError } = options;

  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isPolling, setIsPolling] = useState<boolean>(false);
  const [error, setError] = useState<ApiError | null>(null);

  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef<boolean>(true);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);

  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  const stopPolling = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (isMountedRef.current) {
      setIsPolling(false);
    }
  }, []);

  const fetchStatus = useCallback(async () => {
    if (!jobId) return;

    try {
      const data = await api.getJobStatus(jobId);
      if (!isMountedRef.current) return;

      setJob(data);
      setError(null);

      if (data.status === 'completed') {
        stopPolling();
        onCompleteRef.current?.(data);
      } else if (data.status === 'failed' || data.status === 'cancelled') {
        stopPolling();
        const failureErr = new ApiError(
          data.error || 'Analysis job failed to complete.',
          400,
          'JOB_FAILED'
        );
        setError(failureErr);
        onErrorRef.current?.(failureErr);
      }
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      const apiErr =
        err instanceof ApiError
          ? err
          : new ApiError(
              err instanceof Error ? err.message : 'Failed to fetch job status',
              500,
              'FETCH_STATUS_ERROR'
            );
      setError(apiErr);
      onErrorRef.current?.(apiErr);
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [jobId, stopPolling]);

  // Main polling loop
  useEffect(() => {
    isMountedRef.current = true;

    if (!jobId || !enabled) {
      stopPolling();
      setJob(null);
      setError(null);
      return;
    }

    setIsLoading(true);
    setIsPolling(true);

    let isSubscribed = true;

    const poll = async () => {
      if (!isSubscribed) return;
      await fetchStatus();

      if (isSubscribed && isMountedRef.current) {
        setJob((currentJob) => {
          if (
            currentJob &&
            (currentJob.status === 'completed' ||
              currentJob.status === 'failed' ||
              currentJob.status === 'cancelled')
          ) {
            setIsPolling(false);
            return currentJob;
          }

          // Schedule next poll
          timerRef.current = setTimeout(poll, intervalMs);
          return currentJob;
        });
      }
    };

    poll();

    return () => {
      isSubscribed = false;
      isMountedRef.current = false;
      stopPolling();
    };
  }, [jobId, enabled, intervalMs, fetchStatus, stopPolling]);

  return {
    job,
    isLoading,
    isPolling,
    error,
    refetch: fetchStatus,
    stopPolling,
  };
}
