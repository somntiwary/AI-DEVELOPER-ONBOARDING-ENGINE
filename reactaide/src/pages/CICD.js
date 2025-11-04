import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import useAgentState from '../hooks/useAgentState';
import {
  Workflow,
  Github,
  Settings,
  Activity,
  CheckCircle,
  AlertCircle,
  Clock,
  Play,
  BarChart3,
  Code
} from 'lucide-react';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';

const CICD = () => {
  const { 
    currentProject, 
    loading, 
    apiCall, 
    addNotification 
  } = useApp();
  
  // Use persistent agent state from context
  const agentState = useAgentState('cicd');
  const cicdData = agentState.state.cicdData;
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);
  const [isDiagnosing, setIsDiagnosing] = useState(false);
  const [selectedTab, setSelectedTab] = useState('github');
  const [projectPath, setProjectPath] = useState('');
  const [diagnosticsLog, setDiagnosticsLog] = useState('');
  const [cicdType, setCicdType] = useState('GitHub Actions');
  
  // GitHub trigger credentials
  const [githubRepo, setGithubRepo] = useState('');
  const [githubToken, setGithubToken] = useState('');
  const [workflowFile, setWorkflowFile] = useState('');
  const [branch, setBranch] = useState('main');
  
  // Jenkins trigger credentials
  const [jenkinsUrl, setJenkinsUrl] = useState('');
  const [jenkinsUser, setJenkinsUser] = useState('');
  const [jenkinsToken, setJenkinsToken] = useState('');
  const [jenkinsJob, setJenkinsJob] = useState('');

  useEffect(() => {
    if (currentProject) {
      setProjectPath(currentProject.path);
    }
  }, [currentProject]);

  const tabs = [
    { id: 'github', name: 'GitHub Actions', icon: Github },
    { id: 'jenkins', name: 'Jenkins', icon: Settings },
    { id: 'diagnose', name: 'Diagnose', icon: Activity },
    { id: 'validate', name: 'Validate', icon: CheckCircle }
  ];

  const handleAnalyzeGitHub = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsAnalyzing(true);
    try {
      const result = await apiCall('/api/ci-cd/github/workflows', 'POST', {
        project_path: projectPath
      });
      
      const updatedData = { ...cicdData, githubWorkflows: result };
      agentState.updateStateField('cicdData', updatedData);
      
      addNotification({ 
        message: `Found ${result.workflows?.length || 0} GitHub workflows` 
      });
      
    } catch (error) {
      console.error('GitHub analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleExplainGitHub = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    try {
      const result = await apiCall('/api/ci-cd/github/workflow/explain', 'POST', {
        project_path: projectPath
      });
      
      const updatedData = { ...cicdData, githubExplanations: result };
      agentState.updateStateField('cicdData', updatedData);
      
      addNotification({ 
        message: 'GitHub workflow explanations generated' 
      });
      
    } catch (error) {
      console.error('GitHub explanation failed:', error);
    }
  };

  const handleTriggerGitHub = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    if (!githubRepo.trim() || !githubToken.trim() || !workflowFile.trim()) {
      addNotification({ 
        message: 'Please enter repository (owner/repo), GitHub token, and workflow file name',
        type: 'error'
      });
      return;
    }

    setIsTriggering(true);
    try {
      const result = await apiCall('/api/ci-cd/github/trigger', 'POST', {
        project_path: projectPath,
        repo: githubRepo,
        token: githubToken,
        workflow_file: workflowFile,
        branch: branch
      });
      
      const updatedData = { ...cicdData, githubTrigger: result };
      agentState.updateStateField('cicdData', updatedData);
      
      addNotification({ 
        message: 'GitHub workflow triggered successfully' 
      });
      
    } catch (error) {
      console.error('GitHub trigger failed:', error);
      addNotification({ 
        message: 'Failed to trigger workflow. Check your credentials and workflow settings.',
        type: 'error'
      });
    } finally {
      setIsTriggering(false);
    }
  };

  const handleAnalyzeJenkins = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsAnalyzing(true);
    try {
      const result = await apiCall('/api/ci-cd/jenkins/analyze', 'POST', {
        project_path: projectPath
      });
      
      const updatedData = { ...cicdData, jenkinsAnalysis: result };
      agentState.updateStateField('cicdData', updatedData);
      
      addNotification({ 
        message: 'Jenkins pipeline analyzed successfully' 
      });
      
    } catch (error) {
      console.error('Jenkins analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleTriggerJenkins = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    if (!jenkinsUrl.trim() || !jenkinsUser.trim() || !jenkinsToken.trim() || !jenkinsJob.trim()) {
      addNotification({ 
        message: 'Please enter Jenkins server URL, username, API token, and job name',
        type: 'error'
      });
      return;
    }

    setIsTriggering(true);
    try {
      const result = await apiCall('/api/ci-cd/jenkins/trigger', 'POST', {
        project_path: projectPath,
        base_url: jenkinsUrl,
        username: jenkinsUser,
        api_token: jenkinsToken,
        job_name: jenkinsJob
      });
      
      const updatedData = { ...cicdData, jenkinsTrigger: result };
      agentState.updateStateField('cicdData', updatedData);
      
      addNotification({ 
        message: 'Jenkins job triggered successfully' 
      });
      
    } catch (error) {
      console.error('Jenkins trigger failed:', error);
      addNotification({ 
        message: 'Failed to trigger Jenkins job. Check your credentials.',
        type: 'error'
      });
    } finally {
      setIsTriggering(false);
    }
  };

  const handleDiagnose = async () => {
    if (!projectPath.trim() || !diagnosticsLog.trim()) {
      addNotification({ message: 'Please enter both project path and log content' });
      return;
    }

    setIsDiagnosing(true);
    try {
      const result = await apiCall('/api/ci-cd/diagnose', 'POST', {
        project_path: projectPath,
        log_content: diagnosticsLog,
        ci_type: cicdType
      });
      
      const updatedData = { ...cicdData, diagnosis: result };
      agentState.updateStateField('cicdData', updatedData);
      
      addNotification({ 
        message: 'CI/CD failure diagnosis completed' 
      });
      
    } catch (error) {
      console.error('Diagnosis failed:', error);
    } finally {
      setIsDiagnosing(false);
    }
  };

  const handleValidate = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    try {
      const result = await apiCall('/api/ci-cd/validate', 'POST', {
        project_path: projectPath,
        run_environment_checks: true
      });
      
      const updatedData = { ...cicdData, validation: result };
      agentState.updateStateField('cicdData', updatedData);
      
      addNotification({ 
        message: 'CI/CD validation completed' 
      });
      
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const renderGitHub = () => (
    <div className="space-y-6">
      {/* Information Box */}
      <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-4">
        <div className="flex">
          <AlertCircle className="h-5 w-5 text-blue-400 mr-2 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-medium text-blue-300">Understanding the Buttons</h4>
            <ul className="text-sm text-blue-200 mt-2 space-y-1 list-disc list-inside">
              <li><strong>Analyze:</strong> Scans your project and finds GitHub workflows (.github/workflows/*.yml)</li>
              <li><strong>Explain Workflow:</strong> Generates human-readable explanation of what each workflow does</li>
              <li><strong>Trigger Workflow:</strong> Manually runs a GitHub Actions workflow (requires GitHub token & workflow must have workflow_dispatch trigger)</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            GitHub Actions Analysis
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Analyze GitHub Actions workflows in your repository.
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
              onClick={handleAnalyzeGitHub}
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
                  <Github className="h-4 w-4 mr-2" />
                  Analyze
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {cicdData?.githubWorkflows && (
        <div className="space-y-6">
          <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                GitHub Workflows
              </h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="bg-blue-900/20 rounded-lg p-4">
                  <div className="flex items-center">
                    <Workflow className="h-5 w-5 text-blue-400 mr-2" />
                    <span className="text-sm font-medium text-blue-300">Workflows Found</span>
                  </div>
                  <p className="text-2xl font-bold text-blue-200 mt-1">
                    {cicdData.githubWorkflows.workflow_count || 0}
                  </p>
                </div>
                <div className="bg-green-900/20 rounded-lg p-4">
                  <div className="flex items-center">
                    <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
                    <span className="text-sm font-medium text-green-300">Status</span>
                  </div>
                  <p className="text-sm font-bold text-green-200 mt-1">
                    {cicdData.githubWorkflows.status}
                  </p>
                </div>
                <div className="bg-purple-900/20 rounded-lg p-4">
                  <div className="flex items-center">
                    <Clock className="h-5 w-5 text-purple-400 mr-2" />
                    <span className="text-sm font-medium text-purple-300">Cache</span>
                  </div>
                  <p className="text-sm font-bold text-purple-200 mt-1">
                    {cicdData.githubWorkflows.metadata?.cache_status || 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {cicdData.githubWorkflows.workflows && (
            <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                  Workflow Details
                </h3>
                <div className="space-y-4">
                  {cicdData.githubWorkflows.workflows.map((workflow, index) => (
                    <div key={index} className="border border-dark-border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-dark-text">
                          {workflow.name || `Workflow ${index + 1}`}
                        </h4>
                        <button
                          onClick={handleExplainGitHub}
                          className="btn btn-secondary px-3 py-1 text-sm"
                        >
                          <Code className="h-4 w-4 mr-1" />
                          Explain
                        </button>
                      </div>
                      {workflow.content && (
                        <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                          <SyntaxHighlighter
                            language="yaml"
                            style={docco}
                            customStyle={{ margin: 0, fontSize: '14px' }}
                          >
                            {workflow.content}
                          </SyntaxHighlighter>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="bg-dark-surface shadow rounded-lg border border-dark-border p-4">
            <h3 className="text-sm font-medium text-dark-text mb-4">
              Trigger GitHub Workflow
            </h3>
            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-dark-text-secondary mb-1">Repository (owner/repo)</label>
                  <input
                    type="text"
                    className="input text-sm"
                    placeholder="username/repo-name"
                    value={githubRepo}
                    onChange={(e) => setGithubRepo(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark-text-secondary mb-1">GitHub Token</label>
                  <input
                    type="password"
                    className="input text-sm"
                    placeholder="ghp_xxxxx"
                    value={githubToken}
                    onChange={(e) => setGithubToken(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark-text-secondary mb-1">Workflow File</label>
                  <input
                    type="text"
                    className="input text-sm"
                    placeholder="ci.yml"
                    value={workflowFile}
                    onChange={(e) => setWorkflowFile(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark-text-secondary mb-1">Branch</label>
                  <input
                    type="text"
                    className="input text-sm"
                    placeholder="main"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleExplainGitHub}
                  disabled={loading}
                  className="btn btn-secondary px-4 py-2"
                >
                  <Code className="h-4 w-4 mr-2" />
                  Explain Workflows
                </button>
                <button
                  onClick={handleTriggerGitHub}
                  disabled={isTriggering || loading}
                  className="btn btn-primary px-4 py-2"
                >
                  {isTriggering ? (
                    <>
                      <Activity className="animate-spin h-4 w-4 mr-2" />
                      Triggering...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Trigger Workflow
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderJenkins = () => (
    <div className="space-y-6">
      {/* Information Box */}
      <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-4">
        <div className="flex">
          <AlertCircle className="h-5 w-5 text-blue-400 mr-2 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-medium text-blue-300">Understanding Jenkins</h4>
            <ul className="text-sm text-blue-200 mt-2 space-y-1 list-disc list-inside">
              <li><strong>Analyze:</strong> Parses Jenkinsfile and extracts stages, steps, and environment variables</li>
              <li><strong>Trigger Job:</strong> Manually starts a Jenkins job build (requires Jenkins server URL and API token)</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Jenkins Pipeline Analysis
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Analyze Jenkins pipeline configuration.
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
              onClick={handleAnalyzeJenkins}
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
                  <Settings className="h-4 w-4 mr-2" />
                  Analyze
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {cicdData?.jenkinsAnalysis && (
        <div className="space-y-6">
          <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
                Jenkins Analysis Results
              </h3>
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Summary</h4>
                  <div className="bg-dark-accent rounded-md p-3">
                    <pre className="text-sm text-dark-text whitespace-pre-wrap">
                      {JSON.stringify(cicdData.jenkinsAnalysis.summary, null, 2)}
                    </pre>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Explanation</h4>
                  <div className="bg-blue-900/20 rounded-md p-3">
                    <p className="text-sm text-blue-300">
                      {cicdData.jenkinsAnalysis.explanation}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-dark-surface shadow rounded-lg border border-dark-border p-4">
            <h3 className="text-sm font-medium text-dark-text mb-4">
              Trigger Jenkins Job
            </h3>
            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-dark-text-secondary mb-1">Jenkins URL</label>
                  <input
                    type="text"
                    className="input text-sm"
                    placeholder="http://jenkins.example.com"
                    value={jenkinsUrl}
                    onChange={(e) => setJenkinsUrl(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark-text-secondary mb-1">Username</label>
                  <input
                    type="text"
                    className="input text-sm"
                    placeholder="admin"
                    value={jenkinsUser}
                    onChange={(e) => setJenkinsUser(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark-text-secondary mb-1">API Token</label>
                  <input
                    type="password"
                    className="input text-sm"
                    placeholder="your-api-token"
                    value={jenkinsToken}
                    onChange={(e) => setJenkinsToken(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark-text-secondary mb-1">Job Name</label>
                  <input
                    type="text"
                    className="input text-sm"
                    placeholder="my-job"
                    value={jenkinsJob}
                    onChange={(e) => setJenkinsJob(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleTriggerJenkins}
                  disabled={isTriggering || loading}
                  className="btn btn-primary px-4 py-2"
                >
                  {isTriggering ? (
                    <>
                      <Activity className="animate-spin h-4 w-4 mr-2" />
                      Triggering...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Trigger Job
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderDiagnose = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            CI/CD Failure Diagnosis
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Diagnose CI/CD failures using LLM analysis.
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
                CI/CD Type
              </label>
              <select
                className="input"
                value={cicdType}
                onChange={(e) => setCicdType(e.target.value)}
              >
                <option value="GitHub Actions">GitHub Actions</option>
                <option value="Jenkins">Jenkins</option>
                <option value="GitLab CI">GitLab CI</option>
                <option value="Azure DevOps">Azure DevOps</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text-secondary mb-2">
                Log Content
              </label>
              <textarea
                className="input min-h-[200px]"
                placeholder="Paste your CI/CD failure logs here..."
                value={diagnosticsLog}
                onChange={(e) => setDiagnosticsLog(e.target.value)}
              />
            </div>
            <button
              onClick={handleDiagnose}
              disabled={isDiagnosing || loading}
              className="btn btn-primary px-4 py-2"
            >
              {isDiagnosing ? (
                <>
                  <Activity className="animate-spin h-4 w-4 mr-2" />
                  Diagnosing...
                </>
              ) : (
                <>
                  <Activity className="h-4 w-4 mr-2" />
                  Diagnose
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {cicdData?.diagnosis && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Diagnosis Results
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Diagnosis</h4>
                <div className="bg-dark-accent rounded-md p-4">
                  <pre className="text-sm text-dark-text whitespace-pre-wrap">
                    {JSON.stringify(cicdData.diagnosis.diagnosis, null, 2)}
                  </pre>
                </div>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="bg-blue-900/20 rounded-lg p-4">
                  <div className="flex items-center">
                    <BarChart3 className="h-5 w-5 text-blue-400 mr-2" />
                    <span className="text-sm font-medium text-blue-300">Log Length</span>
                  </div>
                  <p className="text-2xl font-bold text-blue-200 mt-1">
                    {cicdData.diagnosis.metadata?.log_length || 0}
                  </p>
                </div>
                <div className="bg-green-900/20 rounded-lg p-4">
                  <div className="flex items-center">
                    <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
                    <span className="text-sm font-medium text-green-300">Quality</span>
                  </div>
                  <p className="text-sm font-bold text-green-200 mt-1">
                    {cicdData.diagnosis.metadata?.diagnosis_quality || 'Unknown'}
                  </p>
                </div>
                <div className="bg-purple-900/20 rounded-lg p-4">
                  <div className="flex items-center">
                    <Clock className="h-5 w-5 text-purple-400 mr-2" />
                    <span className="text-sm font-medium text-purple-300">CI Type</span>
                  </div>
                  <p className="text-sm font-bold text-purple-200 mt-1">
                    {cicdData.diagnosis.metadata?.ci_type || 'Unknown'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderValidate = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            CI/CD Validation
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Validate CI/CD configuration and detect issues.
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
              onClick={handleValidate}
              disabled={loading}
              className="btn btn-primary px-4 py-2"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Validate
            </button>
          </div>
        </div>
      </div>

      {cicdData?.validation && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Validation Results
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Validation Report</h4>
                <div className="bg-dark-accent rounded-md p-4">
                  <pre className="text-sm text-dark-text whitespace-pre-wrap">
                    {JSON.stringify(cicdData.validation.report, null, 2)}
                  </pre>
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
            CI/CD Management
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            GitHub Actions, Jenkins, and diagnostics
          </p>
        </div>
      </div>

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
        {selectedTab === 'github' && renderGitHub()}
        {selectedTab === 'jenkins' && renderJenkins()}
        {selectedTab === 'diagnose' && renderDiagnose()}
        {selectedTab === 'validate' && renderValidate()}
      </motion.div>
    </div>
  );
};

export default CICD;
