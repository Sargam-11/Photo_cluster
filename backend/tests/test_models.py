"""Tests for database models."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Person, Photo, FaceDetection
from app.db_utils import DatabaseManager


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def test_db():
    """Create test database session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestPersonModel:
    """Test Person model."""
    
    def test_create_person(self, test_db):
        """Test creating a person."""
        person = Person(
            thumbnail_url="https://example.com/thumb.jpg",
            face_embedding=[0.1, 0.2, 0.3],
            cluster_confidence=0.95
        )
        test_db.add(person)
        test_db.commit()
        
        assert person.id is not None
        assert person.thumbnail_url == "https://example.com/thumb.jpg"
        assert person.face_embedding == [0.1, 0.2, 0.3]
        assert person.cluster_confidence == 0.95
        assert person.photo_count == 0
        assert isinstance(person.created_at, datetime)
    
    def test_person_relationships(self, test_db):
        """Test person relationships."""
        person = Person(
            thumbnail_url="https://example.com/thumb.jpg",
            face_embedding=[0.1, 0.2, 0.3]
        )
        test_db.add(person)
        test_db.commit()
        
        # Initially no face detections
        assert len(person.face_detections) == 0
    
    def test_person_repr(self, test_db):
        """Test person string representation."""
        person = Person(
            thumbnail_url="https://example.com/thumb.jpg",
            face_embedding=[0.1, 0.2, 0.3],
            photo_count=5
        )
        test_db.add(person)
        test_db.commit()
        
        repr_str = repr(person)
        assert "Person" in repr_str
        assert person.id in repr_str
        assert "5" in repr_str


class TestPhotoModel:
    """Test Photo model."""
    
    def test_create_photo(self, test_db):
        """Test creating a photo."""
        photo = Photo(
            original_url="https://example.com/original.jpg",
            thumbnail_url="https://example.com/thumb.jpg",
            web_url="https://example.com/web.jpg",
            filename="test_photo.jpg",
            width=1920,
            height=1080,
            file_size=2048000,
            metadata={"camera": "Canon EOS R5"}
        )
        test_db.add(photo)
        test_db.commit()
        
        assert photo.id is not None
        assert photo.filename == "test_photo.jpg"
        assert photo.width == 1920
        assert photo.height == 1080
        assert photo.file_size == 2048000
        assert photo.processed is False
        assert photo.metadata["camera"] == "Canon EOS R5"
        assert isinstance(photo.created_at, datetime)
    
    def test_photo_relationships(self, test_db):
        """Test photo relationships."""
        photo = Photo(
            original_url="https://example.com/original.jpg",
            thumbnail_url="https://example.com/thumb.jpg",
            web_url="https://example.com/web.jpg",
            filename="test_photo.jpg",
            width=1920,
            height=1080,
            file_size=2048000
        )
        test_db.add(photo)
        test_db.commit()
        
        # Initially no face detections
        assert len(photo.face_detections) == 0
    
    def test_photo_repr(self, test_db):
        """Test photo string representation."""
        photo = Photo(
            original_url="https://example.com/original.jpg",
            thumbnail_url="https://example.com/thumb.jpg",
            web_url="https://example.com/web.jpg",
            filename="test_photo.jpg",
            width=1920,
            height=1080,
            file_size=2048000
        )
        test_db.add(photo)
        test_db.commit()
        
        repr_str = repr(photo)
        assert "Photo" in repr_str
        assert photo.id in repr_str
        assert "test_photo.jpg" in repr_str


class TestFaceDetectionModel:
    """Test FaceDetection model."""
    
    def test_create_face_detection(self, test_db):
        """Test creating a face detection."""
        # Create person and photo first
        person = Person(
            thumbnail_url="https://example.com/thumb.jpg",
            face_embedding=[0.1, 0.2, 0.3]
        )
        photo = Photo(
            original_url="https://example.com/original.jpg",
            thumbnail_url="https://example.com/thumb.jpg",
            web_url="https://example.com/web.jpg",
            filename="test_photo.jpg",
            width=1920,
            height=1080,
            file_size=2048000
        )
        test_db.add(person)
        test_db.add(photo)
        test_db.commit()
        
        # Create face detection
        face_detection = FaceDetection(
            photo_id=photo.id,
            person_id=person.id,
            bounding_box={"top": 100, "right": 200, "bottom": 300, "left": 50},
            confidence=0.95,
            face_embedding=[0.1, 0.2, 0.3, 0.4]
        )
        test_db.add(face_detection)
        test_db.commit()
        
        assert face_detection.id is not None
        assert face_detection.photo_id == photo.id
        assert face_detection.person_id == person.id
        assert face_detection.confidence == 0.95
        assert face_detection.bounding_box["top"] == 100
        assert face_detection.face_embedding == [0.1, 0.2, 0.3, 0.4]
        assert isinstance(face_detection.created_at, datetime)
    
    def test_face_detection_relationships(self, test_db):
        """Test face detection relationships."""
        # Create person and photo first
        person = Person(
            thumbnail_url="https://example.com/thumb.jpg",
            face_embedding=[0.1, 0.2, 0.3]
        )
        photo = Photo(
            original_url="https://example.com/original.jpg",
            thumbnail_url="https://example.com/thumb.jpg",
            web_url="https://example.com/web.jpg",
            filename="test_photo.jpg",
            width=1920,
            height=1080,
            file_size=2048000
        )
        test_db.add(person)
        test_db.add(photo)
        test_db.commit()
        
        # Create face detection
        face_detection = FaceDetection(
            photo_id=photo.id,
            person_id=person.id,
            bounding_box={"top": 100, "right": 200, "bottom": 300, "left": 50},
            confidence=0.95,
            face_embedding=[0.1, 0.2, 0.3, 0.4]
        )
        test_db.add(face_detection)
        test_db.commit()
        
        # Test relationships
        assert face_detection.photo == photo
        assert face_detection.person == person
        assert face_detection in photo.face_detections
        assert face_detection in person.face_detections
    
    def test_face_detection_repr(self, test_db):
        """Test face detection string representation."""
        # Create person and photo first
        person = Person(
            thumbnail_url="https://example.com/thumb.jpg",
            face_embedding=[0.1, 0.2, 0.3]
        )
        photo = Photo(
            original_url="https://example.com/original.jpg",
            thumbnail_url="https://example.com/thumb.jpg",
            web_url="https://example.com/web.jpg",
            filename="test_photo.jpg",
            width=1920,
            height=1080,
            file_size=2048000
        )
        test_db.add(person)
        test_db.add(photo)
        test_db.commit()
        
        face_detection = FaceDetection(
            photo_id=photo.id,
            person_id=person.id,
            bounding_box={"top": 100, "right": 200, "bottom": 300, "left": 50},
            confidence=0.95,
            face_embedding=[0.1, 0.2, 0.3, 0.4]
        )
        test_db.add(face_detection)
        test_db.commit()
        
        repr_str = repr(face_detection)
        assert "FaceDetection" in repr_str
        assert face_detection.id in repr_str
        assert photo.id in repr_str
        assert person.id in repr_str


class TestDatabaseManager:
    """Test DatabaseManager utility functions."""
    
    def test_create_person(self, test_db):
        """Test creating person via DatabaseManager."""
        person = DatabaseManager.create_person(
            test_db,
            thumbnail_url="https://example.com/thumb.jpg",
            face_embedding=[0.1, 0.2, 0.3],
            cluster_confidence=0.95
        )
        
        assert person.id is not None
        assert person.thumbnail_url == "https://example.com/thumb.jpg"
        assert person.cluster_confidence == 0.95
    
    def test_create_photo(self, test_db):
        """Test creating photo via DatabaseManager."""
        photo = DatabaseManager.create_photo(
            test_db,
            original_url="https://example.com/original.jpg",
            thumbnail_url="https://example.com/thumb.jpg",
            web_url="https://example.com/web.jpg",
            filename="test_photo.jpg",
            width=1920,
            height=1080,
            file_size=2048000,
            metadata={"camera": "Canon EOS R5"}
        )
        
        assert photo.id is not None
        assert photo.filename == "test_photo.jpg"
        assert photo.metadata["camera"] == "Canon EOS R5"
    
    def test_get_person_by_id(self, test_db):
        """Test getting person by ID."""
        person = DatabaseManager.create_person(
            test_db,
            thumbnail_url="https://example.com/thumb.jpg",
            face_embedding=[0.1, 0.2, 0.3]
        )
        
        retrieved_person = DatabaseManager.get_person_by_id(test_db, person.id)
        assert retrieved_person is not None
        assert retrieved_person.id == person.id
        
        # Test non-existent person
        non_existent = DatabaseManager.get_person_by_id(test_db, "non-existent-id")
        assert non_existent is None