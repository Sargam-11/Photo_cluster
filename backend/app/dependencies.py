"""FastAPI dependencies for dependency injection."""

import logging
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
import redis
from redis.exceptions import ConnectionError as RedisConnectionError

from .database import get_db
from .config import settings

logger = logging.getLogger(__name__)

# Redis client (initialized lazily)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance.
    
    Returns:
        Redis client or None if connection fails
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis connection established")
        except (RedisConnectionError, Exception) as e:
            logger.warning(f"Redis connection failed: {e}")
            _redis_client = None
    
    return _redis_client


def get_db_session() -> Generator[Session, None, None]:
    """Get database session dependency.
    
    Yields:
        Database session
    """
    db = next(get_db())
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    finally:
        db.close()


def get_cache_client() -> Optional[redis.Redis]:
    """Get cache client dependency.
    
    Returns:
        Redis client or None if not available
    """
    return get_redis_client()


class CacheService:
    """Service for caching operations."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize cache service.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis_client = redis_client
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        if not self.redis_client:
            return False
        
        try:
            if ttl:
                return self.redis_client.setex(key, ttl, value)
            else:
                return self.redis_client.set(key, value)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful
        """
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False


def get_cache_service(redis_client: Optional[redis.Redis] = Depends(get_cache_client)) -> CacheService:
    """Get cache service dependency.
    
    Args:
        redis_client: Redis client instance
        
    Returns:
        Cache service instance
    """
    return CacheService(redis_client)


def validate_pagination(page: int = 1, per_page: int = 20) -> tuple[int, int]:
    """Validate pagination parameters.
    
    Args:
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Tuple of (offset, limit)
        
    Raises:
        HTTPException: If parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be >= 1"
        )
    
    if per_page < 1 or per_page > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Per page must be between 1 and 100"
        )
    
    offset = (page - 1) * per_page
    return offset, per_page


class PaginationParams:
    """Pagination parameters dependency."""
    
    def __init__(self, page: int = 1, per_page: int = 20):
        """Initialize pagination parameters.
        
        Args:
            page: Page number (1-based)
            per_page: Items per page
        """
        self.offset, self.limit = validate_pagination(page, per_page)
        self.page = page
        self.per_page = per_page