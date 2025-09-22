import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { usePersons, usePaginatedData } from '../hooks/useApi';
import { PersonThumbnail, Photo } from '../types';
import { LoadingSpinner, PageLoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';
import { apiService } from '../services/api';

export function GalleryHomepage() {
  const [minPhotos, setMinPhotos] = useState(1);
  const [activeSection, setActiveSection] = useState<'people' | 'all-photos' | 'no-faces'>('people');

  const { data: personsResponse, loading: personsLoading, error: personsError, refetch: refetchPersons } = usePersons(1, 50, minPhotos);

  // Stable fetch functions for infinite scrolling
  const fetchAllPhotos = useCallback((page: number, perPage: number) =>
    apiService.getAllPhotos(page, perPage, true, undefined).then(response => ({
      data: response.photos,
      total: response.total,
      has_next: response.has_next
    })), []);

  const fetchNoFacesPhotos = useCallback((page: number, perPage: number) =>
    apiService.getAllPhotos(page, perPage, true, false).then(response => ({
      data: response.photos,
      total: response.total,
      has_next: response.has_next
    })), []);

  // Use infinite scrolling for photos
  const {
    data: allPhotos,
    loading: allPhotosLoading,
    error: allPhotosError,
    hasNextPage: allPhotosHasNext,
    loadMore: loadMoreAllPhotos,
    refresh: refreshAllPhotos,
    total: allPhotosTotal
  } = usePaginatedData(fetchAllPhotos, 50);

  const {
    data: noFacesPhotos,
    loading: noFacesLoading,
    error: noFacesError,
    hasNextPage: noFacesHasNext,
    loadMore: loadMoreNoFaces,
    refresh: refreshNoFaces,
    total: noFacesTotal
  } = usePaginatedData(fetchNoFacesPhotos, 50);

  const handleMinPhotosChange = useCallback((newMinPhotos: number) => {
    setMinPhotos(newMinPhotos);
  }, []);

  const handleSectionChange = useCallback((section: 'people' | 'all-photos' | 'no-faces') => {
    setActiveSection(section);
  }, []);

  const loading = personsLoading;
  const error = personsError;

  if (loading && activeSection === 'people' && personsLoading) {
    return <PageLoadingSpinner text="Loading photo gallery..." />;
  }

  if (error && activeSection === 'people' && personsError) {
    return (
      <ErrorMessage
        message={personsError}
        onRetry={refetchPersons}
        title="Failed to load gallery"
      />
    );
  }

  const persons = personsResponse?.persons || [];
  const personsTotal = personsResponse?.total || 0;

  // Debug logging
  console.log('Gallery state:', {
    activeSection,
    personsTotal,
    allPhotosTotal,
    noFacesTotal,
    personsLoading,
    allPhotosLoading,
    noFacesLoading
  });

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header Section */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Event Photo Gallery
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Find all your photos by clicking on the faces below. Each person shows
          the number of photos they appear in.
        </p>
      </div>

      {/* Section Navigation */}
      <div className="flex justify-center items-center mb-8">
        <div className="flex space-x-2 bg-gray-100 p-2 rounded-lg">
          <button
            onClick={() => {
              console.log('Switching to people section');
              handleSectionChange('people');
            }}
            className={`px-6 py-3 rounded-md text-sm font-medium transition-colors border-2 ${
              activeSection === 'people'
                ? 'bg-blue-600 text-white border-blue-600 shadow-lg'
                : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
            }`}
          >
People ({personsTotal})
          </button>
          <button
            onClick={() => {
              console.log('Switching to all-photos section');
              handleSectionChange('all-photos');
            }}
            className={`px-6 py-3 rounded-md text-sm font-medium transition-colors border-2 ${
              activeSection === 'all-photos'
                ? 'bg-blue-600 text-white border-blue-600 shadow-lg'
                : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
            }`}
          >
All Photos ({allPhotosTotal})
          </button>
          <button
            onClick={() => {
              console.log('Switching to no-faces section');
              handleSectionChange('no-faces');
            }}
            className={`px-6 py-3 rounded-md text-sm font-medium transition-colors border-2 ${
              activeSection === 'no-faces'
                ? 'bg-blue-600 text-white border-blue-600 shadow-lg'
                : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
            }`}
          >
No Faces ({noFacesTotal})
          </button>
        </div>
      </div>

      {/* Debug Info */}
      <div className="text-center mb-4 text-sm text-gray-500">
        Active Section: {activeSection} | People: {personsTotal} | All Photos: {allPhotosTotal} | No Faces: {noFacesTotal}
      </div>

      {/* Filter Controls - Only show for people section */}
      {activeSection === 'people' && (
        <div className="flex flex-col sm:flex-row justify-between items-center mb-8 bg-white p-4 rounded-lg shadow-sm">
          <div className="flex items-center space-x-4 mb-4 sm:mb-0">
            <span className="text-sm font-medium text-gray-700">
              Minimum photos per person:
            </span>
            <div className="flex space-x-2">
              {[1, 2, 5, 10].map((count) => (
                <button
                  key={count}
                  onClick={() => handleMinPhotosChange(count)}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    minPhotos === count
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {count}+
                </button>
              ))}
            </div>
          </div>

          <div className="text-sm text-gray-600">
            {personsTotal} {personsTotal === 1 ? 'person' : 'people'} found
          </div>
        </div>
      )}

      {/* Content Sections */}
      {activeSection === 'people' && (
        <PeopleSection
          persons={persons}
          loading={personsLoading}
          error={personsError}
          onRefresh={refetchPersons}
        />
      )}

      {activeSection === 'all-photos' && (
        <InfinitePhotosSection
          photos={allPhotos}
          loading={allPhotosLoading}
          error={allPhotosError}
          hasNextPage={allPhotosHasNext}
          onLoadMore={loadMoreAllPhotos}
          onRefresh={refreshAllPhotos}
          title="All Photos"
          emptyMessage="No photos found. Upload some photos to get started."
          showDownloadAll={true}
          hasFacesFilter={undefined}
        />
      )}

      {activeSection === 'no-faces' && (
        <InfinitePhotosSection
          photos={noFacesPhotos}
          loading={noFacesLoading}
          error={noFacesError}
          hasNextPage={noFacesHasNext}
          onLoadMore={loadMoreNoFaces}
          onRefresh={refreshNoFaces}
          title="Photos Without Faces"
          emptyMessage="No photos without faces found. All photos seem to contain people!"
          showDownloadAll={true}
          hasFacesFilter={false}
        />
      )}

      {/* Footer Info */}
      <div className="mt-12 text-center text-sm text-gray-500">
        <p>
          Photos are automatically organized by face recognition.
          Click on any face to view all photos containing that person.
        </p>
      </div>
    </div>
  );
}

interface PersonCardProps {
  person: PersonThumbnail;
}

function PersonCard({ person }: PersonCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const handleImageLoad = useCallback(() => {
    setImageLoaded(true);
  }, []);

  const handleImageError = useCallback(() => {
    setImageError(true);
    setImageLoaded(true);
  }, []);

  const downloadPhotos = useCallback(async (quality: 'original' | 'web' | 'thumbnail', event: React.MouseEvent) => {
    event.preventDefault(); // Prevent navigation to person page
    event.stopPropagation();

    setDownloading(true);
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/persons/${person.id}/download?quality=${quality}`
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `person_${person.id.slice(0, 8)}_photos_${quality}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        console.error('Download failed:', response.statusText);
        alert('Download failed. Please try again.');
      }
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    }
    setDownloading(false);
  }, [person.id]);

  return (
    <Link
      to={`/person/${person.id}`}
      className="group block bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden"
    >
      <div className="aspect-square relative bg-gray-100">
        {!imageLoaded && (
          <div className="absolute inset-0 flex items-center justify-center">
            <LoadingSpinner size="sm" />
          </div>
        )}

        {imageError ? (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
            <svg
              className="w-8 h-8 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
        ) : (
          <img
            src={person.thumbnail_url}
            alt={`Person ${person.id}`}
            className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-200 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
            onLoad={handleImageLoad}
            onError={handleImageError}
            loading="lazy"
          />
        )}

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200 flex items-center justify-center">
          <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
              />
            </svg>
          </div>
        </div>
      </div>

      <div className="p-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-900">
            Person {person.id.slice(0, 8)}
          </span>
          <span className="text-xs text-gray-500">
            {person.photo_count} {person.photo_count === 1 ? 'photo' : 'photos'}
          </span>
        </div>

        {/* Confidence indicator */}
        <div className="mt-2 flex items-center">
          <div className="flex-1 bg-gray-200 rounded-full h-1">
            <div
              className="bg-blue-600 h-1 rounded-full transition-all duration-300"
              style={{ width: `${person.cluster_confidence * 100}%` }}
            />
          </div>
          <span className="ml-2 text-xs text-gray-400">
            {Math.round(person.cluster_confidence * 100)}%
          </span>
        </div>

        {/* Download Buttons */}
        <div className="mt-3 flex space-x-2">
          <button
            onClick={(e) => downloadPhotos('web', e)}
            disabled={downloading}
            className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white text-xs py-2 px-3 rounded-md transition-colors duration-200 font-medium"
          >
            {downloading ? 'Preparing...' : 'Download Photos'}
          </button>
          <button
            onClick={(e) => downloadPhotos('original', e)}
            disabled={downloading}
            className="flex-1 bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white text-xs py-2 px-3 rounded-md transition-colors duration-200 font-medium"
          >
            {downloading ? 'Preparing...' : 'Original Quality'}
          </button>
        </div>
      </div>
    </Link>
  );
}

interface PeopleSectionProps {
  persons: PersonThumbnail[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

function PeopleSection({ persons, loading, error, onRefresh }: PeopleSectionProps) {
  if (loading) {
    return <PageLoadingSpinner text="Loading people..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message={error}
        onRetry={onRefresh}
        title="Failed to load people"
      />
    );
  }

  if (persons.length === 0) {
    return (
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
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No people found
        </h3>
        <p className="text-gray-600 mb-4">
          Try reducing the minimum photo count or check if photos have been processed.
        </p>
        <button
          onClick={onRefresh}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
        >
          Refresh Gallery
        </button>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
      {persons.map((person) => (
        <PersonCard key={person.id} person={person} />
      ))}
    </div>
  );
}

interface PhotoCardProps {
  photo: Photo;
}

function PhotoCard({ photo }: PhotoCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleImageLoad = useCallback(() => {
    setImageLoaded(true);
  }, []);

  const handleImageError = useCallback(() => {
    setImageError(true);
    setImageLoaded(true);
  }, []);

  return (
    <div className="group block bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden">
      <div className="aspect-square relative bg-gray-100">
        {!imageLoaded && (
          <div className="absolute inset-0 flex items-center justify-center">
            <LoadingSpinner size="sm" />
          </div>
        )}

        {imageError ? (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
            <svg
              className="w-8 h-8 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 002 2z"
              />
            </svg>
          </div>
        ) : (
          <img
            src={photo.thumbnail_url}
            alt={photo.filename}
            className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-200 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
            onLoad={handleImageLoad}
            onError={handleImageError}
            loading="lazy"
          />
        )}

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200 flex items-center justify-center">
          <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
              />
            </svg>
          </div>
        </div>
      </div>

      <div className="p-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-900 truncate">
            {photo.filename}
          </span>
          {photo.persons && photo.persons.length > 0 && (
            <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
              {photo.persons.length} {photo.persons.length === 1 ? 'person' : 'people'}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

interface InfinitePhotosSectionProps {
  photos: Photo[];
  loading: boolean;
  error: string | null;
  hasNextPage: boolean;
  onLoadMore: () => void;
  onRefresh: () => void;
  title: string;
  emptyMessage: string;
  showDownloadAll: boolean;
  hasFacesFilter?: boolean;
}

function InfinitePhotosSection({
  photos,
  loading,
  error,
  hasNextPage,
  onLoadMore,
  onRefresh,
  title,
  emptyMessage,
  showDownloadAll,
  hasFacesFilter
}: InfinitePhotosSectionProps) {
  const [downloading, setDownloading] = useState(false);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  console.log(`InfinitePhotosSection ${title}:`, { photos: photos.length, loading, error, hasNextPage });

  // Intersection observer for infinite scrolling
  useEffect(() => {
    if (!loadMoreRef.current || loading || !hasNextPage) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !loading) {
          onLoadMore();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(loadMoreRef.current);

    return () => observer.disconnect();
  }, [loading, hasNextPage, onLoadMore]);

  const downloadAllPhotos = useCallback(async (quality: 'original' | 'web' | 'thumbnail') => {
    setDownloading(true);
    try {
      const params = new URLSearchParams({ quality });
      if (hasFacesFilter !== undefined) {
        params.append('has_faces', hasFacesFilter.toString());
      }

      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/photos/download?${params}`
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        let filename = `all_photos_${quality}.zip`;
        if (hasFacesFilter === true) {
          filename = `all_photos_with_faces_${quality}.zip`;
        } else if (hasFacesFilter === false) {
          filename = `all_photos_no_faces_${quality}.zip`;
        }

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        console.error('Download failed:', response.statusText);
        alert('Download failed. Please try again.');
      }
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    }
    setDownloading(false);
  }, [hasFacesFilter]);

  if (loading && photos.length === 0) {
    return <PageLoadingSpinner text={`Loading ${title.toLowerCase()}...`} />;
  }

  if (error && photos.length === 0) {
    return (
      <ErrorMessage
        message={error}
        onRetry={onRefresh}
        title={`Failed to load ${title.toLowerCase()}`}
      />
    );
  }

  if (photos.length === 0 && !loading) {
    return (
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
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 002 2z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No photos found
        </h3>
        <p className="text-gray-600 mb-4">
          {emptyMessage}
        </p>
        <button
          onClick={onRefresh}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
        >
          Refresh
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Download All Section */}
      {showDownloadAll && photos.length > 0 && (
        <div className="mb-6 bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex flex-col sm:flex-row items-center justify-between">
            <div className="mb-4 sm:mb-0">
              <h3 className="text-lg font-medium text-gray-900 mb-1">
                Download All Photos
              </h3>
              <p className="text-sm text-gray-600">
                Download all {photos.length}+ photos as a ZIP file
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => downloadAllPhotos('web')}
                disabled={downloading}
                className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors duration-200 font-medium text-sm"
              >
                {downloading ? 'Preparing...' : 'Download Web Quality'}
              </button>
              <button
                onClick={() => downloadAllPhotos('original')}
                disabled={downloading}
                className="bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-colors duration-200 font-medium text-sm"
              >
                {downloading ? 'Preparing...' : 'Download Original'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Photos Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 transition-all duration-300">
        {photos.map((photo, index) => (
          <div
            key={photo.id}
            style={{
              animationDelay: `${Math.min(index * 50, 1000)}ms`,
              opacity: 1
            }}
            className="animate-fadeIn"
          >
            <PhotoCard photo={photo} />
          </div>
        ))}
      </div>

      {/* Load More Trigger */}
      {hasNextPage && (
        <div
          ref={loadMoreRef}
          className="mt-8 text-center py-8"
        >
          {loading ? (
            <div className="flex items-center justify-center space-x-3 py-4">
              <LoadingSpinner size="sm" />
              <span className="text-gray-600 font-medium">Loading more photos...</span>
            </div>
          ) : (
            <button
              onClick={onLoadMore}
              className="bg-blue-600 text-white px-8 py-4 rounded-lg hover:bg-blue-700 transition-all duration-200 font-medium shadow-md hover:shadow-lg transform hover:scale-105"
            >
              Load More Photos ({photos.length} of many loaded)
            </button>
          )}
        </div>
      )}

      {/* Loading Skeleton for Smooth Experience */}
      {loading && photos.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 mt-4">
          {Array.from({ length: 12 }).map((_, index) => (
            <div
              key={`skeleton-${index}`}
              className="bg-gray-200 rounded-lg aspect-square animate-pulse"
            />
          ))}
        </div>
      )}

      {/* Error Message for Load More */}
      {error && photos.length > 0 && (
        <div className="mt-4 text-center">
          <div className="inline-flex items-center px-4 py-2 bg-red-50 border border-red-200 rounded-md">
            <span className="text-red-600 text-sm mr-2">Failed to load more photos</span>
            <button
              onClick={onLoadMore}
              className="text-red-600 hover:text-red-700 text-sm font-medium underline"
            >
              Try again
            </button>
          </div>
        </div>
      )}
    </div>
  );
}