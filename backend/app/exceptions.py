"""Custom exceptions for the photo gallery application."""

from typing import Any, Dict, Optional


class PhotoGalleryException(Exception):
    """Base exception for photo gallery application."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(PhotoGalleryException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field = field


class NotFoundError(PhotoGalleryException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str, identifier: str, **kwargs):
        message = f"{resource} with ID '{identifier}' not found"
        super().__init__(message, error_code="NOT_FOUND", **kwargs)
        self.resource = resource
        self.identifier = identifier


class DatabaseError(PhotoGalleryException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="DATABASE_ERROR", **kwargs)
        self.operation = operation


class ProcessingError(PhotoGalleryException):
    """Raised when photo processing fails."""
    
    def __init__(self, message: str, photo_path: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="PROCESSING_ERROR", **kwargs)
        self.photo_path = photo_path


class StorageError(PhotoGalleryException):
    """Raised when storage operations fail."""
    
    def __init__(self, message: str, storage_type: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="STORAGE_ERROR", **kwargs)
        self.storage_type = storage_type


class CacheError(PhotoGalleryException):
    """Raised when cache operations fail."""
    
    def __init__(self, message: str, cache_key: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="CACHE_ERROR", **kwargs)
        self.cache_key = cache_key


class RateLimitError(PhotoGalleryException):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(message, error_code="RATE_LIMIT_EXCEEDED", **kwargs)


class AuthenticationError(PhotoGalleryException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(message, error_code="AUTHENTICATION_ERROR", **kwargs)


class AuthorizationError(PhotoGalleryException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(message, error_code="AUTHORIZATION_ERROR", **kwargs)


class ConfigurationError(PhotoGalleryException):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)
        self.config_key = config_key


class ExternalServiceError(PhotoGalleryException):
    """Raised when external service calls fail."""
    
    def __init__(self, message: str, service: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="EXTERNAL_SERVICE_ERROR", **kwargs)
        self.service = service