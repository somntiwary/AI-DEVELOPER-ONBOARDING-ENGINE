import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import useAgentState from '../hooks/useAgentState';
import {
  FileText,
  Search,
  Download,
  Upload,
  RefreshCw,
  CheckCircle,
  Activity,
  Database
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const Documentation = () => {
  const { 
    currentProject, 
    loading, 
    apiCall, 
    addNotification 
  } = useApp();
  
  // Use persistent agent state from context
  const agentState = useAgentState('documentation');
  const documentationData = agentState.state.documentationData;
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [selectedTab, setSelectedTab] = useState('generate');
  const [projectPath, setProjectPath] = useState('');
  const [query, setQuery] = useState('');
  const [queryResult, setQueryResult] = useState(null);

  useEffect(() => {
    if (currentProject) {
      setProjectPath(currentProject.path);
    }
  }, [currentProject]);

  const tabs = [
    { id: 'generate', name: 'Generate Docs', icon: FileText },
    { id: 'query', name: 'Query Docs', icon: Search },
    { id: 'ingest', name: 'Ingest Docs', icon: Upload },
    { id: 'reset', name: 'Reset Schema', icon: RefreshCw }
  ];

  const handleGenerateDocs = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsGenerating(true);
    try {
      const result = await apiCall('/api/documentation/generate', 'POST', {
        project_path: projectPath
      });
      
      agentState.updateStateField('documentationData', result);
      agentState.updateStateField('data', result);
      agentState.updateStateField('initialized', true);
      
      addNotification({ 
        message: 'Documentation generated successfully' 
      });
      
    } catch (error) {
      console.error('Documentation generation failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleQueryDocs = async () => {
    if (!projectPath.trim() || !query.trim()) {
      addNotification({ message: 'Please enter both project path and query' });
      return;
    }

    setIsQuerying(true);
    try {
      const result = await apiCall('/api/documentation/query', 'POST', {
        project_path: projectPath,
        question: query
      });
      
      setQueryResult(result);
      
      addNotification({ 
        message: 'Documentation query completed successfully' 
      });
      
    } catch (error) {
      console.error('Documentation query failed:', error);
    } finally {
      setIsQuerying(false);
    }
  };

  const handleIngestDocs = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsIngesting(true);
    try {
      const result = await apiCall('/api/documentation/ingest', 'POST', {
        project_path: projectPath
      });
      
      const updatedData = { ...documentationData, ingestResult: result };
      agentState.updateStateField('documentationData', updatedData);
      
      addNotification({ 
        message: `Successfully ingested ${result.chunks_ingested} documentation chunks` 
      });
      
    } catch (error) {
      console.error('Documentation ingestion failed:', error);
    } finally {
      setIsIngesting(false);
    }
  };

  const handleResetSchema = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    try {
      const result = await apiCall('/api/documentation/reset', 'POST', {
        project_path: projectPath
      });
      
      const updatedData = { ...documentationData, resetResult: result };
      agentState.updateStateField('documentationData', updatedData);
      
      addNotification({ 
        message: 'Documentation schema reset successfully' 
      });
      
    } catch (error) {
      console.error('Schema reset failed:', error);
    }
  };

  const handleDownloadFile = async (fileType) => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    try {
      setIsDownloading(true);
      
      // Fetch the file as a blob
      const response = await fetch(
        `http://localhost:8000/api/documentation/download/${fileType}?project_path=${encodeURIComponent(projectPath)}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to download file' }));
        throw new Error(errorData.detail || 'Download failed');
      }

      // Get the blob and create a download link
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileType === 'readme' ? 'README_AUTO.md' : 'API_DOCUMENTATION.md';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      addNotification({ 
        message: `${fileType === 'readme' ? 'README' : 'API Documentation'} downloaded successfully` 
      });
      
    } catch (error) {
      console.error('Download failed:', error);
      addNotification({ 
        message: error.message || 'Download failed. Please try again.', 
        type: 'error' 
      });
    } finally {
      setIsDownloading(false);
    }
  };

  const renderGenerateDocs = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Generate Documentation
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Generate comprehensive README and API documentation for your project.
          </p>
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
            <button
              onClick={handleGenerateDocs}
              disabled={isGenerating || loading}
              className="btn btn-primary px-4 py-2"
            >
              {isGenerating ? (
                <>
                  <Activity className="animate-spin h-4 w-4 mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  <FileText className="h-4 w-4 mr-2" />
                  Generate
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {documentationData && (
        <div className="space-y-6">
          {documentationData.readme_path && (
            <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                  Generated README
                </h3>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm text-dark-text-secondary">
                    Path: {documentationData.readme_path}
                  </span>
                  <button 
                    className="btn btn-secondary px-3 py-1 text-sm"
                    onClick={() => handleDownloadFile('readme')}
                    disabled={isDownloading || loading}
                  >
                    {isDownloading ? (
                      <>
                        <Activity className="h-4 w-4 mr-1 animate-spin" />
                        Downloading...
                      </>
                    ) : (
                      <>
                        <Download className="h-4 w-4 mr-1" />
                        Download
                      </>
                    )}
                  </button>
                </div>
                <div className="bg-dark-accent rounded-lg p-4">
                  <div className="text-sm text-dark-text-secondary">
                    README file generated successfully. Click download to view the content.
                  </div>
                </div>
              </div>
            </div>
          )}

          {documentationData.api_docs_path && (
            <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                  Generated API Documentation
                </h3>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm text-dark-text-secondary">
                    Path: {documentationData.api_docs_path}
                  </span>
                  <button 
                    className="btn btn-secondary px-3 py-1 text-sm"
                    onClick={() => handleDownloadFile('api_docs')}
                    disabled={isDownloading || loading}
                  >
                    {isDownloading ? (
                      <>
                        <Activity className="h-4 w-4 mr-1 animate-spin" />
                        Downloading...
                      </>
                    ) : (
                      <>
                        <Download className="h-4 w-4 mr-1" />
                        Download
                      </>
                    )}
                  </button>
                </div>
                <div className="bg-dark-accent rounded-lg p-4">
                  <div className="text-sm text-dark-text-secondary">
                    API documentation generated successfully. Click download to view the content.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderQueryDocs = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Query Documentation
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Ask questions about your project's documentation using RAG or LLM.
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-text-secondary mb-2">
                Project Path
              </label>
              <input
                type="text"
                className="input"
                placeholder="Enter project path"
                value={projectPath}
                onChange={(e) => setProjectPath(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text-secondary mb-2">
                Question
              </label>
              <textarea
                className="input min-h-[100px]"
                placeholder="Ask a question about your project..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <button
              onClick={handleQueryDocs}
              disabled={isQuerying || loading}
              className="btn btn-primary px-4 py-2"
            >
              {isQuerying ? (
                <>
                  <Activity className="animate-spin h-4 w-4 mr-2" />
                  Querying...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Query
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {queryResult && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Query Result
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Question</h4>
                <p className="text-sm text-dark-text bg-dark-accent rounded-md p-3">
                  {queryResult.question}
                </p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Answer</h4>
                <div className="bg-dark-accent rounded-md p-4">
                  <ReactMarkdown className="prose prose-sm max-w-none prose-invert">
                    {queryResult.answer}
                  </ReactMarkdown>
                </div>
              </div>
              {queryResult.sources && queryResult.sources.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Sources</h4>
                  <div className="space-y-2">
                    {queryResult.sources.map((source, index) => (
                      <div key={index} className="bg-blue-900/20 border border-blue-800 rounded-md p-2">
                        <span className="text-sm text-blue-300">{source}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderIngestDocs = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Ingest Documentation
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Ingest project documentation into Weaviate for RAG queries.
          </p>
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
            <button
              onClick={handleIngestDocs}
              disabled={isIngesting || loading}
              className="btn btn-primary px-4 py-2"
            >
              {isIngesting ? (
                <>
                  <Activity className="animate-spin h-4 w-4 mr-2" />
                  Ingesting...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Ingest
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {documentationData?.ingestResult && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Ingestion Results
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                  <span className="text-sm font-medium text-green-800">Chunks Ingested</span>
                </div>
                <p className="text-2xl font-bold text-green-900 mt-1">
                  {documentationData.ingestResult.chunks_ingested}
                </p>
              </div>
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center">
                  <FileText className="h-5 w-5 text-blue-500 mr-2" />
                  <span className="text-sm font-medium text-blue-800">Files Processed</span>
                </div>
                <p className="text-2xl font-bold text-blue-900 mt-1">
                  {documentationData.ingestResult.files_processed}
                </p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center">
                  <Database className="h-5 w-5 text-purple-500 mr-2" />
                  <span className="text-sm font-medium text-purple-800">Status</span>
                </div>
                <p className="text-sm font-bold text-purple-900 mt-1">
                  {documentationData.ingestResult.status}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderResetSchema = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Reset Documentation Schema
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Clear existing DocsChunk class and data. Use this if you encounter schema conflicts.
          </p>
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
            <button
              onClick={handleResetSchema}
              disabled={loading}
              className="btn btn-secondary px-4 py-2"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Reset Schema
            </button>
          </div>
        </div>
      </div>

      {documentationData?.resetResult && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Reset Results
            </h3>
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <div className="flex">
                <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
                <div>
                  <h4 className="text-sm font-medium text-green-800">Schema Reset Successful</h4>
                  <p className="text-sm text-green-700 mt-1">
                    {documentationData.resetResult.message}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-dark-text sm:text-3xl sm:truncate">
            Documentation
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Generate docs and RAG-based knowledge queries
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedTab(tab.id)}
              className={`${
                selectedTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-dark-text-secondary hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center`}
            >
              <tab.icon className="h-4 w-4 mr-2" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <motion.div
        key={selectedTab}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.2 }}
      >
        {selectedTab === 'generate' && renderGenerateDocs()}
        {selectedTab === 'query' && renderQueryDocs()}
        {selectedTab === 'ingest' && renderIngestDocs()}
        {selectedTab === 'reset' && renderResetSchema()}
      </motion.div>
    </div>
  );
};

export default Documentation;
