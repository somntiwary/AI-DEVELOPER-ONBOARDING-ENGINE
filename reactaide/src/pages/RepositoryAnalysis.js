import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import useAgentState from '../hooks/useAgentState';
import {
  GitBranch,
  FileText,
  Code,
  Package,
  Activity,
  CheckCircle,
  Clock,
  BarChart3,
  Layers,
  Zap
} from 'lucide-react';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';

const RepositoryAnalysis = () => {
  const { 
    loading, 
    apiCall, 
    addNotification 
  } = useApp();
  
  // Use persistent agent state from context
  const agentState = useAgentState('repository');
  const analysisData = agentState.state.analysisData;
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [repoUrl, setRepoUrl] = useState('');
  const [showAllFiles, setShowAllFiles] = useState(false);
  const [fileSearchTerm, setFileSearchTerm] = useState('');
  const [folderSearchTerm, setFolderSearchTerm] = useState('');

  // Reset search terms when switching tabs
  useEffect(() => {
    if (selectedTab !== 'structure') {
      setFileSearchTerm('');
      setFolderSearchTerm('');
      setShowAllFiles(false);
    }
  }, [selectedTab]);

  const handleAnalyze = async () => {
    if (!repoUrl.trim()) {
      addNotification({ message: 'Please enter a repository URL' });
      return;
    }

    setIsAnalyzing(true);
    try {
      const result = await apiCall('/api/repo/analyze', 'POST', {
        repo_url: repoUrl
      });
      
      agentState.updateStateField('analysisData', result);
      agentState.updateStateField('data', result);
      agentState.updateStateField('initialized', true);
      
      addNotification({ 
        message: `Repository analysis completed: ${result.stats.files_scanned} files processed` 
      });
      
    } catch (error) {
      console.error('Repository analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: BarChart3 },
    { id: 'structure', name: 'Structure', icon: Layers },
    { id: 'dependencies', name: 'Dependencies', icon: Package },
    { id: 'frameworks', name: 'Frameworks', icon: Code },
    { id: 'ci', name: 'CI/CD', icon: Activity }
  ];

  const StatCard = ({ title, value, icon: Icon, color = 'blue' }) => (
    <div className="bg-dark-surface overflow-hidden shadow rounded-lg border border-dark-border">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <Icon className={`h-8 w-8 text-${color}-500`} />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-dark-text-secondary truncate">{title}</dt>
              <dd className="text-lg font-medium text-dark-text">{value}</dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );

  const renderOverview = () => {
    if (!analysisData) return null;

    const { stats } = analysisData;

    return (
      <div className="space-y-6">
        {/* Statistics */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Files Scanned"
            value={stats.files_scanned}
            icon={FileText}
            color="blue"
          />
          <StatCard
            title="Files Parsed"
            value={stats.files_parsed}
            icon={CheckCircle}
            color="green"
          />
          <StatCard
            title="Files Embedded"
            value={stats.files_embedded}
            icon={Zap}
            color="purple"
          />
          <StatCard
            title="Processing Time"
            value={`${analysisData.processing_time_seconds?.toFixed(2)}s`}
            icon={Clock}
            color="orange"
          />
        </div>

        {/* Repository Information */}
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Repository Information
            </h3>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Repository URL</dt>
                <dd className="mt-1 text-sm text-dark-text">{analysisData.repo_url}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Local Path</dt>
                <dd className="mt-1 text-sm text-dark-text">{analysisData.repo_path || 'N/A'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Weaviate Enabled</dt>
                <dd className="mt-1 text-sm text-dark-text">
                  {analysisData.weaviate_enabled ? 'Yes' : 'No'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Success</dt>
                <dd className="mt-1 text-sm text-dark-text">
                  {analysisData.success ? 'Yes' : 'No'}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Parse Engines */}
        {stats.parse_engines_used && Object.keys(stats.parse_engines_used).length > 0 && (
          <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                Parse Engines Used
              </h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {Object.entries(stats.parse_engines_used).map(([engine, count]) => (
                  <div key={engine} className="bg-dark-accent rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-dark-text">{engine}</span>
                      <span className="text-sm text-dark-text-secondary">{count} files</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Errors and Skipped Files */}
        {(stats.errors.length > 0 || stats.skipped_files.length > 0) && (
          <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                Issues Found
              </h3>
              {stats.errors.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-red-600 mb-2">Errors ({stats.errors.length})</h4>
                  <div className="space-y-2">
                    {stats.errors.slice(0, 5).map((error, index) => (
                      <div key={index} className="bg-red-900/20 border border-red-800 rounded-md p-3">
                        <p className="text-sm text-red-300">{error.message || 'Unknown error'}</p>
                        {error.file && (
                          <p className="text-xs text-red-600 mt-1">File: {error.file}</p>
                        )}
                      </div>
                    ))}
                    {stats.errors.length > 5 && (
                      <p className="text-sm text-dark-text-secondary">... and {stats.errors.length - 5} more errors</p>
                    )}
                  </div>
                </div>
              )}
              {stats.skipped_files.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-yellow-600 mb-2">Skipped Files ({stats.skipped_files.length})</h4>
                  <div className="space-y-2">
                    {stats.skipped_files.slice(0, 5).map((file, index) => (
                      <div key={index} className="bg-yellow-900/20 border border-yellow-800 rounded-md p-3">
                        <p className="text-sm text-yellow-300">{file.file || 'Unknown file'}</p>
                        {file.reason && (
                          <p className="text-xs text-yellow-600 mt-1">Reason: {file.reason}</p>
                        )}
                      </div>
                    ))}
                    {stats.skipped_files.length > 5 && (
                      <p className="text-sm text-dark-text-secondary">... and {stats.skipped_files.length - 5} more files</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderStructure = () => {
    if (!analysisData?.structure) return null;

    const { structure } = analysisData;

    // Filter files and folders based on search terms
    const filteredFiles = structure.files.filter(file => 
      file.toLowerCase().includes(fileSearchTerm.toLowerCase())
    );
    const filteredFolders = structure.folders.filter(folder => 
      folder.toLowerCase().includes(folderSearchTerm.toLowerCase())
    );

    // Determine how many files to show
    const filesToShow = showAllFiles ? filteredFiles : filteredFiles.slice(0, 50);

    return (
      <div className="space-y-6">
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Repository Structure
            </h3>
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Root Directory</h4>
                <div className="bg-dark-accent rounded-md p-3 overflow-x-auto">
                  <span className="text-sm text-dark-text font-mono whitespace-nowrap">{structure.root}</span>
                </div>
              </div>
              
              {structure.folders.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-dark-text-secondary">Folders ({filteredFolders.length})</h4>
                    {structure.folders.length > 10 && (
                      <div className="flex-1 max-w-xs ml-4">
                        <input
                          type="text"
                          placeholder="Search folders..."
                          className="w-full text-xs input"
                          value={folderSearchTerm}
                          onChange={(e) => setFolderSearchTerm(e.target.value)}
                        />
                      </div>
                    )}
                  </div>
                  <div className="max-h-60 overflow-y-auto shadow rounded-lg border border-dark-border rounded-md">
                    <div className="grid grid-cols-1 gap-1 p-2">
                      {filteredFolders.map((folder, index) => (
                        <div key={index} className="bg-dark-accent hover:bg-dark-border rounded-md p-2 transition-colors">
                          <div className="flex items-center">
                            <Layers className="h-4 w-4 text-gray-400 mr-2 flex-shrink-0" />
                            <span className="text-sm text-dark-text font-mono truncate" title={folder}>
                              {folder}
                            </span>
                          </div>
                        </div>
                      ))}
                      {filteredFolders.length === 0 && folderSearchTerm && (
                        <div className="text-center py-4 text-dark-text-secondary text-sm">
                          No folders found matching "{folderSearchTerm}"
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {structure.files.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-dark-text-secondary">Files ({filteredFiles.length})</h4>
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 max-w-xs">
                        <input
                          type="text"
                          placeholder="Search files..."
                          className="w-full text-xs input"
                          value={fileSearchTerm}
                          onChange={(e) => setFileSearchTerm(e.target.value)}
                        />
                      </div>
                      {filteredFiles.length > 50 && (
                        <button
                          onClick={() => setShowAllFiles(!showAllFiles)}
                          className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                        >
                          {showAllFiles ? 'Show Less' : `Show All (${filteredFiles.length})`}
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="max-h-96 overflow-y-auto shadow rounded-lg border border-dark-border rounded-md">
                    <div className="grid grid-cols-1 gap-1 p-2">
                      {filesToShow.map((file, index) => {
                        const fileExtension = file.split('.').pop()?.toLowerCase();
                        const getFileIcon = (ext) => {
                          switch (ext) {
                            case 'js': case 'jsx': case 'ts': case 'tsx': return 'text-yellow-600';
                            case 'py': return 'text-green-600';
                            case 'java': return 'text-red-600';
                            case 'css': case 'scss': return 'text-blue-600';
                            case 'html': case 'htm': return 'text-orange-600';
                            case 'json': case 'xml': case 'yaml': case 'yml': return 'text-purple-600';
                            case 'md': case 'txt': return 'text-dark-text-secondary';
                            default: return 'text-dark-text-secondary';
                          }
                        };
                        
                        return (
                          <div key={index} className="bg-dark-accent hover:bg-dark-border rounded-md p-2 transition-colors">
                            <div className="flex items-center">
                              <FileText className={`h-4 w-4 ${getFileIcon(fileExtension)} mr-2 flex-shrink-0`} />
                              <span 
                                className="text-sm text-dark-text font-mono truncate flex-1" 
                                title={file}
                              >
                                {file}
                              </span>
                              {fileExtension && (
                                <span className="text-xs text-gray-400 ml-2 flex-shrink-0">
                                  .{fileExtension}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                      {filteredFiles.length === 0 && fileSearchTerm && (
                        <div className="text-center py-4 text-dark-text-secondary text-sm">
                          No files found matching "{fileSearchTerm}"
                        </div>
                      )}
                      {!showAllFiles && filteredFiles.length > 50 && (
                        <div className="bg-gray-100 rounded-md p-3 text-center">
                          <span className="text-sm text-dark-text-secondary">
                            Showing 50 of {filteredFiles.length} files. 
                            <button
                              onClick={() => setShowAllFiles(true)}
                              className="text-primary-600 hover:text-primary-800 font-medium ml-1"
                            >
                              Show all
                            </button>
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {structure.main_modules.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Main Modules ({structure.main_modules.length})</h4>
                  <div className="max-h-40 overflow-y-auto shadow rounded-lg border border-dark-border rounded-md">
                    <div className="grid grid-cols-1 gap-1 p-2">
                      {structure.main_modules.map((module, index) => (
                        <div key={index} className="bg-blue-900/20 hover:bg-blue-800/30 border border-blue-800 rounded-md p-2 transition-colors">
                          <div className="flex items-center">
                            <Code className="h-4 w-4 text-blue-600 mr-2 flex-shrink-0" />
                            <span className="text-sm text-blue-300 font-mono truncate" title={module}>
                              {module}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderDependencies = () => {
    if (!analysisData?.dependencies) return null;

    const { dependencies } = analysisData;

    return (
      <div className="space-y-6">
        {dependencies.requirements.length > 0 && (
          <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                Python Requirements ({dependencies.requirements.length})
              </h3>
              <div className="space-y-2">
                {dependencies.requirements.map((req, index) => (
                  <div key={index} className="bg-dark-accent rounded-md p-3">
                    <span className="text-sm text-dark-text font-mono">{req}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {dependencies.package_json && Object.keys(dependencies.package_json).length > 0 && (
          <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                Node.js Dependencies
              </h3>
              <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                <SyntaxHighlighter
                  language="json"
                  style={docco}
                  customStyle={{ margin: 0, fontSize: '14px' }}
                >
                  {JSON.stringify(dependencies.package_json, null, 2)}
                </SyntaxHighlighter>
              </div>
            </div>
          </div>
        )}

        {dependencies.pom_xml && Object.keys(dependencies.pom_xml).length > 0 && (
          <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                Java Dependencies (Maven)
              </h3>
              <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                <SyntaxHighlighter
                  language="json"
                  style={docco}
                  customStyle={{ margin: 0, fontSize: '14px' }}
                >
                  {JSON.stringify(dependencies.pom_xml, null, 2)}
                </SyntaxHighlighter>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderFrameworks = () => {
    if (!analysisData?.frameworks) return null;

    const { frameworks } = analysisData;

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          {frameworks.python_frameworks.length > 0 && (
            <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                  Python Frameworks
                </h3>
                <div className="space-y-2">
                  {frameworks.python_frameworks.map((framework, index) => (
                    <div key={index} className="bg-green-900/20 border border-green-800 rounded-md p-2">
                      <span className="text-sm text-green-300">{framework}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {frameworks.js_frameworks.length > 0 && (
            <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                  JavaScript Frameworks
                </h3>
                <div className="space-y-2">
                  {frameworks.js_frameworks.map((framework, index) => (
                    <div key={index} className="bg-yellow-900/20 border border-yellow-800 rounded-md p-2">
                      <span className="text-sm text-yellow-300">{framework}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {frameworks.java_frameworks.length > 0 && (
            <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                  Java Frameworks
                </h3>
                <div className="space-y-2">
                  {frameworks.java_frameworks.map((framework, index) => (
                    <div key={index} className="bg-blue-900/20 border border-blue-800 rounded-md p-2">
                      <span className="text-sm text-blue-300">{framework}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderCI = () => {
    if (!analysisData?.ci) return null;

    const { ci } = analysisData;

    return (
      <div className="space-y-6">
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              CI/CD Information
            </h3>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Has Tests</dt>
                <dd className="mt-1 text-sm text-dark-text">
                  {ci.has_tests ? 'Yes' : 'No'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Test Paths</dt>
                <dd className="mt-1 text-sm text-dark-text">
                  {ci.test_paths.length} found
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">CI Files</dt>
                <dd className="mt-1 text-sm text-dark-text">
                  {ci.ci_files.length} found
                </dd>
              </div>
            </dl>
            
            {ci.test_paths.length > 0 && (
              <div className="mt-6">
                <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Test Paths</h4>
                <div className="max-h-40 overflow-y-auto shadow rounded-lg border border-dark-border rounded-md">
                  <div className="space-y-1 p-2">
                    {ci.test_paths.map((path, index) => (
                      <div key={index} className="bg-dark-accent hover:bg-dark-border rounded-md p-2 transition-colors">
                        <div className="flex items-center">
                          <Activity className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                          <span className="text-sm text-dark-text font-mono truncate" title={path}>
                            {path}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            {ci.ci_files.length > 0 && (
              <div className="mt-6">
                <h4 className="text-sm font-medium text-dark-text-secondary mb-2">CI Files</h4>
                <div className="max-h-40 overflow-y-auto shadow rounded-lg border border-dark-border rounded-md">
                  <div className="space-y-1 p-2">
                    {ci.ci_files.map((file, index) => (
                      <div key={index} className="bg-dark-accent hover:bg-dark-border rounded-md p-2 transition-colors">
                        <div className="flex items-center">
                          <FileText className="h-4 w-4 text-blue-500 mr-2 flex-shrink-0" />
                          <span className="text-sm text-dark-text font-mono truncate" title={file}>
                            {file}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
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
            Repository Analysis
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Analyze code structure, dependencies, and frameworks
          </p>
        </div>
      </div>

      {/* Analysis Form */}
      {!analysisData && !agentState.state.initialized && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-dark-surface shadow rounded-lg border border-dark-border"
        >
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Analyze Repository
            </h3>
            <div className="flex space-x-4">
              <div className="flex-1">
                <label htmlFor="repo-url" className="block text-sm font-medium text-dark-text-secondary">
                  Repository URL
                </label>
                <input
                  type="text"
                  id="repo-url"
                  className="input mt-1"
                  placeholder="https://github.com/owner/repo"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || loading}
                  className="btn btn-primary px-4 py-2"
                >
                  {isAnalyzing ? (
                    <>
                      <Activity className="animate-spin h-4 w-4 mr-2" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <GitBranch className="h-4 w-4 mr-2" />
                      Analyze
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Analysis Results */}
      {(analysisData || agentState.state.initialized) && (
        <>
          {/* Tabs */}
          <div className="border-b border-dark-border">
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
            {selectedTab === 'overview' && renderOverview()}
            {selectedTab === 'structure' && renderStructure()}
            {selectedTab === 'dependencies' && renderDependencies()}
            {selectedTab === 'frameworks' && renderFrameworks()}
            {selectedTab === 'ci' && renderCI()}
          </motion.div>
        </>
      )}
    </div>
  );
};

export default RepositoryAnalysis;
