"""Application configuration settings."""

import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database settings
    database_url: str = "postgresql://gallery_user:gallery_password@localhost:5432/photo_gallery"
    database_echo: bool = False
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    redis_cache_ttl: int = 3600  # 1 hour
    
    # Storage settings
    upload_dir: str = "./uploads"
    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list = ["jpg", "jpeg", "png", "heic"]
    
    # AWS S3 settings (optional)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    
    # Cloudinary settings (optional)
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None
    
    # Face recognition settings
    face_detection_model: str = "hog"  # or 'cnn'
    clustering_eps: float = 0.6
    clustering_min_samples: int = 2
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    
    # Logging settings
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()