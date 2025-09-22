import React, { useState, useCallback, useEffect } from 'react';
import { Photo } from '../types';
import { usePhotoDownload } from '../hooks/useApi';
import { LoadingSpinner } from './LoadingSpinner';

interface PhotoViewerProps {
  photo: Photo;
  onClose: () => void;
  onNext?: () => void;
  onPrev?: () => void;
  showNavigation?: boolean;
}

export function PhotoViewer({ 
  photo, 
  onClose, 
  onNext, 
  onPrev, 
  showNavigation = false 
}: PhotoViewerProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(null);
  const [imagePosition, setImagePosition] = useState({ x: 0, y: 0 });

  const { downloadPhoto, downloading, error: downloadError } = usePhotoDownload();

  // Reset state when photo changes
  useEffect(() => {
    setImageLoaded(false);
    setImageError(false);
    setZoomLevel(1);
    setImagePosition({ x: 0, y: 0 });
  }, [photo.id]);

  // Handle image loading
  const handleImageLoad = useCallback(() => {
    setImageLoaded(true);
  }, []);

  const handleImageError = useCallback(() => {
    setImageError(true);
    setImageLoaded(true);
  }, []);

  // Handle zoom
  const handleZoomIn = useCallback(() => {
    setZoomLevel(prev => Math.min(prev * 1.5, 5));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoomLevel(prev => Math.max(prev / 1.5, 0.5));
    if (zoomLevel <= 1) {
      setImagePosition({ x: 0, y: 0 });
    }
  }, [zoomLevel]);

  const handleZoomReset = useCallback(() => {
    setZoomLevel(1);
    setImagePosition({ x: 0, y: 0 });
  }, []);

  // Handle dragging for panning
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (zoomLevel > 1) {
      setDragStart({ x: e.clientX - imagePosition.x, y: e.clientY - imagePosition.y });
    }
  }, [zoomLevel, imagePosition]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (dragStart && zoomLevel > 1) {
      setImagePosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  }, [dragStart, zoomLevel]);

  const handleMouseUp = useCallback(() => {
    setDragStart(null);
  }, []);

  // Handle downloads
  const handleDownload = useCallback((quality: 'original' | 'web' | 'thumbnail') => {
    const filename = `${photo.filename.split('.')[0]}_${quality}.jpg`;
    downloadPhoto(photo.id, quality, filename);
  }, [photo, downloadPhoto]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      switch (event.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowLeft':
          onPrev?.();
          break;
        case 'ArrowRight':
          onNext?.();
          break;
        case '+':
        case '=':
          event.preventDefault();
          handleZoomIn();
          break;
        case '-':
          event.preventDefault();
          handleZoomOut();
          break;
        case '0':
          event.preventDefault();
          handleZoomReset();
          break;
        case 'i':
          setShowInfo(prev => !prev);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [onClose, onNext, onPrev, handleZoomIn, handleZoomOut, handleZoomReset]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-95 flex items-center justify-center">
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 z-10 text-white hover:text-gray-300 transition-colors"
        aria-label="Close photo viewer"
      >
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {/* Navigation buttons */}
      {showNavigation && (
        <>
          {onPrev && (
            <button
              onClick={onPrev}
              className="absolute left-4 top-1/2 transform -translate-y-1/2 z-10 text-white hover:text-gray-300 transition-colors"
              aria-label="Previous photo"
            >
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          )}
          
          {onNext && (
            <button
              onClick={onNext}
              className="absolute right-4 top-1/2 transform -translate-y-1/2 z-10 text-white hover:text-gray-300 transition-colors"
              aria-label="Next photo"
            >
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          )}
        </>
      )}

      {/* Toolbar */}
      <div className="absolute top-4 left-4 z-10 flex items-center space-x-2">
        {/* Zoom controls */}
        <div className="bg-black bg-opacity-50 rounded-lg p-2 flex items-center space-x-2">
          <button
            onClick={handleZoomOut}
            className="text-white hover:text-gray-300 transition-colors"
            aria-label="Zoom out"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
            </svg>
          </button>
          
          <span className="text-white text-sm min-w-12 text-center">
            {Math.round(zoomLevel * 100)}%
          </span>
          
          <button
            onClick={handleZoomIn}
            className="text-white hover:text-gray-300 transition-colors"
            aria-label="Zoom in"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
            </svg>
          </button>
          
          <button
            onClick={handleZoomReset}
            className="text-white hover:text-gray-300 transition-colors text-sm px-2"
            aria-label="Reset zoom"
          >
            Reset
          </button>
        </div>

        {/* Download menu */}
        <div className="relative group">
          <button className="bg-black bg-opacity-50 rounded-lg p-2 text-white hover:text-gray-300 transition-colors">
            {downloading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            )}
          </button>
          
          <div className="absolute top-full left-0 mt-1 bg-black bg-opacity-80 rounded-lg py-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none group-hover:pointer-events-auto">
            <button
              onClick={() => handleDownload('original')}
              className="block w-full text-left px-4 py-2 text-white hover:bg-white hover:bg-opacity-10 transition-colors text-sm whitespace-nowrap"
            >
              Download Original
            </button>
            <button
              onClick={() => handleDownload('web')}
              className="block w-full text-left px-4 py-2 text-white hover:bg-white hover:bg-opacity-10 transition-colors text-sm whitespace-nowrap"
            >
              Download Web Quality
            </button>
            <button
              onClick={() => handleDownload('thumbnail')}
              className="block w-full text-left px-4 py-2 text-white hover:bg-white hover:bg-opacity-10 transition-colors text-sm whitespace-nowrap"
            >
              Download Thumbnail
            </button>
          </div>
        </div>

        {/* Info toggle */}
        <button
          onClick={() => setShowInfo(prev => !prev)}
          className={`bg-black bg-opacity-50 rounded-lg p-2 transition-colors ${
            showInfo ? 'text-blue-400' : 'text-white hover:text-gray-300'
          }`}
          aria-label="Toggle photo info"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      </div>

      {/* Photo info panel */}
      {showInfo && (
        <div className="absolute bottom-4 left-4 right-4 z-10 bg-black bg-opacity-80 rounded-lg p-4 text-white">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold mb-2">{photo.filename}</h3>
              <div className="text-sm space-y-1">
                <div>Dimensions: {photo.width} × {photo.height}</div>
                <div>File size: {(photo.file_size / 1024 / 1024).toFixed(2)} MB</div>
                {photo.taken_at && (
                  <div>Taken: {new Date(photo.taken_at).toLocaleDateString()}</div>
                )}
              </div>
            </div>
            <div>
              <div className="text-sm space-y-1">
                <div>People in photo: {photo.persons.length}</div>
                <div>Processed: {photo.processed ? 'Yes' : 'No'}</div>
                {photo.metadata && Object.keys(photo.metadata).length > 0 && (
                  <div>
                    <div className="font-medium mt-2 mb-1">Metadata:</div>
                    {Object.entries(photo.metadata).map(([key, value]) => (
                      <div key={key} className="text-xs">
                        {key}: {String(value)}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main image container */}
      <div 
        className="relative max-w-full max-h-full flex items-center justify-center cursor-move"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {!imageLoaded && (
          <div className="absolute inset-0 flex items-center justify-center">
            <LoadingSpinner size="lg" className="text-white" />
          </div>
        )}

        {imageError ? (
          <div className="flex flex-col items-center justify-center text-white">
            <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <p className="text-lg">Failed to load image</p>
            <p className="text-sm text-gray-400 mt-2">The image could not be displayed</p>
          </div>
        ) : (
          <img
            src={photo.original_url}
            alt={photo.filename}
            className={`max-w-full max-h-full object-contain transition-all duration-200 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            } ${zoomLevel > 1 ? 'cursor-move' : 'cursor-zoom-in'}`}
            onLoad={handleImageLoad}
            onError={handleImageError}
            style={{
              transform: `scale(${zoomLevel}) translate(${imagePosition.x / zoomLevel}px, ${imagePosition.y / zoomLevel}px)`,
              transformOrigin: 'center center'
            }}
            onClick={zoomLevel === 1 ? handleZoomIn : undefined}
            draggable={false}
          />
        )}
      </div>

      {/* Download error */}
      {downloadError && (
        <div className="absolute bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded-lg">
          Download failed: {downloadError}
        </div>
      )}

      {/* Keyboard shortcuts help */}
      <div className="absolute bottom-4 right-4 text-white text-xs opacity-50">
        <div>ESC: Close • ←→: Navigate • +/-: Zoom • I: Info</div>
      </div>
    </div>
  );
}