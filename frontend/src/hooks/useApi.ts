/**
 * Custom hooks for API operations with error handling and loading states
 */

import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import { PersonsResponse, PhotosResponse, Person, Photo } from '../types';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiReturn<T> extends UseApiState<T> {
  refetch: () => Promise<void>;
  clearError: () => void;
}

// Generic hook for API calls
function useApi<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
): UseApiReturn<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const data = await apiCall();
      setState({ data, loading: false, error: null });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      setState({ data: null, loading: false, error: errorMessage });
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    ...state,
    refetch: fetchData,
    clearError,
  };
}

// Hook for fetching persons
export function usePersons(page: number = 1, perPage: number = 20, minPhotos: number = 1) {
  return useApi(
    () => apiService.getPersons(page, perPage, minPhotos),
    [page, perPage, minPhotos]
  );
}

// Hook for fetching a single person
export function usePerson(personId: string | null) {
  return useApi(
    () => personId ? apiService.getPerson(personId) : Promise.resolve(null),
    [personId]
  );
}

// Hook for fetching photos by person
export function usePhotosByPerson(personId: string | null, page: number = 1, perPage: number = 20) {
  return useApi(
    () => personId ? apiService.getPhotosByPerson(personId, page, perPage) : Promise.resolve(null),
    [personId, page, perPage]
  );
}

// Hook for fetching all photos
export function usePhotos(page: number = 1, perPage: number = 20, processedOnly: boolean = true, hasFaces?: boolean) {
  return useApi(
    () => apiService.getAllPhotos(page, perPage, processedOnly, hasFaces),
    [page, perPage, processedOnly, hasFaces]
  );
}

// Hook for fetching photos with faces
export function usePhotosWithFaces(page: number = 1, perPage: number = 20) {
  return usePhotos(page, perPage, true, true);
}

// Hook for fetching photos without faces
export function usePhotosWithoutFaces(page: number = 1, perPage: number = 20) {
  return usePhotos(page, perPage, true, false);
}

// Hook for lazy loading with pagination
export function usePaginatedData<T>(
  fetchFunction: (page: number, perPage: number) => Promise<{ data: T[]; total: number; has_next: boolean }>,
  perPage: number = 20
) {
  const [allData, setAllData] = useState<T[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const loadPage = useCallback(async (page: number, append: boolean = false) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetchFunction(page, perPage);

      if (append) {
        setAllData(prev => {
          // Avoid duplicates
          const newIds = new Set(prev.map((item: any) => item.id));
          const newItems = response.data.filter((item: any) => !newIds.has(item.id));
          return [...prev, ...newItems];
        });
      } else {
        setAllData(response.data);
      }

      setCurrentPage(page);
      setHasNextPage(response.has_next);
      setTotal(response.total);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [perPage]); // Remove fetchFunction dependency

  const loadMore = useCallback(() => {
    if (hasNextPage && !loading) {
      const nextPage = currentPage + 1;
      fetchFunction(nextPage, perPage).then(response => {
        setAllData(prev => {
          // Avoid duplicates
          const newIds = new Set(prev.map((item: any) => item.id));
          const newItems = response.data.filter((item: any) => !newIds.has(item.id));
          return [...prev, ...newItems];
        });
        setCurrentPage(nextPage);
        setHasNextPage(response.has_next);
        setTotal(response.total);
      }).catch(error => {
        const errorMessage = error instanceof Error ? error.message : 'An error occurred';
        setError(errorMessage);
      });
    }
  }, [hasNextPage, loading, currentPage, perPage, fetchFunction]);

  const refresh = useCallback(() => {
    setAllData([]);
    setCurrentPage(1);
    loadPage(1, false);
  }, [loadPage]);

  useEffect(() => {
    loadPage(1, false);
  }, [loadPage]);

  return {
    data: allData,
    loading,
    error,
    hasNextPage,
    currentPage,
    total,
    loadMore,
    refresh,
    clearError: () => setError(null),
  };
}

// Hook for downloading photos
export function usePhotoDownload() {
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const downloadPhoto = useCallback(async (
    photoId: string, 
    quality: 'original' | 'web' | 'thumbnail' = 'original',
    filename?: string
  ) => {
    setDownloading(photoId);
    setError(null);

    try {
      const url = apiService.getDownloadUrl(photoId, quality);
      
      // Create a temporary link and trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || `photo_${photoId}_${quality}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Download failed';
      setError(errorMessage);
    } finally {
      setDownloading(null);
    }
  }, []);

  return {
    downloadPhoto,
    downloading,
    error,
    clearError: () => setError(null),
  };
}