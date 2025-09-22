import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { GalleryHomepage } from '../GalleryHomepage';
import { usePersons } from '../../hooks/useApi';

// Mock the usePersons hook
jest.mock('../../hooks/useApi');
const mockUsePersons = usePersons as jest.MockedFunction<typeof usePersons>;

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

const mockPersonsData = {
  persons: [
    {
      id: 'person-1',
      thumbnail_url: 'https://example.com/thumb1.jpg',
      photo_count: 5,
      cluster_confidence: 0.95,
    },
    {
      id: 'person-2',
      thumbnail_url: 'https://example.com/thumb2.jpg',
      photo_count: 3,
      cluster_confidence: 0.87,
    },
  ],
  total: 2,
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('GalleryHomepage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    mockUsePersons.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: jest.fn(),
      clearError: jest.fn(),
    });

    renderWithRouter(<GalleryHomepage />);
    
    expect(screen.getByText('Loading photo gallery...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    const mockRefetch = jest.fn();
    mockUsePersons.mockReturnValue({
      data: null,
      loading: false,
      error: 'Failed to load data',
      refetch: mockRefetch,
      clearError: jest.fn(),
    });

    renderWithRouter(<GalleryHomepage />);
    
    expect(screen.getByText('Failed to load gallery')).toBeInTheDocument();
    expect(screen.getByText('Failed to load data')).toBeInTheDocument();
    
    const retryButton = screen.getByText('Try Again');
    fireEvent.click(retryButton);
    expect(mockRefetch).toHaveBeenCalled();
  });

  it('renders persons grid', () => {
    mockUsePersons.mockReturnValue({
      data: mockPersonsData,
      loading: false,
      error: null,
      refetch: jest.fn(),
      clearError: jest.fn(),
    });

    renderWithRouter(<GalleryHomepage />);
    
    expect(screen.getByText('Event Photo Gallery')).toBeInTheDocument();
    expect(screen.getByText('2 people found')).toBeInTheDocument();
    expect(screen.getByText('Person person-1')).toBeInTheDocument();
    expect(screen.getByText('Person person-2')).toBeInTheDocument();
    expect(screen.getByText('5 photos')).toBeInTheDocument();
    expect(screen.getByText('3 photos')).toBeInTheDocument();
  });

  it('handles minimum photos filter', async () => {
    const mockRefetch = jest.fn();
    mockUsePersons.mockReturnValue({
      data: mockPersonsData,
      loading: false,
      error: null,
      refetch: mockRefetch,
      clearError: jest.fn(),
    });

    renderWithRouter(<GalleryHomepage />);
    
    const filter5Button = screen.getByText('5+');
    fireEvent.click(filter5Button);
    
    // The hook should be called with new parameters
    await waitFor(() => {
      expect(mockUsePersons).toHaveBeenCalledWith(1, 50, 5);
    });
  });

  it('renders empty state when no persons found', () => {
    mockUsePersons.mockReturnValue({
      data: { persons: [], total: 0 },
      loading: false,
      error: null,
      refetch: jest.fn(),
      clearError: jest.fn(),
    });

    renderWithRouter(<GalleryHomepage />);
    
    expect(screen.getByText('No people found')).toBeInTheDocument();
    expect(screen.getByText('Try reducing the minimum photo count or check if photos have been processed.')).toBeInTheDocument();
  });

  it('handles image load errors', () => {
    mockUsePersons.mockReturnValue({
      data: mockPersonsData,
      loading: false,
      error: null,
      refetch: jest.fn(),
      clearError: jest.fn(),
    });

    renderWithRouter(<GalleryHomepage />);
    
    const images = screen.getAllByRole('img');
    fireEvent.error(images[0]);
    
    // Should show fallback icon instead of broken image
    expect(images[0]).toHaveStyle('display: none');
  });

  it('shows confidence indicators', () => {
    mockUsePersons.mockReturnValue({
      data: mockPersonsData,
      loading: false,
      error: null,
      refetch: jest.fn(),
      clearError: jest.fn(),
    });

    renderWithRouter(<GalleryHomepage />);
    
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByText('87%')).toBeInTheDocument();
  });

  it('creates correct links to person galleries', () => {
    mockUsePersons.mockReturnValue({
      data: mockPersonsData,
      loading: false,
      error: null,
      refetch: jest.fn(),
      clearError: jest.fn(),
    });

    renderWithRouter(<GalleryHomepage />);
    
    const personLinks = screen.getAllByRole('link');
    expect(personLinks[0]).toHaveAttribute('href', '/person/person-1');
    expect(personLinks[1]).toHaveAttribute('href', '/person/person-2');
  });
});