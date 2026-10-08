/**
 * Dedicated React hook for managing Asynchronous Analysis Job lifecycle (Phase 6).
 * Encapsulates job creation, status polling, real-time stage progress,
 * error classification, race condition protection, and clean timer teardown.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  AnalysisJobRequest,
  AnalysisJobState,
  JobProgress,
  AnalysisResult,
  JobStatusResponse,
} from '@/services/api/types';
import { createAnalysisJob, getAnalysisJob } from '@/services/api/analysis';
import { ApiError } from '@/services/api/client';

export interface UseAnalysisJobOptions {
  pollingIntervalMs?: number;
  onComplete?: (result: JobStatusResponse) => void;
  onError?: (error: ApiError) => void;
}

export interface UseAnalysisJobReturn {
  state: AnalysisJobState;
  jobId: string | null;
  progress: JobProgress | null;
  result: AnalysisResult | null;
  error: ApiError | null;
  isSubmitting: boolean;
  isPolling: boolean;
  isCompleted: boolean;
  isFailed: boolean;
  submitJob: (request: AnalysisJobRequest) => Promise<string | null>;
  reset: () => void;
  retry: () => Promise<string | null>;
}

export function useAnalysisJob(
  options: UseAnalysisJobOptions = {}
): UseAnalysisJobReturn {
  const { pollingIntervalMs = 2000, onComplete, onError } = options;

  const [state, setState] = useState<AnalysisJobState>('IDLE');
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<JobProgress | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  // References for lifecycle and race condition management
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const activeJobIdRef = useRef<string | null>(null);
  const isMountedRef = useRef<boolean>(true);
  const lastRequestRef = useRef<AnalysisJobRequest | null>(null);

  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    clearTimer();
    activeJobIdRef.current = null;
    setState('IDLE');
    setJobId(null);
    setProgress(null);
    setResult(null);
    setError(null);
  }, [clearTimer]);

  const pollJobStatus = useCallback(
    async (targetJobId: string) => {
      if (!isMountedRef.current) return;
      // Stale job response protection
      if (activeJobIdRef.current !== targetJobId) return;

      try {
        const response = await getAnalysisJob(targetJobId);
        if (!isMountedRef.current) return;
        if (activeJobIdRef.current !== targetJobId) return;

        const statusUpper = (response.status || '').toUpperCase();

        if (response.progress) {
          if (typeof response.progress === 'object') {
            setProgress(response.progress);
          } else if (typeof response.progress === 'number') {
            setProgress({
              stage: statusUpper,
              completed: (response as any).processed_comments ?? 0,
              total: (response as any).total_comments ?? null,
              percentage: Math.round(Number(response.progress) * 100),
            });
          }
        }

        if (statusUpper === 'COMPLETED') {
          clearTimer();
          setState('COMPLETED');
          if (response.result) {
            setResult(response.result);
          } else if ((response as any).video) {
            setResult({
              video: (response as any).video,
              total_comments: (response as any).total_comments ?? 0,
              processed_comments: (response as any).processed_comments ?? 0,
              comments: (response as any).comments ?? [],
              model_name: (response as any).model_name,
              model_version: (response as any).model_version,
            });
          }
          onCompleteRef.current?.(response);
          return;
        }

        if (statusUpper === 'FAILED') {
          clearTimer();
          setState('FAILED');
          const errDetail = response.error;
          const failureErr = new ApiError(
            (typeof errDetail === 'string' ? errDetail : errDetail?.message) || 'Analysis job failed.',
            400,
            (typeof errDetail === 'object' ? errDetail?.code : 'JOB_FAILED') || 'JOB_FAILED',
            typeof errDetail === 'object' ? errDetail?.details : undefined
          );
          setError(failureErr);
          onErrorRef.current?.(failureErr);
          return;
        }

        // Active state: QUEUED or PROCESSING
        if (statusUpper === 'PROCESSING' || statusUpper === 'RUNNING') {
          setState('PROCESSING');
        } else {
          setState('QUEUED');
        }


        // Schedule next poll interval
        timerRef.current = setTimeout(() => {
          pollJobStatus(targetJobId);
        }, pollingIntervalMs);
      } catch (err: unknown) {
        if (!isMountedRef.current) return;
        if (activeJobIdRef.current !== targetJobId) return;

        clearTimer();
        setState('FAILED');
        const apiErr =
          err instanceof ApiError
            ? err
            : new ApiError(
                err instanceof Error ? err.message : 'Failed to retrieve job status',
                500,
                'POLLING_ERROR'
              );
        setError(apiErr);
        onErrorRef.current?.(apiErr);
      }
    },
    [clearTimer, pollingIntervalMs]
  );

  const submitJob = useCallback(
    async (req: AnalysisJobRequest): Promise<string | null> => {
      // 1. Stop any current polling and clear state
      clearTimer();
      setError(null);
      setResult(null);
      setProgress(null);
      setState('SUBMITTING');
      lastRequestRef.current = req;

      try {
        // 2. Dispatch POST /api/v1/analysis/jobs
        const createRes = await createAnalysisJob(req);
        if (!isMountedRef.current) return null;

        const newJobId = createRes.job_id;
        activeJobIdRef.current = newJobId;
        setJobId(newJobId);
        setState('QUEUED');

        // Initial default progress representation
        setProgress({
          stage: 'QUEUED',
          completed: 0,
          total: req.comment_limit === 'ALL' ? null : req.comment_limit,
          percentage: 0,
        });

        // 3. Kick off status polling immediately
        pollJobStatus(newJobId);

        return newJobId;

      } catch (err: unknown) {
        if (!isMountedRef.current) return null;
        clearTimer();
        activeJobIdRef.current = null;
        setState('FAILED');

        const apiErr =
          err instanceof ApiError
            ? err
            : new ApiError(
                err instanceof Error ? err.message : 'Failed to submit analysis job',
                500,
                'JOB_CREATION_FAILED'
              );
        setError(apiErr);
        onErrorRef.current?.(apiErr);
        return null;
      }
    },
    [clearTimer, pollJobStatus, pollingIntervalMs]
  );

  const retry = useCallback(async (): Promise<string | null> => {
    if (lastRequestRef.current) {
      return submitJob(lastRequestRef.current);
    }
    return null;
  }, [submitJob]);

  // Teardown timers on unmount
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      clearTimer();
    };
  }, [clearTimer]);

  return {
    state,
    jobId,
    progress,
    result,
    error,
    isSubmitting: state === 'SUBMITTING',
    isPolling: state === 'QUEUED' || state === 'PROCESSING',
    isCompleted: state === 'COMPLETED',
    isFailed: state === 'FAILED',
    submitJob,
    reset,
    retry,
  };
}
