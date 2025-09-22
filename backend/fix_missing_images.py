#!/usr/bin/env python3
"""
Fix missing optimized images for existing database records.
"""

import os
import shutil
from pathlib import Path
import logging
from PIL import Image
from app.database import SessionLocal
from app.models import Photo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def copy_and_optimize_missing_images():
    """Copy and optimize missing image files for existing database records."""

    # Get database session
    db = SessionLocal()

    try:
        # Get all photos from database
        photos = db.query(Photo).all()
        logger.info(f"Found {len(photos)} photos in database")

        # Create static directories
        static_dir = Path("/app/static")
        original_dir = static_dir / "original"
        web_dir = static_dir / "web"
        thumbnail_dir = static_dir / "thumbnails"

        original_dir.mkdir(parents=True, exist_ok=True)
        web_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_dir.mkdir(parents=True, exist_ok=True)

        uploads_dir = Path("/app/uploads")

        processed_count = 0

        for photo in photos:
            filename = photo.filename
            source_path = uploads_dir / filename

            if not source_path.exists():
                logger.warning(f"Source file not found: {source_path}")
                continue

            # Check if optimized files already exist
            original_dest = original_dir / filename
            web_dest = web_dir / filename
            thumbnail_dest = thumbnail_dir / filename

            files_created = 0

            # Copy original if not exists
            if not original_dest.exists():
                shutil.copy2(source_path, original_dest)
                logger.info(f"Copied original: {filename}")
                files_created += 1

            # Create web version if not exists
            if not web_dest.exists():
                try:
                    with Image.open(source_path) as img:
                        img_web = img.copy()
                        img_web.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                        img_web.save(web_dest, "JPEG", quality=85)
                        logger.info(f"Created web version: {filename}")
                        files_created += 1
                except Exception as e:
                    logger.error(f"Error creating web version for {filename}: {e}")

            # Create thumbnail if not exists
            if not thumbnail_dest.exists():
                try:
                    with Image.open(source_path) as img:
                        img_thumb = img.copy()
                        img_thumb.thumbnail((300, 300), Image.Resampling.LANCZOS)
                        img_thumb.save(thumbnail_dest, "JPEG", quality=85)
                        logger.info(f"Created thumbnail: {filename}")
                        files_created += 1
                except Exception as e:
                    logger.error(f"Error creating thumbnail for {filename}: {e}")

            if files_created > 0:
                processed_count += 1

        logger.info(f"Processed {processed_count} photos, created missing optimized images")

    except Exception as e:
        logger.error(f"Error processing images: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    copy_and_optimize_missing_images()