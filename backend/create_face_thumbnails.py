#!/usr/bin/env python3
"""
Create missing face thumbnails for existing persons.
"""

import os
import shutil
from pathlib import Path
import logging
from PIL import Image
import face_recognition
import numpy as np
from app.database import SessionLocal
from app.models import Person, Photo, FaceDetection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_and_save_face_thumbnail(image_path, face_location, person_id, padding=30):
    """Extract face thumbnail and save it."""
    try:
        # Load image
        image = face_recognition.load_image_file(str(image_path))

        # Convert from PIL to numpy array format for face_recognition
        top, right, bottom, left = face_location

        # Add padding
        height, width = image.shape[:2]
        top = max(0, top - padding)
        right = min(width, right + padding)
        bottom = min(height, bottom + padding)
        left = max(0, left - padding)

        # Extract face region
        face_image = image[top:bottom, left:right]

        # Convert to PIL for resizing and saving
        face_pil = Image.fromarray(face_image)
        face_pil = face_pil.resize((150, 150), Image.Resampling.LANCZOS)

        # Create faces directory
        faces_dir = Path("/app/static/faces")
        faces_dir.mkdir(parents=True, exist_ok=True)

        # Save thumbnail
        thumbnail_path = faces_dir / f"person_{person_id}.jpg"
        face_pil.save(thumbnail_path, "JPEG", quality=90)

        logger.info(f"Created face thumbnail for person {person_id}")
        return True

    except Exception as e:
        logger.error(f"Error creating face thumbnail for person {person_id}: {e}")
        return False

def create_face_thumbnails():
    """Create face thumbnails for all persons."""

    db = SessionLocal()

    try:
        # Get all persons
        persons = db.query(Person).all()
        logger.info(f"Found {len(persons)} persons")

        created_count = 0

        for person in persons:
            # Get the first face detection for this person
            face_detection = db.query(FaceDetection).filter(
                FaceDetection.person_id == person.id
            ).first()

            if not face_detection:
                logger.warning(f"No face detection found for person {person.id}")
                continue

            # Get the photo for this face detection
            photo = db.query(Photo).filter(Photo.id == face_detection.photo_id).first()
            if not photo:
                logger.warning(f"No photo found for face detection {face_detection.id}")
                continue

            # Build image path
            image_path = Path("/app/uploads") / photo.filename
            if not image_path.exists():
                logger.warning(f"Image file not found: {image_path}")
                continue

            # Extract face location
            bbox = face_detection.bounding_box
            face_location = (bbox['top'], bbox['right'], bbox['bottom'], bbox['left'])

            # Create face thumbnail using person.id directly
            success = extract_and_save_face_thumbnail(
                image_path,
                face_location,
                person.id
            )

            if success:
                created_count += 1

        logger.info(f"Created {created_count} face thumbnails")

    except Exception as e:
        logger.error(f"Error creating face thumbnails: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_face_thumbnails()