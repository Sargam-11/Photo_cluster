#!/usr/bin/env python3
"""
Upload photos to production Render backend.
"""

import os
import requests
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Production API URL
API_BASE_URL = "https://photo-gallery-backend-z2v3.onrender.com"

def check_backend_health():
    """Check if backend is healthy."""
    try:
        logger.info("🔄 Checking backend health (may take 30+ seconds if sleeping)...")
        response = requests.get(f"{API_BASE_URL}/health", timeout=60)
        if response.status_code == 200:
            logger.info("✅ Backend is healthy")
            logger.info(f"Response: {response.json()}")
            return True
        else:
            logger.error(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Cannot reach backend: {e}")
        return False

def upload_photo(photo_path):
    """Upload a single photo."""
    try:
        with open(photo_path, 'rb') as f:
            files = {'file': (photo_path.name, f, 'image/jpeg')}
            response = requests.post(
                f"{API_BASE_URL}/api/photos/upload",
                files=files,
                timeout=120
            )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Uploaded {photo_path.name}")
            return result
        elif response.status_code == 422:
            logger.warning(f"⚠️  {photo_path.name} might already exist or validation failed")
            return None
        else:
            logger.error(f"❌ Failed to upload {photo_path.name}: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Error uploading {photo_path.name}: {e}")
        return None

def get_current_photos():
    """Get current photos from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/photos", timeout=30)
        if response.status_code == 200:
            photos = response.json()
            logger.info(f"📊 Current photos in database: {len(photos)}")
            return photos
        else:
            logger.error(f"❌ Failed to get photos: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"❌ Error getting photos: {e}")
        return []

def get_current_persons():
    """Get current persons from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/persons", timeout=30)
        if response.status_code == 200:
            persons = response.json()
            logger.info(f"📊 Current persons in database: {len(persons)}")
            return persons
        else:
            logger.error(f"❌ Failed to get persons: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"❌ Error getting persons: {e}")
        return []

def trigger_face_processing():
    """Trigger face processing on uploaded photos."""
    try:
        logger.info("🔄 Starting face processing...")
        response = requests.post(
            f"{API_BASE_URL}/api/photos/process-all",
            timeout=600  # 10 minute timeout for processing
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Face processing completed!")
            logger.info(f"Result: {result}")
            return True
        else:
            logger.error(f"❌ Face processing failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error during face processing: {e}")
        return False

def main():
    """Main function."""
    logger.info("🚀 Starting photo upload to Render...")

    # Check backend health
    if not check_backend_health():
        logger.error("❌ Backend is not healthy. Exiting.")
        return

    # Find photos to upload
    uploads_dir = Path("backend/uploads_sample")
    if not uploads_dir.exists():
        logger.error(f"❌ Uploads directory not found: {uploads_dir}")
        return

    photo_files = list(uploads_dir.glob("*.JPG")) + list(uploads_dir.glob("*.jpg"))
    logger.info(f"📁 Found {len(photo_files)} photos to upload")

    if not photo_files:
        logger.error("❌ No photos found!")
        return

    # Check current state
    current_photos = get_current_photos()
    current_persons = get_current_persons()

    # Upload photos
    uploaded_count = 0
    for photo_path in photo_files:
        logger.info(f"📤 Uploading {photo_path.name}...")
        result = upload_photo(photo_path)
        if result:
            uploaded_count += 1

    logger.info(f"📊 Successfully uploaded {uploaded_count}/{len(photo_files)} photos")

    # Trigger processing if we uploaded photos
    if uploaded_count > 0:
        logger.info("🔄 Triggering face processing...")
        if trigger_face_processing():
            logger.info("✅ Face processing completed!")
        else:
            logger.warning("⚠️  Face processing may have failed - check manually")
    else:
        logger.info("ℹ️  No new photos uploaded, skipping processing")

    # Final status
    final_photos = get_current_photos()
    final_persons = get_current_persons()

    logger.info("🎉 Upload process completed!")
    logger.info(f"📊 Final Summary:")
    logger.info(f"   Photos: {len(final_photos)} (was {len(current_photos)})")
    logger.info(f"   Persons: {len(final_persons)} (was {len(current_persons)})")
    logger.info(f"   Frontend: https://your-vercel-app.vercel.app")

    logger.info("🔗 Next steps:")
    logger.info("   1. Check your Vercel frontend to see the photos")
    logger.info("   2. Test face recognition by clicking on person cards")
    logger.info("   3. Share the link with your event attendees!")

if __name__ == "__main__":
    main()