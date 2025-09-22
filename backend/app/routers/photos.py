"""API endpoints for photos management."""

import logging
import os
import zipfile
import tempfile
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_cache_service, CacheService, PaginationParams
from ..schemas import PhotosResponse, Photo, PhotoCreate, PhotoUpdate
from ..models import Photo as PhotoModel, FaceDetection
from ..db_utils import DatabaseManager
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/persons/{person_id}/photos", response_model=PhotosResponse)
async def get_photos_by_person(
    person_id: str,
    db: Session = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service),
    pagination: PaginationParams = Depends()
):
    """Get all photos containing a specific person.
    
    Args:
        person_id: Person identifier
        db: Database session
        cache: Cache service
        pagination: Pagination parameters
        
    Returns:
        List of photos containing the person
    """
    try:
        # Create cache key
        cache_key = f"person_photos:{person_id}:page:{pagination.page}:per_page:{pagination.per_page}"
        
        # Try cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached photos for person: {person_id}")
            return PhotosResponse.model_validate_json(cached_result)
        
        # Verify person exists
        person = DatabaseManager.get_person_by_id(db, person_id)
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        # Query photos
        photos = DatabaseManager.get_photos_by_person(
            db=db,
            person_id=person_id,
            limit=pagination.limit,
            offset=pagination.offset
        )
        
        # Get total count
        total_query = (
            db.query(PhotoModel)
            .join(FaceDetection)
            .filter(FaceDetection.person_id == person_id)
        )
        total = total_query.count()
        
        # Convert to response format and add person IDs
        photo_responses = []
        for photo in photos:
            # Get all persons in this photo
            person_ids = [
                fd.person_id for fd in photo.face_detections
            ]
            
            photo_dict = {
                "id": photo.id,
                "original_url": photo.original_url,
                "thumbnail_url": photo.thumbnail_url,
                "web_url": photo.web_url,
                "filename": photo.filename,
                "width": photo.width,
                "height": photo.height,
                "file_size": photo.file_size,
                "taken_at": photo.taken_at,
                "processed": photo.processed,
                "processing_error": photo.processing_error,
                "metadata": photo.photo_metadata or {},
                "created_at": photo.created_at,
                "updated_at": photo.updated_at,
                "persons": person_ids
            }
            photo_responses.append(Photo(**photo_dict))
        
        # Calculate pagination info
        has_next = (pagination.offset + pagination.limit) < total
        
        response = PhotosResponse(
            photos=photo_responses,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            has_next=has_next
        )
        
        # Cache the result
        cache.set(cache_key, response.model_dump_json(), ttl=settings.redis_cache_ttl)
        
        logger.info(f"Retrieved {len(photo_responses)} photos for person {person_id} (total: {total})")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving photos for person {person_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving photos"
        )


@router.get("/photos/{photo_id}", response_model=Photo)
async def get_photo(
    photo_id: str,
    db: Session = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
):
    """Get a specific photo by ID.
    
    Args:
        photo_id: Photo identifier
        db: Database session
        cache: Cache service
        
    Returns:
        Photo details
    """
    try:
        # Try cache first
        cache_key = f"photo:{photo_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached photo data for ID: {photo_id}")
            return Photo.model_validate_json(cached_result)
        
        # Query database
        photo = DatabaseManager.get_photo_by_id(db, photo_id)
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Photo with ID {photo_id} not found"
            )
        
        # Get all persons in this photo
        person_ids = [fd.person_id for fd in photo.face_detections]
        
        # Convert to response format
        photo_dict = {
            "id": photo.id,
            "original_url": photo.original_url,
            "thumbnail_url": photo.thumbnail_url,
            "web_url": photo.web_url,
            "filename": photo.filename,
            "width": photo.width,
            "height": photo.height,
            "file_size": photo.file_size,
            "taken_at": photo.taken_at,
            "processed": photo.processed,
            "processing_error": photo.processing_error,
            "metadata": photo.photo_metadata or {},
            "created_at": photo.created_at,
            "updated_at": photo.updated_at,
            "persons": person_ids
        }
        photo_response = Photo(**photo_dict)
        
        # Cache the result
        cache.set(cache_key, photo_response.model_dump_json(), ttl=settings.redis_cache_ttl)
        
        logger.info(f"Retrieved photo: {photo_id}")
        return photo_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving photo {photo_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving photo"
        )


@router.get("/photos/{photo_id}/download")
async def download_photo(
    photo_id: str,
    db: Session = Depends(get_db_session),
    quality: str = Query(default="original", regex="^(original|web|thumbnail)$")
):
    """Download a photo in specified quality.
    
    Args:
        photo_id: Photo identifier
        db: Database session
        quality: Photo quality (original, web, thumbnail)
        
    Returns:
        Photo file for download
    """
    try:
        # Get photo from database
        photo = DatabaseManager.get_photo_by_id(db, photo_id)
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Photo with ID {photo_id} not found"
            )
        
        # Determine file URL based on quality
        if quality == "original":
            file_url = photo.original_url
        elif quality == "web":
            file_url = photo.web_url
        else:  # thumbnail
            file_url = photo.thumbnail_url
        
        # Check if it's a local file or remote URL
        if file_url.startswith(('http://', 'https://')):
            # For remote URLs, redirect to the URL
            return Response(
                status_code=status.HTTP_302_FOUND,
                headers={"Location": file_url}
            )
        else:
            # For local files, serve directly
            if not os.path.exists(file_url):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Photo file not found on server"
                )
            
            # Determine filename for download
            filename = f"{photo.filename.split('.')[0]}_{quality}.jpg"
            
            return FileResponse(
                path=file_url,
                filename=filename,
                media_type="image/jpeg"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading photo {photo_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error downloading photo"
        )


@router.get("/persons/{person_id}/download")
async def download_person_photos(
    person_id: str,
    db: Session = Depends(get_db_session),
    quality: str = Query(default="web", regex="^(original|web|thumbnail)$")
):
    """Download all photos of a person as a ZIP file.

    Args:
        person_id: Person identifier
        db: Database session
        quality: Photo quality (original, web, thumbnail)

    Returns:
        ZIP file containing all photos of the person
    """
    try:
        # Verify person exists
        from ..db_utils import DatabaseManager
        person = DatabaseManager.get_person_by_id(db, person_id)
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )

        # Get all photos for this person
        photos = DatabaseManager.get_photos_by_person(
            db=db,
            person_id=person_id,
            limit=1000,  # Limit to reasonable number
            offset=0
        )

        if not photos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No photos found for this person"
            )

        # Create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for photo in photos:
                try:
                    # Determine file path based on quality
                    if quality == "original":
                        file_url = photo.original_url
                        folder_prefix = "original"
                    elif quality == "web":
                        file_url = photo.web_url
                        folder_prefix = "web"
                    else:  # thumbnail
                        file_url = photo.thumbnail_url
                        folder_prefix = "thumbnail"

                    # Convert URL to local file path
                    if file_url.startswith('http://localhost:8000/static/'):
                        file_path = file_url.replace('http://localhost:8000/static/', '/app/static/')

                        if os.path.exists(file_path):
                            # Add file to ZIP with quality prefix
                            zip_filename = f"{folder_prefix}/{photo.filename}"
                            zip_file.write(file_path, zip_filename)
                        else:
                            logger.warning(f"File not found: {file_path}")

                except Exception as e:
                    logger.warning(f"Could not add photo {photo.filename} to ZIP: {e}")
                    continue

        zip_buffer.seek(0)

        # Generate filename
        zip_filename = f"person_{person_id[:8]}_photos_{quality}.zip"

        # Return ZIP file
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ZIP for person {person_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating photo archive"
        )


@router.post("/photos", response_model=Photo, status_code=status.HTTP_201_CREATED)
async def create_photo(
    photo_data: PhotoCreate,
    db: Session = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
):
    """Create a new photo record.
    
    Args:
        photo_data: Photo creation data
        db: Database session
        cache: Cache service
        
    Returns:
        Created photo
    """
    try:
        # Create photo in database
        photo = DatabaseManager.create_photo(
            db=db,
            original_url=photo_data.original_url,
            thumbnail_url=photo_data.thumbnail_url,
            web_url=photo_data.web_url,
            filename=photo_data.filename,
            width=photo_data.width,
            height=photo_data.height,
            file_size=photo_data.file_size,
            taken_at=photo_data.taken_at,
            photo_metadata=photo_data.metadata
        )
        
        # Invalidate related caches
        _invalidate_photos_cache(cache)
        
        # Convert to response format
        photo_dict = {
            "id": photo.id,
            "original_url": photo.original_url,
            "thumbnail_url": photo.thumbnail_url,
            "web_url": photo.web_url,
            "filename": photo.filename,
            "width": photo.width,
            "height": photo.height,
            "file_size": photo.file_size,
            "taken_at": photo.taken_at,
            "processed": photo.processed,
            "processing_error": photo.processing_error,
            "metadata": photo.photo_metadata or {},
            "created_at": photo.created_at,
            "updated_at": photo.updated_at,
            "persons": []  # No persons initially
        }
        
        logger.info(f"Created photo: {photo.id}")
        return Photo(**photo_dict)
        
    except Exception as e:
        logger.error(f"Error creating photo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating photo"
        )


@router.put("/photos/{photo_id}", response_model=Photo)
async def update_photo(
    photo_id: str,
    photo_data: PhotoUpdate,
    db: Session = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
):
    """Update a photo.
    
    Args:
        photo_id: Photo identifier
        photo_data: Photo update data
        db: Database session
        cache: Cache service
        
    Returns:
        Updated photo
    """
    try:
        # Get existing photo
        photo = DatabaseManager.get_photo_by_id(db, photo_id)
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Photo with ID {photo_id} not found"
            )
        
        # Update fields
        update_data = photo_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(photo, field, value)
        
        db.commit()
        db.refresh(photo)
        
        # Invalidate cache
        cache.delete(f"photo:{photo_id}")
        _invalidate_photos_cache(cache)
        
        # Get persons for response
        person_ids = [fd.person_id for fd in photo.face_detections]
        
        # Convert to response format
        photo_dict = {
            "id": photo.id,
            "original_url": photo.original_url,
            "thumbnail_url": photo.thumbnail_url,
            "web_url": photo.web_url,
            "filename": photo.filename,
            "width": photo.width,
            "height": photo.height,
            "file_size": photo.file_size,
            "taken_at": photo.taken_at,
            "processed": photo.processed,
            "processing_error": photo.processing_error,
            "metadata": photo.photo_metadata or {},
            "created_at": photo.created_at,
            "updated_at": photo.updated_at,
            "persons": person_ids
        }
        
        logger.info(f"Updated photo: {photo_id}")
        return Photo(**photo_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating photo {photo_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating photo"
        )


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    photo_id: str,
    db: Session = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
):
    """Delete a photo.
    
    Args:
        photo_id: Photo identifier
        db: Database session
        cache: Cache service
    """
    try:
        # Get existing photo
        photo = DatabaseManager.get_photo_by_id(db, photo_id)
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Photo with ID {photo_id} not found"
            )
        
        # Delete photo (cascade will handle face detections)
        db.delete(photo)
        db.commit()
        
        # Invalidate cache
        cache.delete(f"photo:{photo_id}")
        _invalidate_photos_cache(cache)
        
        logger.info(f"Deleted photo: {photo_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting photo {photo_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting photo"
        )


@router.get("/photos/download")
async def download_all_photos(
    db: Session = Depends(get_db_session),
    quality: str = Query(default="web", regex="^(original|web|thumbnail)$"),
    has_faces: Optional[bool] = Query(default=None, description="Filter by whether photos have faces")
):
    """Download all photos as a ZIP file.

    Args:
        db: Database session
        quality: Photo quality (original, web, thumbnail)
        has_faces: Filter by whether photos have faces

    Returns:
        ZIP file containing all photos
    """
    try:
        # Build base query
        base_query = db.query(PhotoModel).filter(PhotoModel.processed == True)

        # Apply face filtering
        if has_faces is not None:
            if has_faces:
                # Photos with faces
                face_subquery = db.query(FaceDetection.photo_id).filter(FaceDetection.photo_id == PhotoModel.id)
                query = base_query.filter(face_subquery.exists())
            else:
                # Photos without faces
                face_subquery = db.query(FaceDetection.photo_id).filter(FaceDetection.photo_id == PhotoModel.id)
                query = base_query.filter(~face_subquery.exists())
        else:
            query = base_query

        # Get all photos (limit to reasonable number for memory)
        photos = query.order_by(PhotoModel.created_at.desc()).limit(2000).all()

        if not photos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No photos found"
            )

        # Create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for photo in photos:
                try:
                    # Determine file path based on quality
                    if quality == "original":
                        file_url = photo.original_url
                        folder_prefix = "original"
                    elif quality == "web":
                        file_url = photo.web_url
                        folder_prefix = "web"
                    else:  # thumbnail
                        file_url = photo.thumbnail_url
                        folder_prefix = "thumbnail"

                    # Convert URL to local file path
                    if file_url.startswith('http://localhost:8000/static/'):
                        file_path = file_url.replace('http://localhost:8000/static/', '/app/static/')

                        if os.path.exists(file_path):
                            # Add file to ZIP with quality prefix
                            zip_filename = f"{folder_prefix}/{photo.filename}"
                            zip_file.write(file_path, zip_filename)
                        else:
                            logger.warning(f"File not found: {file_path}")

                except Exception as e:
                    logger.warning(f"Could not add photo {photo.filename} to ZIP: {e}")
                    continue

        zip_buffer.seek(0)

        # Generate filename with face filter info
        filter_suffix = ""
        if has_faces is True:
            filter_suffix = "_with_faces"
        elif has_faces is False:
            filter_suffix = "_no_faces"

        zip_filename = f"all_photos{filter_suffix}_{quality}.zip"

        # Return ZIP file
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ZIP for all photos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating photo archive"
        )


@router.get("/photos", response_model=PhotosResponse)
async def get_all_photos(
    db: Session = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service),
    pagination: PaginationParams = Depends(),
    processed_only: bool = Query(default=True, description="Only return processed photos"),
    has_faces: Optional[bool] = Query(default=None, description="Filter by whether photos have faces")
):
    """Get all photos.
    
    Args:
        db: Database session
        cache: Cache service
        pagination: Pagination parameters
        processed_only: Whether to return only processed photos
        
    Returns:
        List of photos
    """
    try:
        # Create cache key
        cache_key = f"photos:page:{pagination.page}:per_page:{pagination.per_page}:processed:{processed_only}:has_faces:{has_faces}"
        
        # Try cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached photos data")
            return PhotosResponse.model_validate_json(cached_result)
        
        # Build base query
        base_query = db.query(PhotoModel)
        if processed_only:
            base_query = base_query.filter(PhotoModel.processed == True)
        
        # Apply face filtering
        if has_faces is not None:
            if has_faces:
                # Photos with faces - use EXISTS subquery for better performance
                face_subquery = db.query(FaceDetection.photo_id).filter(FaceDetection.photo_id == PhotoModel.id)
                query = base_query.filter(face_subquery.exists())
            else:
                # Photos without faces - use NOT EXISTS
                face_subquery = db.query(FaceDetection.photo_id).filter(FaceDetection.photo_id == PhotoModel.id)
                query = base_query.filter(~face_subquery.exists())
        else:
            query = base_query
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        photos = (
            query
            .order_by(PhotoModel.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )
        
        # Convert to response format
        photo_responses = []
        for photo in photos:
            person_ids = [fd.person_id for fd in photo.face_detections]
            
            photo_dict = {
                "id": photo.id,
                "original_url": photo.original_url,
                "thumbnail_url": photo.thumbnail_url,
                "web_url": photo.web_url,
                "filename": photo.filename,
                "width": photo.width,
                "height": photo.height,
                "file_size": photo.file_size,
                "taken_at": photo.taken_at,
                "processed": photo.processed,
                "processing_error": photo.processing_error,
                "metadata": photo.photo_metadata or {},
                "created_at": photo.created_at,
                "updated_at": photo.updated_at,
                "persons": person_ids
            }
            photo_responses.append(Photo(**photo_dict))
        
        # Calculate pagination info
        has_next = (pagination.offset + pagination.limit) < total
        
        response = PhotosResponse(
            photos=photo_responses,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            has_next=has_next
        )
        
        # Cache the result
        cache.set(cache_key, response.model_dump_json(), ttl=settings.redis_cache_ttl)
        
        logger.info(f"Retrieved {len(photo_responses)} photos (total: {total})")
        return response
        
    except Exception as e:
        logger.error(f"Error retrieving photos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving photos"
        )


def _invalidate_photos_cache(cache: CacheService) -> None:
    """Invalidate photos cache entries.
    
    Args:
        cache: Cache service
    """
    try:
        # Clear common cache patterns
        for page in range(1, 11):  # Clear first 10 pages
            for per_page in [10, 20, 50]:
                for processed in [True, False]:
                    cache_key = f"photos:page:{page}:per_page:{per_page}:processed:{processed}"
                    cache.delete(cache_key)
        
        logger.debug("Invalidated photos cache entries")
        
    except Exception as e:
        logger.error(f"Error invalidating photos cache: {e}")
