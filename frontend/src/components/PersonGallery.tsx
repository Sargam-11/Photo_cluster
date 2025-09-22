import React, { useState, useCallback, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { usePhotosByPerson, usePerson } from '../hooks/useApi';
import { Photo } from '../types';
import { PageLoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';
import { PhotoViewer } from './PhotoViewer';
import { PhotoGrid } from './PhotoGrid';

export function PersonGallery() {
  const { personId } = useParams<{ personId: string }>();
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const perPage = 24;

  // Fetch person details and photos
  const { data: person, loading: personLoading, error: personError } = usePerson(personId || null);
  const { 
    data: photosResponse, 
    loading: photosLoading, 
    error: photosError, 
    refetch: refetchPhotos 
  } = usePhotosByPerson(personId || null, currentPage, perPage);

  const loading = personLoading || photosLoading;
  const error = personError || photosError;

  // Handle photo selection
  const handlePhotoClick = useCallback((photo: Photo) => {
    setSelectedPhoto(photo);
  }, []);

  const handleCloseViewer = useCallback(() => {
    setSelectedPhoto(null);
  }, []);

  // Handle pagination
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  // Navigation in photo viewer
  const handleNextPhoto = useCallback(() => {
    if (!selectedPhoto || !photosResponse?.photos) return;
    
    const currentIndex = photosResponse.photos.findIndex(p => p.id === selectedPhoto.id);
    const nextIndex = (currentIndex + 1) % photosResponse.photos.length;
    setSelectedPhoto(photosResponse.photos[nextIndex]);
  }, [selectedPhoto, photosResponse?.photos]);

  const handlePrevPhoto = useCallback(() => {
    if (!selectedPhoto || !photosResponse?.photos) return;
    
    const currentIndex = photosResponse.photos.findIndex(p => p.id === selectedPhoto.id);
    const prevIndex = currentIndex === 0 ? photosResponse.photos.length - 1 : currentIndex - 1;
    setSelectedPhoto(photosResponse.photos[prevIndex]);
  }, [selectedPhoto, photosResponse?.photos]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (!selectedPhoto) return;
      
      switch (event.key) {
        case 'Escape':
          handleCloseViewer();
          break;
        case 'ArrowLeft':
          handlePrevPhoto();
          break;
        case 'ArrowRight':
          handleNextPhoto();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedPhoto, handleCloseViewer, handlePrevPhoto, handleNextPhoto]);

  if (loading) {
    return <PageLoadingSpinner text="Loading photos..." />;
  }

  if (error) {
    return (
      <ErrorMessage 
        message={error} 
        onRetry={refetchPhotos}
        title="Failed to load photos"
      />
    );
  }

  if (!person) {
    return (
      <ErrorMessage 
        message="Person not found. They may have been removed or the link is invalid."
        title="Person Not Found"
      />
    );
  }

  const photos = photosResponse?.photos || [];
  const totalPhotos = photosResponse?.total || 0;
  const hasNextPage = photosResponse?.has_next || false;
  const totalPages = Math.ceil(totalPhotos / perPage);

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-4 mb-4">
          <Link
            to="/"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors"
          >
            <svg
              className="w-4 h-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to Gallery
          </Link>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center space-x-4 mb-4 sm:mb-0">
            <div className="w-16 h-16 rounded-full overflow-hidden bg-gray-100 flex-shrink-0">
              <img
                src={person.thumbnail_url}
                alt={`Person ${person.id}`}
                className="w-full h-full object-cover"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.style.display = 'none';
                }}
              />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Person {person.id.slice(0, 8)}
              </h1>
              <p className="text-gray-600">
                {totalPhotos} {totalPhotos === 1 ? 'photo' : 'photos'} found
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-500">
              Confidence: {Math.round(person.cluster_confidence * 100)}%
            </div>
            <button
              onClick={refetchPhotos}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-md text-sm transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Photos */}
      {photos.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg
              className="w-12 h-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No photos found
          </h3>
          <p className="text-gray-600">
            This person doesn't appear in any processed photos yet.
          </p>
        </div>
      ) : (
        <>
          <PhotoGrid photos={photos} onPhotoClick={handlePhotoClick} />
          
          {/* Pagination */}
          {totalPages > 1 && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={handlePageChange}
              hasNextPage={hasNextPage}
            />
          )}
        </>
      )}

      {/* Photo Viewer Modal */}
      {selectedPhoto && (
        <PhotoViewer
          photo={selectedPhoto}
          onClose={handleCloseViewer}
          onNext={handleNextPhoto}
          onPrev={handlePrevPhoto}
          showNavigation={photos.length > 1}
        />
      )}
    </div>
  );
}

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  hasNextPage: boolean;
}

function Pagination({ currentPage, totalPages, onPageChange, hasNextPage }: PaginationProps) {
  const getVisiblePages = () => {
    const delta = 2;
    const range = [];
    const rangeWithDots = [];

    for (let i = Math.max(2, currentPage - delta); 
         i <= Math.min(totalPages - 1, currentPage + delta); 
         i++) {
      range.push(i);
    }

    if (currentPage - delta > 2) {
      rangeWithDots.push(1, '...');
    } else {
      rangeWithDots.push(1);
    }

    rangeWithDots.push(...range);

    if (currentPage + delta < totalPages - 1) {
      rangeWithDots.push('...', totalPages);
    } else if (totalPages > 1) {
      rangeWithDots.push(totalPages);
    }

    return rangeWithDots;
  };

  return (
    <div className="flex items-center justify-center space-x-2 mt-8">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 rounded-md text-sm font-medium text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Previous
      </button>

      {getVisiblePages().map((page, index) => (
        <React.Fragment key={index}>
          {page === '...' ? (
            <span className="px-3 py-2 text-gray-400">...</span>
          ) : (
            <button
              onClick={() => onPageChange(page as number)}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                currentPage === page
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              {page}
            </button>
          )}
        </React.Fragment>
      ))}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={!hasNextPage}
        className="px-3 py-2 rounded-md text-sm font-medium text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Next
      </button>
    </div>
  );
}