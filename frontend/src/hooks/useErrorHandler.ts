/**
 * Hook for centralized error handling and user notifications
 */

import { useState, useCallback, useEffect } from 'react';

interface ErrorState {
  message: string;
  code?: string;
  timestamp: number;
}

interface UseErrorHandlerReturn {
  error: ErrorState | null;
  showError: (message: string, code?: string) => void;
  clearError: () => void;
  handleApiError: (error: unknown) => void;
}

export function useErrorHandler(autoHideDelay?: number): UseErrorHandlerReturn {
  const [error, setError] = useState<ErrorState | null>(null);

  const showError = useCallback((message: string, code?: string) => {
    setError({
      message,
      code,
      timestamp: Date.now(),
    });
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const handleApiError = useCallback((error: unknown) => {
    let message = 'An unexpected error occurred';
    let code: string | undefined;

    if (error instanceof Error) {
      message = error.message;
      
      // Extract error code if present
      if (error.message.includes('HTTP')) {
        const match = error.message.match(/HTTP (\d+)/);
        if (match) {
          code = match[1];
          
          // Provide user-friendly messages for common HTTP errors
          switch (code) {
            case '400':
              message = 'Invalid request. Please check your input.';
              break;
            case '401':
              message = 'Authentication required. Please log in.';
              break;
            case '403':
              message = 'Access denied. You don\'t have permission for this action.';
              break;
            case '404':
              message = 'The requested resource was not found.';
              break;
            case '429':
              message = 'Too many requests. Please wait a moment and try again.';
              break;
            case '500':
              message = 'Server error. Please try again later.';
              break;
            case '503':
              message = 'Service temporarily unavailable. Please try again later.';
              break;
          }
        }
      }
      
      // Handle network errors
      if (error.name === 'AbortError') {
        message = 'Request timed out. Please check your connection and try again.';
        code = 'TIMEOUT';
      } else if (error.message.includes('fetch')) {
        message = 'Network error. Please check your connection.';
        code = 'NETWORK';
      }
    }

    showError(message, code);
  }, [showError]);

  // Auto-hide error after delay
  useEffect(() => {
    if (error && autoHideDelay) {
      const timer = setTimeout(() => {
        clearError();
      }, autoHideDelay);

      return () => clearTimeout(timer);
    }
  }, [error, autoHideDelay, clearError]);

  return {
    error,
    showError,
    clearError,
    handleApiError,
  };
}

/**
 * Hook for retry logic with exponential backoff
 */
interface UseRetryOptions {
  maxRetries?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffFactor?: number;
}

interface UseRetryReturn {
  retry: <T>(fn: () => Promise<T>) => Promise<T>;
  isRetrying: boolean;
  retryCount: number;
  resetRetry: () => void;
}

export function useRetry(options: UseRetryOptions = {}): UseRetryReturn {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    backoffFactor = 2,
  } = options;

  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const retry = useCallback(async <T>(fn: () => Promise<T>): Promise<T> => {
    setIsRetrying(true);
    let lastError: Error;
    let currentRetryCount = 0;

    while (currentRetryCount <= maxRetries) {
      try {
        const result = await fn();
        setIsRetrying(false);
        setRetryCount(0);
        return result;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        currentRetryCount++;
        setRetryCount(currentRetryCount);

        if (currentRetryCount > maxRetries) {
          break;
        }

        // Calculate delay with exponential backoff
        const delay = Math.min(
          initialDelay * Math.pow(backoffFactor, currentRetryCount - 1),
          maxDelay
        );

        await sleep(delay);
      }
    }

    setIsRetrying(false);
    throw lastError!;
  }, [maxRetries, initialDelay, maxDelay, backoffFactor]);

  const resetRetry = useCallback(() => {
    setRetryCount(0);
    setIsRetrying(false);
  }, []);

  return {
    retry,
    isRetrying,
    retryCount,
    resetRetry,
  };
}

/**
 * Hook for debounced error reporting to prevent spam
 */
export function useDebouncedErrorHandler(delay: number = 1000) {
  const [debouncedErrors, setDebouncedErrors] = useState<Map<string, ErrorState>>(new Map());
  const { error, showError, clearError, handleApiError } = useErrorHandler();

  const debouncedShowError = useCallback((message: string, code?: string) => {
    const key = `${message}-${code || ''}`;
    const now = Date.now();
    
    // Check if we've shown this error recently
    const lastError = debouncedErrors.get(key);
    if (lastError && now - lastError.timestamp < delay) {
      return; // Skip showing the error
    }

    // Update the debounced errors map
    setDebouncedErrors(prev => new Map(prev.set(key, { message, code, timestamp: now })));
    
    // Show the error
    showError(message, code);
  }, [debouncedErrors, delay, showError]);

  const debouncedHandleApiError = useCallback((error: unknown) => {
    let message = 'An unexpected error occurred';
    let code: string | undefined;

    if (error instanceof Error) {
      message = error.message;
      if (error.message.includes('HTTP')) {
        const match = error.message.match(/HTTP (\d+)/);
        if (match) {
          code = match[1];
        }
      }
    }

    debouncedShowError(message, code);
  }, [debouncedShowError]);

  // Clean up old debounced errors
  useEffect(() => {
    const cleanup = setInterval(() => {
      const now = Date.now();
      setDebouncedErrors(prev => {
        const updated = new Map(prev);
        const keysToDelete: string[] = [];
        updated.forEach((errorState, key) => {
          if (now - errorState.timestamp > delay * 2) {
            keysToDelete.push(key);
          }
        });
        keysToDelete.forEach(key => updated.delete(key));
        return updated;
      });
    }, delay);

    return () => clearInterval(cleanup);
  }, [delay]);

  return {
    error,
    showError: debouncedShowError,
    clearError,
    handleApiError: debouncedHandleApiError,
  };
}