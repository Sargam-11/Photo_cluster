import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { AppState, AppContextType, PersonThumbnail, Person, Photo } from '../types';

// Initial state
const initialState: AppState = {
  persons: [],
  selectedPerson: null,
  photos: [],
  loading: false,
  error: null,
  currentPage: 1,
  hasNextPage: false,
};

// Action types
type AppAction =
  | { type: 'SET_PERSONS'; payload: PersonThumbnail[] }
  | { type: 'SET_SELECTED_PERSON'; payload: Person | null }
  | { type: 'SET_PHOTOS'; payload: Photo[] }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_CURRENT_PAGE'; payload: number }
  | { type: 'SET_HAS_NEXT_PAGE'; payload: boolean }
  | { type: 'CLEAR_ERROR' };

// Reducer
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_PERSONS':
      return { ...state, persons: action.payload };
    case 'SET_SELECTED_PERSON':
      return { ...state, selectedPerson: action.payload };
    case 'SET_PHOTOS':
      return { ...state, photos: action.payload };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_CURRENT_PAGE':
      return { ...state, currentPage: action.payload };
    case 'SET_HAS_NEXT_PAGE':
      return { ...state, hasNextPage: action.payload };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    default:
      return state;
  }
}

// Context
const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider component
interface AppProviderProps {
  children: ReactNode;
}

export function AppProvider({ children }: AppProviderProps) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  const actions = {
    setPersons: (persons: PersonThumbnail[]) => 
      dispatch({ type: 'SET_PERSONS', payload: persons }),
    setSelectedPerson: (person: Person | null) => 
      dispatch({ type: 'SET_SELECTED_PERSON', payload: person }),
    setPhotos: (photos: Photo[]) => 
      dispatch({ type: 'SET_PHOTOS', payload: photos }),
    setLoading: (loading: boolean) => 
      dispatch({ type: 'SET_LOADING', payload: loading }),
    setError: (error: string | null) => 
      dispatch({ type: 'SET_ERROR', payload: error }),
    setCurrentPage: (page: number) => 
      dispatch({ type: 'SET_CURRENT_PAGE', payload: page }),
    setHasNextPage: (hasNext: boolean) => 
      dispatch({ type: 'SET_HAS_NEXT_PAGE', payload: hasNext }),
    clearError: () => 
      dispatch({ type: 'CLEAR_ERROR' }),
  };

  const contextValue: AppContextType = {
    state,
    actions,
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
}

// Hook to use the context
export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}