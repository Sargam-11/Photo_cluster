import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Header } from './components/Header';
import { GalleryHomepage } from './components/GalleryHomepage';
import { PersonGallery } from './components/PersonGallery';
import { LoadingSpinner } from './components/LoadingSpinner';

function App() {
  return (
    <ErrorBoundary>
      <AppProvider>
        <Router>
          <div className="min-h-screen bg-gray-50">
            <Header />
            <main className="container mx-auto px-4 py-8">
              <Routes>
                <Route path="/" element={<GalleryHomepage />} />
                <Route path="/person/:personId" element={<PersonGallery />} />
                <Route path="/loading" element={<LoadingSpinner />} />
                <Route path="*" element={
                  <div className="text-center py-16">
                    <h1 className="text-2xl font-bold text-gray-900 mb-4">Page Not Found</h1>
                    <p className="text-gray-600">The page you're looking for doesn't exist.</p>
                  </div>
                } />
              </Routes>
            </main>
          </div>
        </Router>
      </AppProvider>
    </ErrorBoundary>
  );
}

export default App;