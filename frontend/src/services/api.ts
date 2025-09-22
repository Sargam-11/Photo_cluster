/**
 * API service for communicating with the backend
 */

import { PersonsResponse, PhotosResponse, Person, Photo, ApiError } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData: ApiError = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`,
        }));
        throw new Error(errorData.detail || 'An error occurred');
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Network error occurred');
    }
  }

  // Persons endpoints
  async getPersons(page: number = 1, perPage: number = 20, minPhotos: number = 1): Promise<PersonsResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      min_photos: minPhotos.toString(),
    });
    
    return this.request<PersonsResponse>(`/api/persons?${params}`);
  }

  async getPerson(personId: string): Promise<Person> {
    return this.request<Person>(`/api/persons/${personId}`);
  }

  // Photos endpoints
  async getPhotosByPerson(
    personId: string, 
    page: number = 1, 
    perPage: number = 20
  ): Promise<PhotosResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });
    
    return this.request<PhotosResponse>(`/api/persons/${personId}/photos?${params}`);
  }

  async getPhoto(photoId: string): Promise<Photo> {
    return this.request<Photo>(`/api/photos/${photoId}`);
  }

  async getAllPhotos(
    page: number = 1, 
    perPage: number = 20, 
    processedOnly: boolean = true,
    hasFaces?: boolean
  ): Promise<PhotosResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      processed_only: processedOnly.toString(),
    });
    
    if (hasFaces !== undefined) {
      params.append('has_faces', hasFaces.toString());
    }
    
    return this.request<PhotosResponse>(`/api/photos?${params}`);
  }

  // Download endpoints
  getDownloadUrl(photoId: string, quality: 'original' | 'web' | 'thumbnail' = 'original'): string {
    return `${this.baseUrl}/api/photos/${photoId}/download?quality=${quality}`;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: number }> {
    return this.request<{ status: string; timestamp: number }>('/health');
  }
}

// Create and export a singleton instance
export const apiService = new ApiService();

// Export the class for testing
export { ApiService };