/**
 * Enhanced API client with retry logic, error handling, and request/response interceptors
 */

import { PersonsResponse, PhotosResponse, Person, Photo, ApiError } from '../types';

interface RequestConfig extends RequestInit {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

interface ApiClientConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
  retryDelay: number;
}

class ApiClient {
  private config: ApiClientConfig;
  private requestInterceptors: Array<(config: RequestConfig) => RequestConfig> = [];
  private responseInterceptors: Array<(response: Response) => Response | Promise<Response>> = [];

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.config = {
      baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 30000,
      retries: 3,
      retryDelay: 1000,
      ...config,
    };
  }

  // Add request interceptor
  addRequestInterceptor(interceptor: (config: RequestConfig) => RequestConfig) {
    this.requestInterceptors.push(interceptor);
  }

  // Add response interceptor
  addResponseInterceptor(interceptor: (response: Response) => Response | Promise<Response>) {
    this.responseInterceptors.push(interceptor);
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async requestWithTimeout(
    url: string,
    config: RequestConfig
  ): Promise<Response> {
    const { timeout = this.config.timeout, ...fetchConfig } = config;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...fetchConfig,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  private async requestWithRetry<T>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<T> {
    const {
      retries = this.config.retries,
      retryDelay = this.config.retryDelay,
      ...requestConfig
    } = config;

    const url = `${this.config.baseUrl}${endpoint}`;
    
    // Apply request interceptors
    let finalConfig = { ...requestConfig };
    for (const interceptor of this.requestInterceptors) {
      finalConfig = interceptor(finalConfig);
    }

    // Set default headers
    finalConfig.headers = {
      'Content-Type': 'application/json',
      ...finalConfig.headers,
    };

    let lastError: Error;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        let response = await this.requestWithTimeout(url, finalConfig);

        // Apply response interceptors
        for (const interceptor of this.responseInterceptors) {
          response = await interceptor(response);
        }

        if (!response.ok) {
          const errorData: ApiError = await response.json().catch(() => ({
            detail: `HTTP ${response.status}: ${response.statusText}`,
          }));
          
          // Don't retry client errors (4xx)
          if (response.status >= 400 && response.status < 500) {
            throw new Error(errorData.detail || 'Client error occurred');
          }
          
          throw new Error(errorData.detail || 'Server error occurred');
        }

        // Handle empty responses
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return await response.json();
        } else {
          return response as unknown as T;
        }

      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        
        // Don't retry on abort (timeout) or client errors
        if (lastError.name === 'AbortError' || lastError.message.includes('Client error')) {
          throw lastError;
        }

        // If this was the last attempt, throw the error
        if (attempt === retries) {
          throw lastError;
        }

        // Wait before retrying (exponential backoff)
        const delay = retryDelay * Math.pow(2, attempt);
        await this.sleep(delay);
      }
    }

    throw lastError!;
  }

  // GET request
  async get<T>(endpoint: string, config: RequestConfig = {}): Promise<T> {
    return this.requestWithRetry<T>(endpoint, {
      method: 'GET',
      ...config,
    });
  }

  // POST request
  async post<T>(endpoint: string, data?: any, config: RequestConfig = {}): Promise<T> {
    return this.requestWithRetry<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      ...config,
    });
  }

  // PUT request
  async put<T>(endpoint: string, data?: any, config: RequestConfig = {}): Promise<T> {
    return this.requestWithRetry<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      ...config,
    });
  }

  // DELETE request
  async delete<T>(endpoint: string, config: RequestConfig = {}): Promise<T> {
    return this.requestWithRetry<T>(endpoint, {
      method: 'DELETE',
      ...config,
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: number }> {
    return this.get<{ status: string; timestamp: number }>('/health');
  }

  // Persons endpoints
  async getPersons(page: number = 1, perPage: number = 20, minPhotos: number = 1): Promise<PersonsResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      min_photos: minPhotos.toString(),
    });
    
    return this.get<PersonsResponse>(`/api/persons?${params}`);
  }

  async getPerson(personId: string): Promise<Person> {
    return this.get<Person>(`/api/persons/${personId}`);
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
    
    return this.get<PhotosResponse>(`/api/persons/${personId}/photos?${params}`);
  }

  async getPhoto(photoId: string): Promise<Photo> {
    return this.get<Photo>(`/api/photos/${photoId}`);
  }

  async getAllPhotos(
    page: number = 1, 
    perPage: number = 20, 
    processedOnly: boolean = true
  ): Promise<PhotosResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      processed_only: processedOnly.toString(),
    });
    
    return this.get<PhotosResponse>(`/api/photos?${params}`);
  }

  // Download URL generator
  getDownloadUrl(photoId: string, quality: 'original' | 'web' | 'thumbnail' = 'original'): string {
    return `${this.config.baseUrl}/api/photos/${photoId}/download?quality=${quality}`;
  }
}

// Create enhanced API client with interceptors
const apiClient = new ApiClient();

// Add request logging in development
if (process.env.NODE_ENV === 'development') {
  apiClient.addRequestInterceptor((config) => {
    console.log('API Request:', config);
    return config;
  });

  apiClient.addResponseInterceptor((response) => {
    console.log('API Response:', response.status, response.statusText);
    return response;
  });
}

// Add authentication header if needed (for future use)
apiClient.addRequestInterceptor((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${token}`,
    };
  }
  return config;
});

export { apiClient, ApiClient };
export type { RequestConfig, ApiClientConfig };