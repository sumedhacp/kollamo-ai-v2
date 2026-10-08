/**
 * Centralized API Client for Kollamo.ai Frontend.
 * Handles base URL configuration, request execution, timeout management,
 * and standardized RFC error envelope parsing.
 */

import { ApiErrorEnvelope } from './types';


/**
 * Standard API error class carrying status code, machine-readable error code,
 * and optional diagnostic details.
 */
export class ApiError extends Error {
  public status: number;
  public code: string;
  public details?: unknown;

  constructor(message: string, status: number, code: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/**
 * Retrieves the normalized base URL from environment or fallback default.
 */
export function getApiBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (typeof envUrl === 'string' && envUrl.trim().length > 0) {
    return envUrl.trim().replace(/\/+$/, '');
  }
  return 'http://localhost:8000';
}

/**
 * Normalizes an API path against the base URL, preventing duplicated slashes.
 */
export function buildApiUrl(endpoint: string): string {
  if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
    return endpoint;
  }
  const baseUrl = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
}

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

/**
 * Generic JSON request handler with timeout and error classification.
 */
export async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const url = buildApiUrl(endpoint);
  const timeoutMs = options.timeoutMs ?? 15000;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Combine external signal if provided
  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
      signal: options.signal || controller.signal,
    });
  } catch (err: unknown) {
    clearTimeout(timeoutId);

    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(
        'Request timed out. The server took too long to respond.',
        408,
        'REQUEST_TIMEOUT'
      );
    }

    const message = err instanceof Error ? err.message : 'Network request failed';
    throw new ApiError(
      `Unable to connect to the Kollamo.ai backend (${message}). Please check that the backend is running.`,
      0,
      'NETWORK_ERROR'
    );
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    let errorCode = 'HTTP_ERROR';
    let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
    let errorDetails: unknown = undefined;

    try {
      const errorJson = (await response.json()) as ApiErrorEnvelope;
      if (errorJson && errorJson.error) {
        errorCode = errorJson.error.code || errorCode;
        errorMessage = errorJson.error.message || errorMessage;
        errorDetails = errorJson.error.details;
      }
    } catch {
      // Body was not JSON; use default status-based user-friendly messages
      if (response.status === 404) {
        errorCode = 'NOT_FOUND';
        errorMessage = 'Requested resource was not found.';
      } else if (response.status === 503) {
        errorCode = 'SERVICE_UNAVAILABLE';
        errorMessage = 'The analysis service is temporarily unavailable.';
      } else if (response.status === 500) {
        errorCode = 'INTERNAL_ERROR';
        errorMessage = 'An internal server error occurred.';
      }
    }

    // Specific user-friendly translation for common error states
    if (errorCode === 'MODEL_NOT_READY') {
      errorMessage = 'The sentiment analysis model is not ready yet. Please try again after the model has been configured.';
    }

    throw new ApiError(errorMessage, response.status, errorCode, errorDetails);
  }

  return response.json() as Promise<T>;
}
