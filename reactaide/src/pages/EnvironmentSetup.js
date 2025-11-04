import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import useAgentState from '../hooks/useAgentState';
import {
  Container,
  Terminal,
  CheckCircle,
  AlertCircle,
  Clock,
  Play,
  Activity,
  Code
} from 'lucide-react';

const EnvironmentSetup = () => {
  const { 
    currentProject, 
    loading, 
    apiCall, 
    addNotification 
  } = useApp();
  
  // Use persistent agent state from context
  const agentState = useAgentState('environment');
  const environmentData = agentState.state.environmentData;
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [selectedStep] = useState(1);
  const [projectPath, setProjectPath] = useState('');

  useEffect(() => {
    if (currentProject) {
      setProjectPath(currentProject.path);
    }
  }, [currentProject]);

  const steps = [
    {
      id: 1,
      name: 'Analyze Environment',
      description: 'Detect runtimes and dependencies',
      icon: Activity,
      action: handleAnalyzeEnvironment
    },
    {
      id: 2,
      name: 'Build Environment',
      description: 'Create Docker/DevContainer setup',
      icon: Container,
      action: handleBuildEnvironment
    },
    {
      id: 3,
      name: 'Validate Setup',
      description: 'Test and validate the environment',
      icon: CheckCircle,
      action: handleValidateEnvironment
    },
    {
      id: 4,
      name: 'Check Status',
      description: 'Monitor container status',
      icon: Terminal,
      action: handleCheckStatus
    }
  ];

  async function handleAnalyzeEnvironment() {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsAnalyzing(true);
    try {
      const result = await apiCall('/api/env/environment/analyze', 'POST', {
        project_path: projectPath,
        dockerize: true,
        runtime_hint: null
      });
      
      agentState.updateStateField('environmentData', result);
      agentState.updateStateField('data', result);
      agentState.updateStateField('initialized', true);
      
      addNotification({ 
        message: 'Environment analysis completed successfully' 
      });
      
    } catch (error) {
      console.error('Environment analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleBuildEnvironment() {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsBuilding(true);
    try {
      const result = await apiCall('/api/env/environment/build', 'POST', {
        project_path: projectPath,
        dockerize: true,
        runtime_hint: null
      });
      
      const updatedData = { ...environmentData, buildResult: result };
      agentState.updateStateField('environmentData', updatedData);
      
      addNotification({ 
        message: 'Environment build completed successfully' 
      });
      
    } catch (error) {
      console.error('Environment build failed:', error);
    } finally {
      setIsBuilding(false);
    }
  }

  async function handleValidateEnvironment() {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsValidating(true);
    try {
      const result = await apiCall('/api/env/environment/validate', 'POST', {
        project_path: projectPath
      });
      
      const updatedData = { ...environmentData, validationResult: result };
      agentState.updateStateField('environmentData', updatedData);
      
      addNotification({ 
        message: 'Environment validation completed successfully' 
      });
      
    } catch (error) {
      console.error('Environment validation failed:', error);
    } finally {
      setIsValidating(false);
    }
  }

  async function handleCheckStatus() {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    try {
      const result = await apiCall('/api/env/environment/status/container-123', 'GET');
      
      const updatedData = { ...environmentData, statusResult: result };
      agentState.updateStateField('environmentData', updatedData);
      
      addNotification({ 
        message: 'Container status retrieved successfully' 
      });
      
    } catch (error) {
      console.error('Status check failed:', error);
    }
  }

  const getStepStatus = (stepId) => {
    if (!environmentData) return 'pending';
    
    switch (stepId) {
      case 1:
        return environmentData.runtime || environmentData.dependencies ? 'completed' : 'pending';
      case 2:
        return environmentData.buildResult ? 'completed' : 'pending';
      case 3:
        return environmentData.validationResult ? 'completed' : 'pending';
      case 4:
        return environmentData.statusResult ? 'completed' : 'pending';
      default:
        return 'pending';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const renderRuntimeInfo = () => {
    if (!environmentData?.runtime) return null;

    const { runtime } = environmentData;

    return (
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Detected Runtimes
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(runtime).map(([key, value]) => (
              <div key={key} className="bg-dark-accent rounded-lg p-4">
                <div className="flex items-center">
                  <Code className="h-5 w-5 text-primary-500 mr-2" />
                  <span className="text-sm font-medium text-dark-text capitalize">
                    {key.replace('_', ' ')}
                  </span>
                </div>
                <div className="mt-1 text-sm text-dark-text-secondary">
                  {typeof value === 'object' ? (
                    <pre className="text-xs bg-dark-surface p-2 rounded overflow-x-auto text-dark-text">
                      {JSON.stringify(value, null, 2)}
                    </pre>
                  ) : (
                    <span>{String(value)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderDependencies = () => {
    if (!environmentData?.dependencies) return null;

    const { dependencies } = environmentData;

    return (
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Dependencies
          </h3>
          <div className="space-y-4">
            {Object.entries(dependencies).map(([type, deps]) => (
              <div key={type}>
                <h4 className="text-sm font-medium text-gray-700 mb-2 capitalize">
                  {type.replace('_', ' ')}
                </h4>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {Array.isArray(deps) ? deps.map((dep, index) => (
                    <div key={index} className="bg-dark-accent rounded-md p-2">
                      <span className="text-sm text-dark-text">
                        {typeof dep === 'object' ? JSON.stringify(dep) : String(dep)}
                      </span>
                    </div>
                  )) : (
                    <div className="bg-dark-accent rounded-md p-2">
                      <span className="text-sm text-dark-text">
                        {typeof deps === 'object' ? (
                          <pre className="text-xs whitespace-pre-wrap">
                            {JSON.stringify(deps, null, 2)}
                          </pre>
                        ) : (
                          String(deps)
                        )}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderBuildResult = () => {
    if (!environmentData?.buildResult) return null;

    const { buildResult } = environmentData;

    return (
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Build Result
          </h3>
          <div className="space-y-4">
            <div className="flex items-center">
              <span className="text-sm font-medium text-gray-700">Status:</span>
              <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                buildResult.status === 'success' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {buildResult.status}
              </span>
            </div>
            {buildResult.result && (
              <div className="bg-gray-900 rounded-lg p-4">
                <pre className="text-sm text-gray-100 whitespace-pre-wrap overflow-x-auto">
                  {typeof buildResult.result === 'object' 
                    ? JSON.stringify(buildResult.result, null, 2)
                    : String(buildResult.result)
                  }
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderValidationResult = () => {
    if (!environmentData?.validationResult) return null;

    const { validationResult } = environmentData;

    return (
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Validation Results
          </h3>
          <div className="space-y-4">
            <div className="flex items-center">
              <span className="text-sm font-medium text-gray-700">Status:</span>
              <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                validationResult.status === 'success' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {validationResult.status}
              </span>
            </div>
            {validationResult.validation_results && (
              <div className="bg-gray-900 rounded-lg p-4">
                <pre className="text-sm text-gray-100 whitespace-pre-wrap overflow-x-auto">
                  {typeof validationResult.validation_results === 'object' 
                    ? JSON.stringify(validationResult.validation_results, null, 2)
                    : String(validationResult.validation_results)
                  }
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-dark-text sm:text-3xl sm:truncate">
            Environment Setup
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Docker containers, DevContainer, and runtime setup
          </p>
        </div>
      </div>

      {/* Project Path Input */}
      {!currentProject && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-dark-surface shadow rounded-lg border border-dark-border"
        >
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Project Path
            </h3>
            <div className="flex space-x-4">
              <div className="flex-1">
                <input
                  type="text"
                  className="input"
                  placeholder="Enter project path"
                  value={projectPath}
                  onChange={(e) => setProjectPath(e.target.value)}
                />
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Steps */}
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-6">
            Environment Setup Steps
          </h3>
          <div className="space-y-4">
            {steps.map((step, index) => {
              const status = getStepStatus(step.id);
              const isActive = selectedStep === step.id;
              
              return (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`border rounded-lg p-4 ${
                    isActive ? 'border-primary-500 bg-primary-900/20' : 'border-dark-border'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <step.icon className="h-6 w-6 text-primary-500" />
                      </div>
                      <div className="ml-4">
                        <h4 className="text-sm font-medium text-dark-text">
                          {step.name}
                        </h4>
                        <p className="text-sm text-dark-text-secondary">
                          {step.description}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(status)}
                      <button
                        onClick={step.action}
                        disabled={loading || isAnalyzing || isBuilding || isValidating}
                        className="btn btn-primary px-3 py-1 text-sm"
                      >
                        {loading || isAnalyzing || isBuilding || isValidating ? (
                          <>
                            <Activity className="animate-spin h-4 w-4 mr-1" />
                            Processing...
                          </>
                        ) : (
                          <>
                            <Play className="h-4 w-4 mr-1" />
                            Execute
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Results */}
      {environmentData && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {renderRuntimeInfo()}
          {renderDependencies()}
          {renderBuildResult()}
          {renderValidationResult()}
        </motion.div>
      )}
    </div>
  );
};

export default EnvironmentSetup;
