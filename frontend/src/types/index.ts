/**
 * Type definitions for the photo gallery application
 */

export interface PersonThumbnail {
  id: string;
  thumbnail_url: string;
  photo_count: number;
  cluster_confidence: number;
}

export interface Person extends PersonThumbnail {
  created_at: string;
  updated_at: string;
}

export interface Photo {
  id: string;
  original_url: string;
  thumbnail_url: string;
  web_url: string;
  filename: string;
  width: number;
  height: number;
  file_size: number;
  taken_at?: string;
  processed: boolean;
  processing_error?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  persons: string[];
}

export interface PersonsResponse {
  persons: PersonThumbnail[];
  total: number;
}

export interface PhotosResponse {
  photos: Photo[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}

export interface ApiError {
  detail: string;
  error_code?: string;
}

export interface AppState {
  persons: PersonThumbnail[];
  selectedPerson: Person | null;
  photos: Photo[];
  loading: boolean;
  error: string | null;
  currentPage: number;
  hasNextPage: boolean;
}

export interface AppContextType {
  state: AppState;
  actions: {
    setPersons: (persons: PersonThumbnail[]) => void;
    setSelectedPerson: (person: Person | null) => void;
    setPhotos: (photos: Photo[]) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    setCurrentPage: (page: number) => void;
    setHasNextPage: (hasNext: boolean) => void;
    clearError: () => void;
  };
}