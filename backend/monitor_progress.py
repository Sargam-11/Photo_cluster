#!/usr/bin/env python3
"""
Monitor processing progress and estimate completion time.
"""

import time
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import Photo

def monitor_progress():
    """Monitor processing progress and show estimates."""

    start_time = datetime.now()
    total_photos = 481  # Known total

    print(f"🔍 Starting progress monitor at {start_time.strftime('%H:%M:%S')}")
    print(f"📊 Total photos to process: {total_photos}")
    print("-" * 60)

    previous_count = 0
    check_interval = 30  # Check every 30 seconds

    while True:
        db = SessionLocal()
        try:
            # Count processed photos
            current_count = db.query(Photo).count()

            # Calculate progress
            progress_percent = (current_count / total_photos) * 100
            photos_processed_since_last = current_count - previous_count

            # Calculate rate (photos per minute)
            elapsed_time = datetime.now() - start_time
            if elapsed_time.total_seconds() > 0:
                photos_per_minute = (current_count / elapsed_time.total_seconds()) * 60

                # Estimate remaining time
                if photos_per_minute > 0:
                    remaining_photos = total_photos - current_count
                    remaining_minutes = remaining_photos / photos_per_minute
                    estimated_completion = datetime.now() + timedelta(minutes=remaining_minutes)
                else:
                    remaining_minutes = float('inf')
                    estimated_completion = "Unknown"
            else:
                photos_per_minute = 0
                remaining_minutes = float('inf')
                estimated_completion = "Calculating..."

            # Print status
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"⏰ {current_time} | Photos: {current_count:3d}/{total_photos} ({progress_percent:5.1f}%)")
            print(f"📈 Rate: {photos_per_minute:.1f} photos/min | New: +{photos_processed_since_last}")

            if remaining_minutes != float('inf'):
                print(f"⏱️  Est. completion: {estimated_completion.strftime('%H:%M:%S')} ({remaining_minutes:.0f} min remaining)")
            else:
                print("⏱️  Est. completion: Calculating...")

            print("-" * 60)

            # Check if completed
            if current_count >= total_photos:
                print("🎉 Processing completed!")
                break

            previous_count = current_count

        except Exception as e:
            print(f"❌ Error checking progress: {e}")
        finally:
            db.close()

        time.sleep(check_interval)

if __name__ == "__main__":
    try:
        monitor_progress()
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")