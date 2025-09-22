"""Pydantic schemas for API request/response models."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class PersonBase(BaseModel):
    """Base person schema."""
    thumbnail_url: str = Field(..., description="URL to person's thumbnail image")
    photo_count: int = Field(default=0, description="Number of photos containing this person")
    cluster_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score for face clustering")


class PersonCreate(PersonBase):
    """Schema for creating a person."""
    face_embedding: List[float] = Field(..., description="128-dimensional face encoding")


class PersonUpdate(BaseModel):
    """Schema for updating a person."""
    thumbnail_url: Optional[str] = None
    photo_count: Optional[int] = None
    cluster_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class Person(PersonBase):
    """Schema for person response."""
    id: str = Field(..., description="Unique person identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class PersonThumbnail(BaseModel):
    """Schema for person thumbnail (used in gallery homepage)."""
    id: str = Field(..., description="Unique person identifier")
    thumbnail_url: str = Field(..., description="URL to person's thumbnail image")
    photo_count: int = Field(..., description="Number of photos containing this person")
    cluster_confidence: float = Field(..., description="Confidence score for face clustering")


class PhotoBase(BaseModel):
    """Base photo schema."""
    original_url: str = Field(..., description="URL to original image")
    thumbnail_url: str = Field(..., description="URL to thumbnail image")
    web_url: str = Field(..., description="URL to web-optimized image")
    filename: str = Field(..., description="Original filename")
    width: int = Field(..., gt=0, description="Image width in pixels")
    height: int = Field(..., gt=0, description="Image height in pixels")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    taken_at: Optional[datetime] = Field(None, description="When photo was taken")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class PhotoCreate(PhotoBase):
    """Schema for creating a photo."""
    pass


class PhotoUpdate(BaseModel):
    """Schema for updating a photo."""
    original_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    web_url: Optional[str] = None
    filename: Optional[str] = None
    width: Optional[int] = Field(None, gt=0)
    height: Optional[int] = Field(None, gt=0)
    file_size: Optional[int] = Field(None, gt=0)
    taken_at: Optional[datetime] = None
    processed: Optional[bool] = None
    processing_error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Photo(PhotoBase):
    """Schema for photo response."""
    id: str = Field(..., description="Unique photo identifier")
    processed: bool = Field(..., description="Whether photo has been processed")
    processing_error: Optional[str] = Field(None, description="Processing error message if any")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    persons: List[str] = Field(default_factory=list, description="List of person IDs detected in photo")
    
    model_config = ConfigDict(from_attributes=True)


class FaceDetectionBase(BaseModel):
    """Base face detection schema."""
    bounding_box: Dict[str, int] = Field(..., description="Face bounding box coordinates")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")


class FaceDetectionCreate(FaceDetectionBase):
    """Schema for creating a face detection."""
    photo_id: str = Field(..., description="Photo ID")
    person_id: str = Field(..., description="Person ID")
    face_embedding: List[float] = Field(..., description="128-dimensional face encoding")


class FaceDetection(FaceDetectionBase):
    """Schema for face detection response."""
    id: str = Field(..., description="Unique face detection identifier")
    photo_id: str = Field(..., description="Photo ID")
    person_id: str = Field(..., description="Person ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class PersonsResponse(BaseModel):
    """Schema for persons list response."""
    persons: List[PersonThumbnail] = Field(..., description="List of persons")
    total: int = Field(..., description="Total number of persons")


class PhotosResponse(BaseModel):
    """Schema for photos list response."""
    photos: List[Photo] = Field(..., description="List of photos")
    total: int = Field(..., description="Total number of photos")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Health status")
    timestamp: float = Field(..., description="Response timestamp")


class ProcessingStatus(BaseModel):
    """Schema for processing status."""
    total_photos: int = Field(..., description="Total number of photos")
    processed_photos: int = Field(..., description="Number of processed photos")
    failed_photos: int = Field(..., description="Number of failed photos")
    total_faces: int = Field(..., description="Total faces detected")
    total_persons: int = Field(..., description="Total persons identified")
    processing_complete: bool = Field(..., description="Whether processing is complete")


class BatchProcessingRequest(BaseModel):
    """Schema for batch processing request."""
    input_directory: str = Field(..., description="Directory containing photos to process")
    batch_size: int = Field(default=10, ge=1, le=100, description="Number of photos to process in parallel")
    face_detection_model: str = Field(default="hog", description="Face detection model ('hog' or 'cnn')")
    clustering_eps: float = Field(default=0.6, ge=0.1, le=1.0, description="DBSCAN eps parameter")
    clustering_min_samples: int = Field(default=2, ge=1, le=10, description="DBSCAN min_samples parameter")