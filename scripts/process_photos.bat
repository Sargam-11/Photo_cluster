@echo off
echo Processing photos with face recognition...
echo.

REM Check if uploads directory exists
if not exist "uploads" (
    echo Creating uploads directory...
    mkdir uploads
    echo.
    echo Please copy your event photos to the 'uploads' folder first!
    echo Example: copy "C:\path\to\your\photos\*.jpg" uploads\
    echo.
    pause
    exit /b 1
)

REM Count photos in uploads
for /f %%i in ('dir /b uploads\*.jpg uploads\*.jpeg uploads\*.png 2^>nul ^| find /c /v ""') do set photo_count=%%i

if %photo_count%==0 (
    echo No photos found in uploads directory!
    echo Please copy your event photos to the 'uploads' folder first.
    echo.
    pause
    exit /b 1
)

echo Found %photo_count% photos to process
echo.

REM Run processing in the backend container
echo Starting face recognition processing...
docker-compose exec -T backend python -c "
import sys, os
sys.path.append('/app')
sys.path.append('/app/../processing')
os.chdir('/app')

from processing.services.batch_processor import BatchProcessor
from processing.services.face_detection import FaceDetectionService
from processing.services.face_clustering import FaceClusteringService
from processing.services.image_optimization import ImageOptimizationService

print('Initializing face recognition system...')
processor = BatchProcessor(
    face_detection_model='hog',
    clustering_eps=0.6,
    clustering_min_samples=2,
    output_dir='./processed',
    max_workers=4
)

print('Processing photos...')
results = processor.process_with_progress_bar('uploads')

if results.get('success'):
    print(f'Processing completed successfully!')
    print(f'Total images: {results[\"total_images\"]}')
    print(f'Successful: {results[\"successful_images\"]}')
    print(f'Failed: {results[\"failed_images\"]}')
    print(f'Total faces detected: {results[\"total_faces_detected\"]}')
    if results.get('clustering', {}).get('success'):
        clustering = results['clustering']
        print(f'Persons identified: {len(clustering.get(\"clusters\", {}))}')
    print('Your gallery is ready at http://localhost:3000')
else:
    print(f'Processing failed: {results.get(\"error\", \"Unknown error\")}')
"

echo.
echo Processing complete! 
echo Open http://localhost:3000 to view your gallery
echo.
pause