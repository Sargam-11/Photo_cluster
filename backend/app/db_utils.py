"""Database utilities and helper functions."""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from .database import SessionLocal, engine
from .models import Person, Photo, FaceDetection

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for common operations."""
    
    @staticmethod
    def get_session() -> Session:
        """Get a new database session."""
        return SessionLocal()
    
    @staticmethod
    def test_connection() -> bool:
        """Test database connection."""
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    @staticmethod
    def create_person(
        db: Session,
        thumbnail_url: str,
        face_embedding: List[float],
        cluster_confidence: float = 0.0
    ) -> Person:
        """Create a new person record."""
        try:
            person = Person(
                thumbnail_url=thumbnail_url,
                face_embedding=face_embedding,
                cluster_confidence=cluster_confidence
            )
            db.add(person)
            db.commit()
            db.refresh(person)
            logger.info(f"Created person with ID: {person.id}")
            return person
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to create person: {e}")
            raise
    
    @staticmethod
    def create_photo(
        db: Session,
        original_url: str,
        thumbnail_url: str,
        web_url: str,
        filename: str,
        width: int,
        height: int,
        file_size: int,
        taken_at: Optional[str] = None,
        photo_metadata: Optional[Dict[str, Any]] = None
    ) -> Photo:
        """Create a new photo record."""
        try:
            photo = Photo(
                original_url=original_url,
                thumbnail_url=thumbnail_url,
                web_url=web_url,
                filename=filename,
                width=width,
                height=height,
                file_size=file_size,
                taken_at=taken_at,
                photo_metadata=photo_metadata or {}
            )
            db.add(photo)
            db.commit()
            db.refresh(photo)
            logger.info(f"Created photo with ID: {photo.id}")
            return photo
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to create photo: {e}")
            raise
    
    @staticmethod
    def create_face_detection(
        db: Session,
        photo_id: str,
        person_id: str,
        bounding_box: Dict[str, float],
        confidence: float,
        face_embedding: List[float]
    ) -> FaceDetection:
        """Create a new face detection record."""
        try:
            face_detection = FaceDetection(
                photo_id=photo_id,
                person_id=person_id,
                bounding_box=bounding_box,
                confidence=confidence,
                face_embedding=face_embedding
            )
            db.add(face_detection)
            db.commit()
            db.refresh(face_detection)
            logger.info(f"Created face detection with ID: {face_detection.id}")
            return face_detection
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to create face detection: {e}")
            raise
    
    @staticmethod
    def get_all_persons(db: Session, limit: int = 100, offset: int = 0) -> List[Person]:
        """Get all persons with pagination."""
        try:
            return db.query(Person).offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get persons: {e}")
            raise
    
    @staticmethod
    def get_person_by_id(db: Session, person_id: str) -> Optional[Person]:
        """Get person by ID."""
        try:
            return db.query(Person).filter(Person.id == person_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get person {person_id}: {e}")
            raise
    
    @staticmethod
    def get_photos_by_person(
        db: Session, 
        person_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Photo]:
        """Get all photos containing a specific person."""
        try:
            return (
                db.query(Photo)
                .join(FaceDetection)
                .filter(FaceDetection.person_id == person_id)
                .offset(offset)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Failed to get photos for person {person_id}: {e}")
            raise
    
    @staticmethod
    def get_photo_by_id(db: Session, photo_id: str) -> Optional[Photo]:
        """Get photo by ID."""
        try:
            return db.query(Photo).filter(Photo.id == photo_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get photo {photo_id}: {e}")
            raise
    
    @staticmethod
    def update_person_photo_count(db: Session, person_id: str) -> None:
        """Update the photo count for a person."""
        try:
            person = db.query(Person).filter(Person.id == person_id).first()
            if person:
                photo_count = (
                    db.query(FaceDetection)
                    .filter(FaceDetection.person_id == person_id)
                    .count()
                )
                person.photo_count = photo_count
                db.commit()
                logger.info(f"Updated photo count for person {person_id}: {photo_count}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to update photo count for person {person_id}: {e}")
            raise
    
    @staticmethod
    def mark_photo_processed(
        db: Session, 
        photo_id: str, 
        error: Optional[str] = None
    ) -> None:
        """Mark a photo as processed."""
        try:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if photo:
                photo.processed = True
                if error:
                    photo.processing_error = error
                db.commit()
                logger.info(f"Marked photo {photo_id} as processed")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to mark photo {photo_id} as processed: {e}")
            raise