#!/usr/bin/env python3
"""
Simple script to upload photo metadata directly to production database.
This creates photo records without face processing for now.
"""

import os
import sys
import logging
import psycopg2
from pathlib import Path
from PIL import Image
from datetime import datetime
import io
import base64

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

def create_image_thumbnail_base64(image_path, max_size=(300, 300)):
    """Create a thumbnail and return as base64."""
    try:
        with Image.open(image_path) as img:
            # Create thumbnail
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        logger.error(f"Error creating thumbnail for {image_path}: {e}")
        return None

def upload_photos():
    """Upload photo metadata to database."""
    uploads_dir = Path("backend/uploads_sample")

    if not uploads_dir.exists():
        logger.error(f"Uploads directory not found: {uploads_dir}")
        return

    # Get photo files
    photo_files = list(uploads_dir.glob("*.jpg")) + list(uploads_dir.glob("*.JPG"))
    logger.info(f"Found {len(photo_files)} photos to upload")

    if not photo_files:
        logger.error("No photo files found!")
        return

    # Connect to database
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        uploaded_count = 0

        for photo_path in photo_files:
            logger.info(f"Processing {photo_path.name}...")

            try:
                # Get image info
                with Image.open(photo_path) as img:
                    width, height = img.size
                    file_size = photo_path.stat().st_size

                # Create thumbnails as base64 (since we can't host files on Render free tier)
                thumbnail_b64 = create_image_thumbnail_base64(photo_path, (300, 300))
                web_b64 = create_image_thumbnail_base64(photo_path, (1200, 1200))

                # For now, use placeholder URLs or base64 data
                original_url = f"/static/original/{photo_path.name}"
                web_url = web_b64 or f"/static/web/{photo_path.name}"
                thumbnail_url = thumbnail_b64 or f"/static/thumbnails/{photo_path.name}"

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
                uploaded_count += 1
                logger.info(f"✅ Added photo to DB with ID: {photo_id}")

            except Exception as e:
                logger.error(f"❌ Error processing {photo_path.name}: {e}")
                continue

        # Create some sample persons (since we can't do face processing without face_recognition)
        logger.info("Creating sample persons...")

        # Get first few photos to use as person thumbnails
        cursor.execute("SELECT id, thumbnail_url FROM photos LIMIT 3")
        sample_photos = cursor.fetchall()

        for i, (photo_id, thumbnail_url) in enumerate(sample_photos):
            cursor.execute("""
                INSERT INTO persons (name, thumbnail_url, photo_count, cluster_confidence)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (f"Person {i+1}", thumbnail_url, 1, 0.8))

            person_id = cursor.fetchone()[0]
            logger.info(f"✅ Created Person {i+1} with ID: {person_id}")

            # Create a sample face detection for this person/photo
            cursor.execute("""
                INSERT INTO face_detections (photo_id, person_id, x, y, width, height, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (photo_id, person_id, 100, 100, 200, 200, 0.9))

        # Commit all changes
        conn.commit()
        logger.info(f"✅ Successfully uploaded {uploaded_count} photos!")

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
        logger.error(f"❌ Error during upload: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function."""
    logger.info("🚀 Starting simple photo upload...")

    try:
        # Test database connection
        conn = connect_to_db()
        conn.close()
        logger.info("✅ Database connection successful")

        # Ask user for confirmation
        print("\n⚠️  This will:")
        print("1. Clear all existing data in the production database")
        print("2. Upload photo metadata with base64 thumbnails")
        print("3. Create sample person records (no real face detection)")

        confirm = input("\nProceed? (y/N): ").strip().lower()
        if confirm != 'y':
            logger.info("❌ Operation cancelled by user")
            return

        # Clear existing data
        clear_existing_data()

        # Upload photos
        upload_photos()

        logger.info("🎉 Upload completed successfully!")
        logger.info("🔗 Check your frontend to see the results")

    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()