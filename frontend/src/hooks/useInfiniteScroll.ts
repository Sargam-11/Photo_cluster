/**
 * Hook for infinite scrolling functionality
 */

import { useState, useEffect, useCallback, useRef } from 'react';

interface UseInfiniteScrollOptions {
  threshold?: number;
  rootMargin?: string;
  enabled?: boolean;
}

interface UseInfiniteScrollReturn {
  isFetching: boolean;
  setIsFetching: (fetching: boolean) => void;
  lastElementRef: (node: HTMLElement | null) => void;
}

export function useInfiniteScroll(
  fetchMore: () => Promise<void>,
  hasNextPage: boolean,
  options: UseInfiniteScrollOptions = {}
): UseInfiniteScrollReturn {
  const {
    threshold = 1.0,
    rootMargin = '100px',
    enabled = true,
  } = options;

  const [isFetching, setIsFetching] = useState(false);
  const observer = useRef<IntersectionObserver | null>(null);

  const lastElementRef = useCallback(
    (node: HTMLElement | null) => {
      if (isFetching || !enabled || !hasNextPage) return;
      
      if (observer.current) observer.current.disconnect();
      
      observer.current = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting && hasNextPage && !isFetching) {
            setIsFetching(true);
            fetchMore().finally(() => setIsFetching(false));
          }
        },
        {
          threshold,
          rootMargin,
        }
      );
      
      if (node) observer.current.observe(node);
    },
    [isFetching, hasNextPage, enabled, fetchMore, threshold, rootMargin]
  );

  useEffect(() => {
    return () => {
      if (observer.current) {
        observer.current.disconnect();
      }
    };
  }, []);

  return {
    isFetching,
    setIsFetching,
    lastElementRef,
  };
}

/**
 * Hook for virtual scrolling with large datasets
 */
interface UseVirtualScrollOptions {
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}

interface UseVirtualScrollReturn {
  visibleRange: { start: number; end: number };
  totalHeight: number;
  offsetY: number;
  scrollElementRef: (node: HTMLElement | null) => void;
}

export function useVirtualScroll<T>(
  items: T[],
  options: UseVirtualScrollOptions
): UseVirtualScrollReturn {
  const { itemHeight, containerHeight, overscan = 5 } = options;
  const [scrollTop, setScrollTop] = useState(0);
  const scrollElementRef = useRef<HTMLElement | null>(null);

  const totalHeight = items.length * itemHeight;
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.floor((scrollTop + containerHeight) / itemHeight) + overscan
  );

  const visibleRange = { start: startIndex, end: endIndex };
  const offsetY = startIndex * itemHeight;

  const handleScroll = useCallback((event: Event) => {
    const target = event.target as HTMLElement;
    setScrollTop(target.scrollTop);
  }, []);

  const setScrollElementRef = useCallback((node: HTMLElement | null) => {
    if (scrollElementRef.current) {
      scrollElementRef.current.removeEventListener('scroll', handleScroll);
    }
    
    scrollElementRef.current = node;
    
    if (node) {
      node.addEventListener('scroll', handleScroll, { passive: true });
    }
  }, [handleScroll]);

  useEffect(() => {
    return () => {
      if (scrollElementRef.current) {
        scrollElementRef.current.removeEventListener('scroll', handleScroll);
      }
    };
  }, [handleScroll]);

  return {
    visibleRange,
    totalHeight,
    offsetY,
    scrollElementRef: setScrollElementRef,
  };
}