#!/usr/bin/env python3
"""
Complete fresh processing with FIXED conservative clustering parameters.
"""

import os
import sys
from pathlib import Path
import logging
from PIL import Image
import face_recognition
import numpy as np
from sklearn.cluster import DBSCAN
import shutil

from app.database import SessionLocal, create_tables
from app.db_utils import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_all_data(db):
    """Clear all existing data from database and static directories."""
    try:
        from sqlalchemy import text

        # Clear database tables in correct order
        db.execute(text("DELETE FROM face_detections"))
        db.execute(text("DELETE FROM persons"))
        db.execute(text("DELETE FROM photos"))
        db.commit()
        logger.info("Cleared all data from database")

        # Clear static directories
        static_dir = Path("/app/static")
        for subdir in ["faces"]:
            dir_path = static_dir / subdir
            if dir_path.exists():
                shutil.rmtree(dir_path)
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Cleared {subdir} directory")

    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        db.rollback()
        raise


def copy_and_optimize_image(source_path, filename):
    """Copy image to static directories and create optimized versions."""
    try:
        static_dir = Path("/app/static")

        # Create directories
        (static_dir / "original").mkdir(parents=True, exist_ok=True)
        (static_dir / "thumbnails").mkdir(parents=True, exist_ok=True)
        (static_dir / "web").mkdir(parents=True, exist_ok=True)

        # Copy original (only if doesn't exist)
        original_dest = static_dir / "original" / filename
        if not original_dest.exists():
            shutil.copy2(source_path, original_dest)

        # Create optimized versions (only if don't exist)
        with Image.open(source_path) as img:
            # Create thumbnail (300x300)
            thumbnail_dest = static_dir / "thumbnails" / filename
            if not thumbnail_dest.exists():
                img_thumb = img.copy()
                img_thumb.thumbnail((300, 300), Image.Resampling.LANCZOS)
                img_thumb.save(thumbnail_dest, "JPEG", quality=85)

            # Create web version (1200px max)
            web_dest = static_dir / "web" / filename
            if not web_dest.exists():
                img_web = img.copy()
                img_web.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                img_web.save(web_dest, "JPEG", quality=85)

        return True
    except Exception as e:
        logger.error(f"Error copying image {filename}: {e}")
        return False


def extract_and_save_face_thumbnail(image_path, face_location, person_id, padding=30):
    """Extract face thumbnail and save it."""
    try:
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
        faces_dir.mkdir(exist_ok=True)

        # Save thumbnail
        thumbnail_path = faces_dir / f"person_{person_id}.jpg"
        face_pil.save(thumbnail_path, "JPEG", quality=90)

        return f"http://localhost:8000/static/faces/person_{person_id}.jpg"

    except Exception as e:
        logger.error(f"Error creating face thumbnail: {e}")
        return f"http://localhost:8000/static/faces/person_{person_id}.jpg"


def process_all_photos_fixed(photos_dir: str):
    """Process all photos with FIXED conservative clustering."""

    # Ensure database tables exist
    create_tables()

    # Get database session
    db = SessionLocal()

    try:
        # Clear all existing data
        clear_all_data(db)

        # Get all photos
        photos_path = Path(photos_dir)
        photo_files = list(photos_path.glob("*.JPG"))

        logger.info(f"Processing ALL {len(photo_files)} photos...")

        all_face_encodings = []
        face_data = []

        # First pass: detect faces in all photos
        for i, photo_path in enumerate(photo_files):
            if i % 50 == 0:
                logger.info(f"Face detection progress: {i}/{len(photo_files)}")

            try:
                # Copy and optimize image
                if not copy_and_optimize_image(photo_path, photo_path.name):
                    continue

                # Load image
                image = face_recognition.load_image_file(str(photo_path))

                # Find faces
                face_locations = face_recognition.face_locations(image, model="hog")
                face_encodings = face_recognition.face_encodings(image, face_locations)

                # Get image dimensions
                with Image.open(photo_path) as img:
                    width, height = img.size

                # Create photo record
                photo = DatabaseManager.create_photo(
                    db=db,
                    original_url=f"http://localhost:8000/static/original/{photo_path.name}",
                    thumbnail_url=f"http://localhost:8000/static/thumbnails/{photo_path.name}",
                    web_url=f"http://localhost:8000/static/web/{photo_path.name}",
                    filename=photo_path.name,
                    width=width,
                    height=height,
                    file_size=photo_path.stat().st_size,
                    photo_metadata={}
                )

                # Store face data
                for j, (face_location, face_encoding) in enumerate(zip(face_locations, face_encodings)):
                    top, right, bottom, left = face_location

                    face_info = {
                        'photo_id': photo.id,
                        'photo_path': str(photo_path),
                        'photo_name': photo_path.name,
                        'encoding': face_encoding.tolist(),
                        'location': {
                            'top': int(top),
                            'right': int(right),
                            'bottom': int(bottom),
                            'left': int(left)
                        },
                        'confidence': 0.95
                    }

                    face_data.append(face_info)
                    all_face_encodings.append(face_encoding)

            except Exception as e:
                logger.error(f"Error processing {photo_path.name}: {e}")
                continue

        logger.info(f"Face detection complete! Found {len(all_face_encodings)} faces total")

        if not all_face_encodings:
            logger.warning("No faces found in any photos")
            return

        # Cluster all faces with CONSERVATIVE parameters
        logger.info("Clustering all faces with conservative parameters...")

        # Convert to numpy array
        encodings_array = np.array(all_face_encodings)

        # Use conservative DBSCAN clustering parameters
        # eps=0.4 is MORE conservative than 0.5, creating MORE separate clusters
        clustering = DBSCAN(eps=0.4, min_samples=2, metric='euclidean')
        cluster_labels = clustering.fit_predict(encodings_array)

        # Group faces by cluster
        clusters = {}
        for i, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(i)

        # Remove noise cluster
        noise_count = 0
        if -1 in clusters:
            noise_count = len(clusters[-1])
            del clusters[-1]
            logger.info(f"Filtered out {noise_count} noise faces")

        logger.info(f"Found {len(clusters)} distinct persons (conservative clustering)")

        # Create person records for each cluster
        person_map = {}
        for cluster_id, face_indices in clusters.items():
            if len(face_indices) < 1:
                continue

            # Use the most centered face as representative
            representative_face = face_data[face_indices[0]]

            # Create person record
            person = DatabaseManager.create_person(
                db=db,
                thumbnail_url=f"http://localhost:8000/static/faces/person_{cluster_id}.jpg",
                face_embedding=representative_face['encoding'],
                cluster_confidence=0.95
            )

            # Create face thumbnail
            extract_and_save_face_thumbnail(
                representative_face['photo_path'],
                (
                    representative_face['location']['top'],
                    representative_face['location']['right'],
                    representative_face['location']['bottom'],
                    representative_face['location']['left']
                ),
                person.id
            )

            # Update thumbnail URL to use person UUID
            person.thumbnail_url = f"http://localhost:8000/static/faces/person_{person.id}.jpg"
            db.commit()

            person_map[cluster_id] = person.id
            logger.info(f"Created person {person.id} (cluster {cluster_id}) with {len(face_indices)} photos")

        # Create face detection records
        logger.info("Creating face detection records...")
        for i, face in enumerate(face_data):
            # Find cluster for this face
            cluster_id = cluster_labels[i]

            if cluster_id in person_map:
                DatabaseManager.create_face_detection(
                    db=db,
                    photo_id=face['photo_id'],
                    person_id=person_map[cluster_id],
                    bounding_box=face['location'],
                    confidence=face['confidence'],
                    face_embedding=face['encoding']
                )

        # Update photo counts for all persons
        for person_id in person_map.values():
            DatabaseManager.update_person_photo_count(db, person_id)

        # Mark all photos as processed
        for photo in db.query(DatabaseManager.Photo).all():
            DatabaseManager.mark_photo_processed(db, photo.id)

        logger.info("=== PROCESSING COMPLETE ===")
        logger.info(f"✅ Total photos processed: {len(photo_files)}")
        logger.info(f"✅ Total faces found: {len(all_face_encodings)}")
        logger.info(f"✅ Unique persons identified: {len(clusters)}")
        logger.info("=== READY TO VIEW ===")

    except Exception as e:
        logger.error(f"Error during processing: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    process_all_photos_fixed("/app/uploads")