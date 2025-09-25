#!/usr/bin/env python3
"""
Process photos locally and upload results directly to production database.
This bypasses the API and connects directly to the PostgreSQL database.
"""

import os
import sys
import logging
import psycopg2
from pathlib import Path
import face_recognition
import numpy as np
from sklearn.cluster import DBSCAN
from PIL import Image
import io
import base64
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Production database URL
DATABASE_URL = "postgresql://photo_gallery_user:Gm5s8xpq5BYEfUaHqE1JRJGu3vAcYOHP@dpg-ctpvn8rqf0us73b5mjj0-a.oregon-postgres.render.com/photo_gallery_1nso"

def connect_to_db():
    """Connect to the production PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def clear_existing_data():
    """Clear existing data from production database."""
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        logger.info("Clearing existing data...")
        cursor.execute("DELETE FROM face_detections")
        cursor.execute("DELETE FROM persons")
        cursor.execute("DELETE FROM photos")
        conn.commit()
        logger.info("✅ Cleared existing data")
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def encode_face_thumbnail(image_array, face_location, padding=30):
    """Create a face thumbnail and encode it as base64."""
    try:
        top, right, bottom, left = face_location

        # Add padding
        height, width = image_array.shape[:2]
        top = max(0, top - padding)
        right = min(width, right + padding)
        bottom = min(height, bottom + padding)
        left = max(0, left - padding)

        # Extract face
        face_image = image_array[top:bottom, left:right]

        # Convert to PIL Image
        pil_image = Image.fromarray(face_image)

        # Resize to thumbnail
        pil_image.thumbnail((150, 150), Image.Resampling.LANCZOS)

        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=85)
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        logger.error(f"Error creating face thumbnail: {e}")
        return None

def process_photos():
    """Process all photos and upload to database."""
    uploads_dir = Path("backend/uploads_sample")

    if not uploads_dir.exists():
        logger.error(f"Uploads directory not found: {uploads_dir}")
        return

    # Get photo files
    photo_files = list(uploads_dir.glob("*.jpg")) + list(uploads_dir.glob("*.JPG"))
    logger.info(f"Found {len(photo_files)} photos to process")

    if not photo_files:
        logger.error("No photo files found!")
        return

    # Connect to database
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        # Process each photo
        all_face_encodings = []
        all_face_data = []

        for photo_path in photo_files:
            logger.info(f"Processing {photo_path.name}...")

            try:
                # Get image info
                with Image.open(photo_path) as img:
                    width, height = img.size
                    file_size = photo_path.stat().st_size

                # Create mock URLs (since we can't host files, we'll use placeholders)
                base_filename = photo_path.stem
                original_url = f"https://photo-gallery-backend-z2v3.onrender.com/static/original/{photo_path.name}"
                web_url = f"https://photo-gallery-backend-z2v3.onrender.com/static/web/{photo_path.name}"
                thumbnail_url = f"https://photo-gallery-backend-z2v3.onrender.com/static/thumbnails/{photo_path.name}"

                # Insert photo into database
                cursor.execute("""
                    INSERT INTO photos (
                        filename, original_filename, original_url, web_url, thumbnail_url,
                        width, height, file_size, processed, upload_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    photo_path.name, photo_path.name, original_url, web_url, thumbnail_url,
                    width, height, file_size, True, datetime.utcnow()
                ))

                photo_id = cursor.fetchone()[0]
                logger.info(f"✅ Added photo to DB with ID: {photo_id}")

                # Process faces
                image = face_recognition.load_image_file(str(photo_path))
                face_locations = face_recognition.face_locations(image, model="hog")
                face_encodings = face_recognition.face_encodings(image, face_locations)

                logger.info(f"Found {len(face_locations)} faces in {photo_path.name}")

                for i, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
                    # Create face thumbnail
                    thumbnail_data = encode_face_thumbnail(image, face_location)

                    all_face_encodings.append(face_encoding)
                    all_face_data.append({
                        'photo_id': photo_id,
                        'face_location': face_location,
                        'face_encoding': face_encoding,
                        'thumbnail_data': thumbnail_data
                    })

            except Exception as e:
                logger.error(f"❌ Error processing {photo_path.name}: {e}")
                continue

        # Cluster faces
        if all_face_encodings:
            logger.info(f"Clustering {len(all_face_encodings)} faces...")

            # Use conservative clustering parameters
            clustering = DBSCAN(eps=0.4, min_samples=1, metric='euclidean')
            face_clusters = clustering.fit_predict(all_face_encodings)

            # Create persons and face detections
            person_clusters = {}

            for idx, cluster_id in enumerate(face_clusters):
                face_data = all_face_data[idx]

                # Create person if not exists
                if cluster_id not in person_clusters:
                    # Use the first face thumbnail as person thumbnail
                    thumbnail_url = face_data['thumbnail_data'] or "https://via.placeholder.com/150"

                    cursor.execute("""
                        INSERT INTO persons (name, thumbnail_url, photo_count, cluster_confidence)
                        VALUES (%s, %s, %s, %s) RETURNING id
                    """, (f"Person {len(person_clusters) + 1}", thumbnail_url, 0, 0.8))

                    person_id = cursor.fetchone()[0]
                    person_clusters[cluster_id] = person_id
                    logger.info(f"✅ Created Person {len(person_clusters)} with ID: {person_id}")
                else:
                    person_id = person_clusters[cluster_id]

                # Insert face detection
                top, right, bottom, left = face_data['face_location']
                cursor.execute("""
                    INSERT INTO face_detections (photo_id, person_id, x, y, width, height, confidence)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (face_data['photo_id'], person_id, left, top, right-left, bottom-top, 0.9))

            # Update person photo counts
            cursor.execute("""
                UPDATE persons SET photo_count = (
                    SELECT COUNT(DISTINCT fd.photo_id)
                    FROM face_detections fd
                    WHERE fd.person_id = persons.id
                )
            """)

        # Commit all changes
        conn.commit()
        logger.info(f"✅ Successfully processed and uploaded {len(photo_files)} photos with face clustering!")

        # Print summary
        cursor.execute("SELECT COUNT(*) FROM photos")
        photo_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM persons")
        person_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM face_detections")
        face_count = cursor.fetchone()[0]

        logger.info(f"📊 Final Summary:")
        logger.info(f"   Photos: {photo_count}")
        logger.info(f"   Persons: {person_count}")
        logger.info(f"   Face detections: {face_count}")

    except Exception as e:
        logger.error(f"❌ Error during processing: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function."""
    logger.info("🚀 Starting remote database processing...")

    try:
        # Test database connection
        conn = connect_to_db()
        conn.close()
        logger.info("✅ Database connection successful")

        # Ask user for confirmation
        print("\n⚠️  This will:")
        print("1. Clear all existing data in the production database")
        print("2. Process photos locally and upload results")
        print("3. Create face thumbnails as base64 data")

        confirm = input("\nProceed? (y/N): ").strip().lower()
        if confirm != 'y':
            logger.info("❌ Operation cancelled by user")
            return

        # Clear existing data
        clear_existing_data()

        # Process and upload photos
        process_photos()

        logger.info("🎉 Processing completed successfully!")
        logger.info("🔗 Check your frontend at the Vercel URL to see the results")

    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()