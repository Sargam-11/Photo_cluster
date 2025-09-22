"""SQLAlchemy models for the photo gallery application."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, 
    ForeignKey, Boolean, ARRAY, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .database import Base


class Person(Base):
    """Model for detected persons in photos."""
    
    __tablename__ = "persons"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=False)
    photo_count: Mapped[int] = mapped_column(Integer, default=0)
    face_embedding: Mapped[List[float]] = mapped_column(ARRAY(Float), nullable=False)
    cluster_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    face_detections: Mapped[List["FaceDetection"]] = relationship(
        "FaceDetection", 
        back_populates="person",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Person(id={self.id}, photo_count={self.photo_count})>"


class Photo(Base):
    """Model for photos in the gallery."""
    
    __tablename__ = "photos"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    original_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=False)
    web_url: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    taken_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_error: Mapped[Optional[str]] = mapped_column(Text)
    photo_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    face_detections: Mapped[List["FaceDetection"]] = relationship(
        "FaceDetection", 
        back_populates="photo",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Photo(id={self.id}, filename={self.filename})>"


class FaceDetection(Base):
    """Model for face detections in photos."""
    
    __tablename__ = "face_detections"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    photo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("photos.id", ondelete="CASCADE"),
        nullable=False
    )
    person_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        ForeignKey("persons.id", ondelete="CASCADE"),
        nullable=False
    )
    bounding_box: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    face_embedding: Mapped[List[float]] = mapped_column(ARRAY(Float), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    # Relationships
    photo: Mapped["Photo"] = relationship("Photo", back_populates="face_detections")
    person: Mapped["Person"] = relationship("Person", back_populates="face_detections")
    
    def __repr__(self) -> str:
        return f"<FaceDetection(id={self.id}, photo_id={self.photo_id}, person_id={self.person_id})>"