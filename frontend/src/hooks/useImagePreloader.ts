/**
 * Hook for preloading images to improve user experience
 */

import { useState, useEffect, useCallback, useRef } from 'react';

interface PreloadedImage {
  src: string;
  loaded: boolean;
  error: boolean;
}

interface UseImagePreloaderOptions {
  maxConcurrent?: number;
  priority?: 'high' | 'low';
}

export function useImagePreloader(
  imageSrcs: string[],
  options: UseImagePreloaderOptions = {}
) {
  const { maxConcurrent = 3, priority = 'low' } = options;
  const [preloadedImages, setPreloadedImages] = useState<Map<string, PreloadedImage>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const loadingQueue = useRef<string[]>([]);
  const activeLoads = useRef<Set<string>>(new Set());

  const preloadImage = useCallback((src: string): Promise<void> => {
    return new Promise((resolve) => {
      const img = new Image();
      
      img.onload = () => {
        setPreloadedImages(prev => new Map(prev.set(src, { src, loaded: true, error: false })));
        resolve();
      };
      
      img.onerror = () => {
        setPreloadedImages(prev => new Map(prev.set(src, { src, loaded: false, error: true })));
        resolve();
      };
      
      // Set loading priority
      if (priority === 'high') {
        img.loading = 'eager';
      }
      
      img.src = src;
    });
  }, [priority]);

  const processQueue = useCallback(async () => {
    while (loadingQueue.current.length > 0 && activeLoads.current.size < maxConcurrent) {
      const src = loadingQueue.current.shift();
      if (!src || activeLoads.current.has(src)) continue;

      activeLoads.current.add(src);
      
      try {
        await preloadImage(src);
      } finally {
        activeLoads.current.delete(src);
      }
    }

    if (activeLoads.current.size === 0 && loadingQueue.current.length === 0) {
      setIsLoading(false);
    }
  }, [maxConcurrent, preloadImage]);

  const startPreloading = useCallback((srcs: string[]) => {
    const newSrcs = srcs.filter(src => !preloadedImages.has(src));
    if (newSrcs.length === 0) return;

    setIsLoading(true);
    loadingQueue.current.push(...newSrcs);
    
    // Initialize preloaded images map
    setPreloadedImages(prev => {
      const updated = new Map(prev);
      newSrcs.forEach(src => {
        if (!updated.has(src)) {
          updated.set(src, { src, loaded: false, error: false });
        }
      });
      return updated;
    });

    processQueue();
  }, [preloadedImages, processQueue]);

  useEffect(() => {
    if (imageSrcs.length > 0) {
      startPreloading(imageSrcs);
    }
  }, [imageSrcs, startPreloading]);

  const getImageStatus = useCallback((src: string) => {
    return preloadedImages.get(src) || { src, loaded: false, error: false };
  }, [preloadedImages]);

  const isImageLoaded = useCallback((src: string) => {
    return preloadedImages.get(src)?.loaded || false;
  }, [preloadedImages]);

  const hasImageError = useCallback((src: string) => {
    return preloadedImages.get(src)?.error || false;
  }, [preloadedImages]);

  return {
    preloadedImages: Array.from(preloadedImages.values()),
    isLoading,
    getImageStatus,
    isImageLoaded,
    hasImageError,
    startPreloading,
  };
}