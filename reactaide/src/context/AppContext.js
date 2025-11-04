import React, { createContext, useContext, useReducer, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

// Global flag to prevent multiple simultaneous health checks
let isCheckingConnection = false;

const AppContext = createContext();

// Load state from sessionStorage on initialization
const loadPersistedState = () => {
  try {
    const persisted = sessionStorage.getItem('aide-app-state');
    if (persisted) {
      return JSON.parse(persisted);
    }
  } catch (error) {
    console.error('Failed to load persisted state:', error);
  }
  return null;
};

// Save state to sessionStorage
const saveStateToStorage = (state) => {
  try {
    // Don't persist loading and error states
    const stateToSave = {
      ...state,
      loading: false,
      error: null,
      notifications: []
    };
    sessionStorage.setItem('aide-app-state', JSON.stringify(stateToSave));
  } catch (error) {
    console.error('Failed to save state to storage:', error);
  }
};

const initialState = {
  // Backend connection
  backendUrl: 'http://localhost:8000',
  isConnected: false,
  connectionError: null,
  
  // Current project
  currentProject: null,
  projectPath: '',
  
  // Agent states - now supports complete state objects
  agents: {
    repository: { initialized: false, data: null, analysisData: null },
    environment: { initialized: false, data: null, environmentData: null },
    documentation: { initialized: false, data: null, documentationData: null },
    qna: { initialized: false, data: null, qnaData: null, conversation: [], followUpQuestions: [] },
    walkthrough: { initialized: false, data: null, walkthroughData: null, steps: [], sessionStatus: null },
    cicd: { initialized: false, data: null, cicdData: null },
    feedback: { initialized: false, data: null, feedbackData: null }
  },
  
  // UI state
  loading: false,
  error: null,
  notifications: []
};

// Merge persisted state with initial state
const persistedState = loadPersistedState();
const finalInitialState = persistedState ? { ...initialState, ...persistedState } : initialState;

function appReducer(state, action) {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    
    case 'SET_BACKEND_CONNECTION':
      return { 
        ...state, 
        isConnected: action.payload.connected,
        connectionError: action.payload.error 
      };
    
    case 'SET_PROJECT':
      return { 
        ...state, 
        currentProject: action.payload.project,
        projectPath: action.payload.path 
      };
    
    case 'UPDATE_AGENT':
      return {
        ...state,
        agents: {
          ...state.agents,
          [action.payload.agent]: {
            ...state.agents[action.payload.agent],
            ...action.payload.data
          }
        }
      };
    
    case 'UPDATE_AGENT_DEEP':
      return {
        ...state,
        agents: {
          ...state.agents,
          [action.payload.agent]: {
            ...state.agents[action.payload.agent],
            ...action.payload.data
          }
        }
      };
    
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [...state.notifications, action.payload]
      };
    
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload)
      };
    
    default:
      return state;
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, finalInitialState);
  const hasCheckedConnection = useRef(false);

  // Persist state to sessionStorage whenever state changes
  useEffect(() => {
    saveStateToStorage(state);
  }, [state]);

  const checkBackendConnection = useCallback(async () => {
    if (isCheckingConnection) {
      return; // Prevent multiple simultaneous checks
    }
    
    isCheckingConnection = true;
    try {
      await axios.get(`${state.backendUrl}/healthz`);
      dispatch({
        type: 'SET_BACKEND_CONNECTION',
        payload: { connected: true, error: null }
      });
    } catch (error) {
      dispatch({
        type: 'SET_BACKEND_CONNECTION',
        payload: { 
          connected: false, 
          error: `Backend connection failed: ${error.message}` 
        }
      });
    } finally {
      isCheckingConnection = false;
    }
  }, [state.backendUrl]);

  // Check backend connection on mount only
  useEffect(() => {
    if (!hasCheckedConnection.current) {
      checkBackendConnection();
      hasCheckedConnection.current = true;
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const setProject = (project, path) => {
    dispatch({
      type: 'SET_PROJECT',
      payload: { project, path }
    });
  };

  const updateAgent = (agent, data) => {
    dispatch({
      type: 'UPDATE_AGENT',
      payload: { agent, data }
    });
  };

  const updateAgentDeep = (agent, data) => {
    dispatch({
      type: 'UPDATE_AGENT_DEEP',
      payload: { agent, data }
    });
  };

  const clearAgentState = (agent) => {
    dispatch({
      type: 'UPDATE_AGENT',
      payload: { agent, data: {} }
    });
  };

  const resetAllAgents = () => {
    const resetAgents = Object.keys(state.agents).reduce((acc, key) => ({
      ...acc,
      [key]: { initialized: false, data: null }
    }), {});
    
    dispatch({
      type: 'UPDATE_AGENT_DEEP',
      payload: { agent: Object.keys(state.agents)[0], data: resetAgents }
    });
  };

  const setLoading = (loading) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  };

  const setError = (error) => {
    dispatch({ type: 'SET_ERROR', payload: error });
    toast.error(error);
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const addNotification = (notification) => {
    const id = Date.now();
    dispatch({
      type: 'ADD_NOTIFICATION',
      payload: { id, ...notification }
    });
    toast.success(notification.message);
  };

  const removeNotification = (id) => {
    dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
  };

  const apiCall = async (endpoint, method = 'GET', data = null) => {
    try {
      setLoading(true);
      clearError();
      
      const config = {
        method,
        url: `${state.backendUrl}${endpoint}`,
        headers: {
          'Content-Type': 'application/json',
        }
      };

      if (data) {
        config.data = data;
      }

      const response = await axios(config);
      return response.data;
    } catch (error) {
      let errorMessage = error.response?.data?.detail || error.message;
      
      // Handle validation error arrays
      if (Array.isArray(errorMessage)) {
        errorMessage = errorMessage.map(err => 
          typeof err === 'object' && err.msg ? err.msg : JSON.stringify(err)
        ).join(', ');
      }
      
      // Only show error toast for non-health check endpoints
      if (!endpoint.includes('healthz') && !endpoint.includes('readyz')) {
        setError(errorMessage);
      } else {
        // For health checks, just update the connection state without showing toast
        dispatch({
          type: 'SET_BACKEND_CONNECTION',
          payload: { 
            connected: false, 
            error: errorMessage 
          }
        });
      }
      
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const refreshConnection = useCallback(async () => {
    await checkBackendConnection();
  }, [checkBackendConnection]);

  const value = {
    ...state,
    setProject,
    updateAgent,
    updateAgentDeep,
    clearAgentState,
    resetAllAgents,
    setLoading,
    setError,
    clearError,
    addNotification,
    removeNotification,
    apiCall,
    checkBackendConnection,
    refreshConnection
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
