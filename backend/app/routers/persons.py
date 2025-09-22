"""API endpoints for persons management."""

import logging
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_cache_service, CacheService, PaginationParams
from ..schemas import PersonsResponse, PersonThumbnail, Person, PersonCreate, PersonUpdate
from ..models import Person as PersonModel
from ..db_utils import DatabaseManager
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/persons", response_model=PersonsResponse)
async def get_all_persons(
    db: Session = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service),
    pagination: PaginationParams = Depends(),
    min_photos: int = Query(default=1, ge=1, description="Minimum number of photos per person")
):
    """Get all persons with their thumbnails.
    
    Args:
        db: Database session
        cache: Cache service
        pagination: Pagination parameters
        min_photos: Minimum number of photos to include person
        
    Returns:
        List of persons with thumbnails
    """
    try:
        # Create cache key
        cache_key = f"persons:page:{pagination.page}:per_page:{pagination.per_page}:min_photos:{min_photos}"
        
        # Try to get from cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached persons data for key: {cache_key}")
            return PersonsResponse.model_validate_json(cached_result)
        
        # Query database
        query = db.query(PersonModel).filter(PersonModel.photo_count >= min_photos)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        persons = (
            query
            .order_by(PersonModel.photo_count.desc(), PersonModel.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )
        
        # Convert to response format
        person_thumbnails = [
            PersonThumbnail(
                id=person.id,
                thumbnail_url=person.thumbnail_url,
                photo_count=person.photo_count,
                cluster_confidence=person.cluster_confidence
            )
            for person in persons
        ]
        
        response = PersonsResponse(
            persons=person_thumbnails,
            total=total
        )
        
        # Cache the result
        cache.set(cache_key, response.model_dump_json(), ttl=settings.redis_cache_ttl)
        
        logger.info(f"Retrieved {len(person_thumbnails)} persons (total: {total})")
        return response
        
    except Exception as e:
        logger.error(f"Error retrieving persons: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving persons"
        )


@router.get("/persons/{person_id}", response_model=Person)
async def get_person(
    person_id: str,
    db: Session = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
):
    """Get a specific person by ID.
    
    Args:
        person_id: Person identifier
        db: Database session
        cache: Cache service
        
    Returns:
        Person details
    """
    try:
        # Try cache first
        cache_key = f"person:{person_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached person data for ID: {person_id}")
            return Person.model_validate_json(cached_result)
        
        # Query database
        person = DatabaseManager.get_person_by_id(db, person_id)
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        # Convert to response format
        person_response = Person.model_validate(person)
        
        # Cache the result
        cache.set(cache_key, person_response.model_dump_json(), ttl=settings.redis_cache_ttl)
        
        logger.info(f"Retrieved person: {person_id}")
        return person_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving person {person_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving person"
        )


@router.post("/persons", response_model=Person, status_code=status.HTTP_201_CREATED)
async def create_person(
    person_data: PersonCreate,
    db: Session = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
):
    """Create a new person.
    
    Args:
        person_data: Person creation data
        db: Database session
        cache: Cache service
        
    Returns:
        Created person
    """
    try:
        # Create person in database
        person = DatabaseManager.create_person(
            db=db,
            thumbnail_url=person_data.thumbnail_url,
            face_embedding=person_data.face_embedding,
            cluster_confidence=person_data.cluster_confidence
        )
        
        # Invalidate persons list cache
        _invalidate_persons_cache(cache)
        
        logger.info(f"Created person: {person.id}")
        return Person.model_validate(person)
        
    except Exception as e:
        logger.error(f"Error creating person: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating person"
        )


@router.put("/persons/{person_id}", response_model=Person)
async def update_person(
    person_id: str,
    person_data: PersonUpdate,
    db: Session = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
):
    """Update a person.
    
    Args:
        person_id: Person identifier
        person_data: Person update data
        db: Database session
        cache: Cache service
        
    Returns:
        Updated person
    """
    try:
        # Get existing person
        person = DatabaseManager.get_person_by_id(db, person_id)
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        # Update fields
        update_data = person_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(person, field, value)
        
        db.commit()
        db.refresh(person)
        
        # Invalidate cache
        cache.delete(f"person:{person_id}")
        _invalidate_persons_cache(cache)
        
        logger.info(f"Updated person: {person_id}")
        return Person.model_validate(person)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating person {person_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating person"
        )


@router.delete("/persons/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: str,
    db: Session = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
):
    """Delete a person.
    
    Args:
        person_id: Person identifier
        db: Database session
        cache: Cache service
    """
    try:
        # Get existing person
        person = DatabaseManager.get_person_by_id(db, person_id)
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        # Delete person (cascade will handle face detections)
        db.delete(person)
        db.commit()
        
        # Invalidate cache
        cache.delete(f"person:{person_id}")
        _invalidate_persons_cache(cache)
        
        logger.info(f"Deleted person: {person_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting person {person_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting person"
        )


@router.post("/persons/{person_id}/update-photo-count")
async def update_person_photo_count(
    person_id: str,
    db: Session = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
):
    """Update photo count for a person.
    
    Args:
        person_id: Person identifier
        db: Database session
        cache: Cache service
        
    Returns:
        Success message
    """
    try:
        # Update photo count
        DatabaseManager.update_person_photo_count(db, person_id)
        
        # Invalidate cache
        cache.delete(f"person:{person_id}")
        _invalidate_persons_cache(cache)
        
        logger.info(f"Updated photo count for person: {person_id}")
        return {"message": "Photo count updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating photo count for person {person_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating photo count"
        )


@router.get("/persons/search")
async def search_persons(
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db_session),
    pagination: PaginationParams = Depends()
):
    """Search persons (placeholder for future implementation).
    
    Args:
        q: Search query
        db: Database session
        pagination: Pagination parameters
        
    Returns:
        Search results
    """
    # This is a placeholder for future search functionality
    # Could search by metadata, tags, or other attributes
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Search functionality not yet implemented"
    )


def _invalidate_persons_cache(cache: CacheService) -> None:
    """Invalidate persons list cache entries.
    
    Args:
        cache: Cache service
    """
    try:
        # In a real implementation, you might want to use Redis SCAN
        # to find and delete all keys matching a pattern
        # For now, we'll just delete some common cache keys
        
        for page in range(1, 11):  # Clear first 10 pages
            for per_page in [10, 20, 50]:
                for min_photos in [1, 2, 5]:
                    cache_key = f"persons:page:{page}:per_page:{per_page}:min_photos:{min_photos}"
                    cache.delete(cache_key)
        
        logger.debug("Invalidated persons cache entries")
        
    except Exception as e:
        logger.error(f"Error invalidating persons cache: {e}")