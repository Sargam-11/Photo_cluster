/**
 * Client-side caching service with TTL and storage management
 */

interface CacheItem<T> {
  data: T;
  timestamp: number;
  ttl: number;
  key: string;
}

interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  storage?: 'memory' | 'localStorage' | 'sessionStorage';
  maxSize?: number; // Maximum number of items in cache
}

class CacheService {
  private memoryCache = new Map<string, CacheItem<any>>();
  private defaultTTL = 5 * 60 * 1000; // 5 minutes
  private maxSize = 100;
  private cleanupInterval: NodeJS.Timeout;

  constructor() {
    // Clean up expired items every minute
    this.cleanupInterval = setInterval(() => {
      this.cleanup();
    }, 60 * 1000);
  }

  private getStorageKey(key: string): string {
    return `photo_gallery_cache_${key}`;
  }

  private isExpired(item: CacheItem<any>): boolean {
    return Date.now() - item.timestamp > item.ttl;
  }

  private evictOldest(): void {
    if (this.memoryCache.size <= this.maxSize) return;

    let oldestKey = '';
    let oldestTimestamp = Date.now();

    this.memoryCache.forEach((item, key) => {
      if (item.timestamp < oldestTimestamp) {
        oldestTimestamp = item.timestamp;
        oldestKey = key;
      }
    });

    if (oldestKey) {
      this.memoryCache.delete(oldestKey);
    }
  }

  private cleanup(): void {
    // Clean memory cache
    const keysToDelete: string[] = [];
    this.memoryCache.forEach((item, key) => {
      if (this.isExpired(item)) {
        keysToDelete.push(key);
      }
    });
    keysToDelete.forEach(key => this.memoryCache.delete(key));

    // Clean localStorage
    try {
      const keysToRemove: string[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('photo_gallery_cache_')) {
          try {
            const item = JSON.parse(localStorage.getItem(key) || '');
            if (this.isExpired(item)) {
              keysToRemove.push(key);
            }
          } catch {
            keysToRemove.push(key); // Remove invalid items
          }
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key));
    } catch (error) {
      console.warn('Error cleaning localStorage cache:', error);
    }

    // Clean sessionStorage
    try {
      const keysToRemove: string[] = [];
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key && key.startsWith('photo_gallery_cache_')) {
          try {
            const item = JSON.parse(sessionStorage.getItem(key) || '');
            if (this.isExpired(item)) {
              keysToRemove.push(key);
            }
          } catch {
            keysToRemove.push(key); // Remove invalid items
          }
        }
      }
      keysToRemove.forEach(key => sessionStorage.removeItem(key));
    } catch (error) {
      console.warn('Error cleaning sessionStorage cache:', error);
    }
  }

  set<T>(key: string, data: T, options: CacheOptions = {}): void {
    const {
      ttl = this.defaultTTL,
      storage = 'memory',
      maxSize = this.maxSize,
    } = options;

    const item: CacheItem<T> = {
      data,
      timestamp: Date.now(),
      ttl,
      key,
    };

    switch (storage) {
      case 'memory':
        this.memoryCache.set(key, item);
        this.evictOldest();
        break;

      case 'localStorage':
        try {
          localStorage.setItem(this.getStorageKey(key), JSON.stringify(item));
        } catch (error) {
          console.warn('Error setting localStorage cache:', error);
          // Fallback to memory cache
          this.memoryCache.set(key, item);
        }
        break;

      case 'sessionStorage':
        try {
          sessionStorage.setItem(this.getStorageKey(key), JSON.stringify(item));
        } catch (error) {
          console.warn('Error setting sessionStorage cache:', error);
          // Fallback to memory cache
          this.memoryCache.set(key, item);
        }
        break;
    }
  }

  get<T>(key: string, storage: 'memory' | 'localStorage' | 'sessionStorage' = 'memory'): T | null {
    let item: CacheItem<T> | null = null;

    switch (storage) {
      case 'memory':
        item = this.memoryCache.get(key) || null;
        break;

      case 'localStorage':
        try {
          const stored = localStorage.getItem(this.getStorageKey(key));
          if (stored) {
            item = JSON.parse(stored);
          }
        } catch (error) {
          console.warn('Error getting localStorage cache:', error);
        }
        break;

      case 'sessionStorage':
        try {
          const stored = sessionStorage.getItem(this.getStorageKey(key));
          if (stored) {
            item = JSON.parse(stored);
          }
        } catch (error) {
          console.warn('Error getting sessionStorage cache:', error);
        }
        break;
    }

    if (!item) return null;

    if (this.isExpired(item)) {
      this.delete(key, storage);
      return null;
    }

    return item.data;
  }

  delete(key: string, storage: 'memory' | 'localStorage' | 'sessionStorage' = 'memory'): void {
    switch (storage) {
      case 'memory':
        this.memoryCache.delete(key);
        break;

      case 'localStorage':
        try {
          localStorage.removeItem(this.getStorageKey(key));
        } catch (error) {
          console.warn('Error deleting localStorage cache:', error);
        }
        break;

      case 'sessionStorage':
        try {
          sessionStorage.removeItem(this.getStorageKey(key));
        } catch (error) {
          console.warn('Error deleting sessionStorage cache:', error);
        }
        break;
    }
  }

  clear(storage?: 'memory' | 'localStorage' | 'sessionStorage'): void {
    if (!storage || storage === 'memory') {
      this.memoryCache.clear();
    }

    if (!storage || storage === 'localStorage') {
      try {
        const keysToRemove: string[] = [];
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key && key.startsWith('photo_gallery_cache_')) {
            keysToRemove.push(key);
          }
        }
        keysToRemove.forEach(key => localStorage.removeItem(key));
      } catch (error) {
        console.warn('Error clearing localStorage cache:', error);
      }
    }

    if (!storage || storage === 'sessionStorage') {
      try {
        const keysToRemove: string[] = [];
        for (let i = 0; i < sessionStorage.length; i++) {
          const key = sessionStorage.key(i);
          if (key && key.startsWith('photo_gallery_cache_')) {
            keysToRemove.push(key);
          }
        }
        keysToRemove.forEach(key => sessionStorage.removeItem(key));
      } catch (error) {
        console.warn('Error clearing sessionStorage cache:', error);
      }
    }
  }

  has(key: string, storage: 'memory' | 'localStorage' | 'sessionStorage' = 'memory'): boolean {
    return this.get(key, storage) !== null;
  }

  size(storage: 'memory' | 'localStorage' | 'sessionStorage' = 'memory'): number {
    switch (storage) {
      case 'memory':
        return this.memoryCache.size;

      case 'localStorage':
        try {
          let count = 0;
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('photo_gallery_cache_')) {
              count++;
            }
          }
          return count;
        } catch {
          return 0;
        }

      case 'sessionStorage':
        try {
          let count = 0;
          for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            if (key && key.startsWith('photo_gallery_cache_')) {
              count++;
            }
          }
          return count;
        } catch {
          return 0;
        }

      default:
        return 0;
    }
  }

  getStats(): {
    memory: { size: number; items: string[] };
    localStorage: { size: number; items: string[] };
    sessionStorage: { size: number; items: string[] };
  } {
    const stats = {
      memory: { size: 0, items: [] as string[] },
      localStorage: { size: 0, items: [] as string[] },
      sessionStorage: { size: 0, items: [] as string[] },
    };

    // Memory cache stats
    stats.memory.size = this.memoryCache.size;
    stats.memory.items = Array.from(this.memoryCache.keys());

    // localStorage stats
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('photo_gallery_cache_')) {
          stats.localStorage.size++;
          stats.localStorage.items.push(key.replace('photo_gallery_cache_', ''));
        }
      }
    } catch (error) {
      console.warn('Error getting localStorage stats:', error);
    }

    // sessionStorage stats
    try {
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key && key.startsWith('photo_gallery_cache_')) {
          stats.sessionStorage.size++;
          stats.sessionStorage.items.push(key.replace('photo_gallery_cache_', ''));
        }
      }
    } catch (error) {
      console.warn('Error getting sessionStorage stats:', error);
    }

    return stats;
  }

  destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }
    this.clear();
  }
}

// Create singleton instance
export const cacheService = new CacheService();

// Export class for testing
export { CacheService };