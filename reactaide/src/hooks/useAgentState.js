import { useCallback, useMemo } from 'react';
import { useApp } from '../context/AppContext';

/**
 * Custom hook to manage agent state in the context
 * This hook provides easy access to agent state and methods to update it
 * All state is automatically persisted to sessionStorage
 * 
 * @param {string} agentName - Name of the agent (e.g., 'repository', 'qna')
 * @returns {Object} - Agent state and update methods
 */
export function useAgentState(agentName) {
  const { agents, updateAgent } = useApp();
  
  // Get the agent's current state - memoized to prevent recreating on every render
  const agentState = useMemo(() => agents[agentName] || {}, [agents, agentName]);
  
  /**
   * Update agent state with new data
   * Merges new data with existing state
   */
  const updateState = useCallback((newData) => {
    updateAgent(agentName, newData);
  }, [agentName, updateAgent]);
  
  /**
   * Replace agent state completely
   */
  const replaceState = useCallback((newState) => {
    updateAgent(agentName, newState);
  }, [agentName, updateAgent]);
  
  /**
   * Get a specific field from agent state
   */
  const getStateField = useCallback((fieldName) => {
    return agentState[fieldName];
  }, [agentState]);
  
  /**
   * Update a specific field in agent state
   */
  const updateStateField = useCallback((fieldName, value) => {
    updateAgent(agentName, { [fieldName]: value });
  }, [agentName, updateAgent]);
  
  return {
    // State
    state: agentState,
    
    // Methods
    updateState,
    replaceState,
    getStateField,
    updateStateField,
    
    // Direct access to common fields
    data: agentState.data,
    initialized: agentState.initialized
  };
}

export default useAgentState;

