import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import {
  GitBranch,
  Settings,
  FileText,
  MessageCircle,
  Play,
  Workflow,
  MessageSquare,
  FolderOpen,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react';

// Global flag to prevent multiple simultaneous stats loading
let isLoadingStats = false;

const Dashboard = () => {
  const { 
    isConnected, 
    currentProject, 
    agents, 
    apiCall,
    refreshConnection
  } = useApp();
  
  const [systemStats, setSystemStats] = useState(null);
  const hasLoadedStats = useRef(false);

  useEffect(() => {
    if (!hasLoadedStats.current && !isLoadingStats) {
      isLoadingStats = true;
      const loadSystemStats = async () => {
        try {
          const health = await apiCall('/healthz');
          const ready = await apiCall('/readyz');
          setSystemStats({ health, ready });
        } catch (error) {
          console.error('Failed to load system stats:', error);
        } finally {
          isLoadingStats = false;
        }
      };

      loadSystemStats();
      hasLoadedStats.current = true;
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const agentCards = [
    {
      name: 'Repository Analysis',
      description: 'Analyze code structure, dependencies, and frameworks',
      icon: GitBranch,
      status: agents.repository.initialized ? 'ready' : 'pending',
      href: '/repository',
      color: 'blue'
    },
    {
      name: 'Environment Setup',
      description: 'Docker containers, DevContainer, and runtime setup',
      icon: Settings,
      status: agents.environment.initialized ? 'ready' : 'pending',
      href: '/environment',
      color: 'green'
    },
    {
      name: 'Documentation',
      description: 'Generate docs and RAG-based knowledge queries',
      icon: FileText,
      status: agents.documentation.initialized ? 'ready' : 'pending',
      href: '/documentation',
      color: 'purple'
    },
    {
      name: 'Q&A Assistant',
      description: 'Conversational interface with project knowledge',
      icon: MessageCircle,
      status: agents.qna.initialized ? 'ready' : 'pending',
      href: '/qna',
      color: 'orange'
    },
    {
      name: 'Walkthrough',
      description: 'Step-by-step onboarding guidance',
      icon: Play,
      status: agents.walkthrough.initialized ? 'ready' : 'pending',
      href: '/walkthrough',
      color: 'pink'
    },
    {
      name: 'CI/CD',
      description: 'GitHub Actions, Jenkins, and diagnostics',
      icon: Workflow,
      status: agents.cicd.initialized ? 'ready' : 'pending',
      href: '/cicd',
      color: 'red'
    },
    {
      name: 'Feedback',
      description: 'Analytics, learning, and model retraining',
      icon: MessageSquare,
      status: agents.feedback.initialized ? 'ready' : 'pending',
      href: '/feedback',
      color: 'indigo'
    }
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'ready':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-dark-text sm:text-3xl sm:truncate">
            Home
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Welcome to AI Developer Onboarding Engine
          </p>
        </div>
      </div>

      {/* Connection Status */}
      <div className="bg-dark-surface overflow-hidden shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              {isConnected ? (
                <CheckCircle className="h-8 w-8 text-green-500" />
              ) : (
                <AlertCircle className="h-8 w-8 text-red-500" />
              )}
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-dark-text-secondary truncate">
                  Backend Connection
                </dt>
                <dd className="text-lg font-medium text-dark-text">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </dd>
              </dl>
            </div>
            {systemStats && (
              <div className="ml-5 flex-shrink-0">
                <div className="text-sm text-dark-text-secondary">
                  Version: {systemStats.health?.version || 'Unknown'}
                </div>
              </div>
            )}
            <div className="ml-2 flex-shrink-0">
              <button
                onClick={async () => {
                  if (isLoadingStats) return; // Prevent multiple simultaneous requests
                  
                  isLoadingStats = true;
                  await refreshConnection();
                  try {
                    const health = await apiCall('/healthz');
                    const ready = await apiCall('/readyz');
                    setSystemStats({ health, ready });
                  } catch (error) {
                    console.error('Failed to load system stats:', error);
                  } finally {
                    isLoadingStats = false;
                  }
                }}
                className="text-primary-600 hover:text-primary-800 text-sm font-medium"
                title="Refresh connection status"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Current Project Info */}
      {currentProject && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-dark-surface shadow rounded-lg border border-dark-border"
        >
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FolderOpen className="h-8 w-8 text-primary-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-dark-text-secondary truncate">
                    Current Project
                  </dt>
                  <dd className="text-lg font-medium text-dark-text">
                    {currentProject.name}
                  </dd>
                  <dd className="text-sm text-dark-text-secondary">
                    {currentProject.path}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Agent Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {agentCards.map((agent, index) => (
          <motion.div
            key={agent.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-dark-surface overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow duration-200 border border-dark-border"
          >
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <agent.icon className={`h-8 w-8 text-${agent.color}-500`} />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-dark-text-secondary truncate">
                      {agent.name}
                    </dt>
                    <dd className="text-lg font-medium text-dark-text">
                      {agent.description}
                    </dd>
                  </dl>
                </div>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(agent.status)}
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                    {agent.status}
                  </span>
                </div>
              </div>
              <div className="mt-4">
                <a
                  href={agent.href}
                  className="text-sm font-medium text-primary-400 hover:text-primary-300"
                >
                  Open {agent.name} →
                </a>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* System Information */}
      {systemStats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-dark-surface shadow rounded-lg border border-dark-border"
        >
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              System Status
            </h3>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Health Status</dt>
                <dd className="mt-1 text-sm text-dark-text">
                  {systemStats.health?.status || 'Unknown'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Readiness</dt>
                <dd className="mt-1 text-sm text-dark-text">
                  {systemStats.ready?.ready ? 'Ready' : 'Not Ready'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Version</dt>
                <dd className="mt-1 text-sm text-dark-text">
                  {systemStats.health?.version || 'Unknown'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Timestamp</dt>
                <dd className="mt-1 text-sm text-dark-text">
                  {new Date(systemStats.health?.timestamp).toLocaleString()}
                </dd>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default Dashboard;
