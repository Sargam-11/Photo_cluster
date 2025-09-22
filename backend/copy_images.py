#!/usr/bin/env python3
"""
Simple script to copy images to static directories and create thumbnails.
"""

import os
import shutil
from pathlib import Path
from PIL import Image

def copy_and_resize_images():
    """Copy images to static directories and create thumbnails."""
    
    uploads_dir = Path("/app/uploads")
    static_dir = Path("/app/static")
    
    # Create directories
    (static_dir / "original").mkdir(parents=True, exist_ok=True)
    (static_dir / "thumbnails").mkdir(parents=True, exist_ok=True)
    (static_dir / "web").mkdir(parents=True, exist_ok=True)
    
    # Get first 20 photos
    photo_files = list(uploads_dir.glob("*.JPG"))[:20]
    
    for photo_path in photo_files:
        print(f"Processing {photo_path.name}")
        
        # Copy original
        original_dest = static_dir / "original" / photo_path.name
        shutil.copy2(photo_path, original_dest)
        
        # Create thumbnail (300x300)
        try:
            with Image.open(photo_path) as img:
                # Create thumbnail
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                thumbnail_dest = static_dir / "thumbnails" / photo_path.name
                img.save(thumbnail_dest, "JPEG", quality=85)
                
                # Create web version (1200px max)
                with Image.open(photo_path) as img_web:
                    img_web.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                    web_dest = static_dir / "web" / photo_path.name
                    img_web.save(web_dest, "JPEG", quality=85)
                    
        except Exception as e:
            print(f"Error processing {photo_path.name}: {e}")
    
    print(f"Processed {len(photo_files)} images")

if __name__ == "__main__":
    copy_and_resize_images()