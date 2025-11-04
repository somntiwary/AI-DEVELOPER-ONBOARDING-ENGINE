import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import useAgentState from '../hooks/useAgentState';
import {
  MessageSquare,
  BarChart3,
  TrendingUp,
  RefreshCw,
  CheckCircle,
  Activity,
  Star,
  ThumbsUp,
  Brain
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const Feedback = () => {
  const { 
    currentProject, 
    loading, 
    apiCall, 
    addNotification 
  } = useApp();
  
  // Use persistent agent state from context
  const agentState = useAgentState('feedback');
  const feedbackData = agentState.state.feedbackData;
  
  const [isCollecting, setIsCollecting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isRetraining, setIsRetraining] = useState(false);
  const [selectedTab, setSelectedTab] = useState('collect');
  const [projectPath, setProjectPath] = useState('');
  
  // Feedback form data
  const [feedbackForm, setFeedbackForm] = useState({
    user_id: 'user_123',
    session_id: 'session_456',
    feedback_type: 'general',
    description: '',
    rating: 5,
    title: '',
    severity: 'medium',
    agent_involved: '',
    step_failed: '',
    suggested_fix: '',
    user_experience: '',
    tags: [],
    context: {}
  });

  // Survey form data
  const [surveyForm, setSurveyForm] = useState({
    user_id: 'user_123',
    session_id: 'session_456',
    overall_rating: 5,
    onboarding_time_minutes: 30,
    agents_used: [],
    most_helpful_agent: '',
    least_helpful_agent: '',
    would_recommend: true,
    additional_comments: ''
  });

  useEffect(() => {
    if (currentProject) {
      setProjectPath(currentProject.path);
    }
  }, [currentProject]);

  const tabs = [
    { id: 'collect', name: 'Collect', icon: MessageSquare },
    { id: 'analytics', name: 'Analytics', icon: BarChart3 },
    { id: 'retrain', name: 'Retrain', icon: RefreshCw },
    { id: 'dashboard', name: 'Dashboard', icon: TrendingUp }
  ];

  const handleCollectFeedback = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsCollecting(true);
    try {
      const result = await apiCall('/api/feedback/collect', 'POST', {
        ...feedbackForm,
        project_path: projectPath
      });
      
      const updatedData = { ...feedbackData, feedbackResult: result };
      agentState.updateStateField('feedbackData', updatedData);
      
      addNotification({ 
        message: 'Feedback collected successfully' 
      });
      
    } catch (error) {
      console.error('Feedback collection failed:', error);
    } finally {
      setIsCollecting(false);
    }
  };

  const handleCollectSurvey = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsCollecting(true);
    try {
      const result = await apiCall('/api/feedback/survey/satisfaction', 'POST', {
        ...surveyForm,
        project_path: projectPath
      });
      
      const updatedData = { ...feedbackData, surveyResult: result };
      agentState.updateStateField('feedbackData', updatedData);
      
      addNotification({ 
        message: 'Satisfaction survey collected successfully' 
      });
      
    } catch (error) {
      console.error('Survey collection failed:', error);
    } finally {
      setIsCollecting(false);
    }
  };

  const handleAnalyzeSatisfaction = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsAnalyzing(true);
    try {
      const result = await apiCall('/api/feedback/analytics/satisfaction', 'POST', {
        project_path: projectPath,
        days: 30
      });
      
      const updatedData = { ...feedbackData, satisfactionTrends: result };
      agentState.updateStateField('feedbackData', updatedData);
      
      addNotification({ 
        message: 'Satisfaction trends analyzed successfully' 
      });
      
    } catch (error) {
      console.error('Satisfaction analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAnalyzePerformance = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsAnalyzing(true);
    try {
      const result = await apiCall('/api/feedback/analytics/performance', 'POST', {
        project_path: projectPath
      });
      
      const updatedData = { ...feedbackData, performanceAnalysis: result };
      agentState.updateStateField('feedbackData', updatedData);
      
      addNotification({ 
        message: 'Agent performance analyzed successfully' 
      });
      
    } catch (error) {
      console.error('Performance analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRetrain = async (agentName) => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsRetraining(true);
    try {
      const result = await apiCall('/api/feedback/retrain/execute', 'POST', {
        agent_name: agentName,
        force_retrain: true
      });
      
      const updatedData = { ...feedbackData, retrainResult: result };
      agentState.updateStateField('feedbackData', updatedData);
      
      addNotification({ 
        message: `Model retraining for ${agentName} completed successfully` 
      });
      
    } catch (error) {
      console.error('Retraining failed:', error);
    } finally {
      setIsRetraining(false);
    }
  };

  const renderCollect = () => (
    <div className="space-y-6">
      {/* Feedback Collection */}
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Collect Feedback
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Collect user feedback from onboarding experiences.
          </p>
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Feedback Type
                </label>
                <select
                  className="input"
                  value={feedbackForm.feedback_type}
                  onChange={(e) => setFeedbackForm(prev => ({ ...prev, feedback_type: e.target.value }))}
                >
                  <option value="general">General</option>
                  <option value="bug">Bug Report</option>
                  <option value="feature">Feature Request</option>
                  <option value="improvement">Improvement</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Severity
                </label>
                <select
                  className="input"
                  value={feedbackForm.severity}
                  onChange={(e) => setFeedbackForm(prev => ({ ...prev, severity: e.target.value }))}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title
              </label>
              <input
                type="text"
                className="input"
                placeholder="Brief title for your feedback"
                value={feedbackForm.title}
                onChange={(e) => setFeedbackForm(prev => ({ ...prev, title: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                className="input min-h-[100px]"
                placeholder="Describe your feedback in detail..."
                value={feedbackForm.description}
                onChange={(e) => setFeedbackForm(prev => ({ ...prev, description: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Rating (1-5)
              </label>
              <div className="flex space-x-2">
                {[1, 2, 3, 4, 5].map((rating) => (
                  <button
                    key={rating}
                    onClick={() => setFeedbackForm(prev => ({ ...prev, rating }))}
                    className={`p-2 rounded-full ${
                      feedbackForm.rating >= rating
                        ? 'text-yellow-400'
                        : 'text-gray-300'
                    }`}
                  >
                    <Star className="h-6 w-6" />
                  </button>
                ))}
              </div>
            </div>
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
                onClick={handleCollectFeedback}
                disabled={isCollecting || loading}
                className="btn btn-primary px-4 py-2"
              >
                {isCollecting ? (
                  <>
                    <Activity className="animate-spin h-4 w-4 mr-2" />
                    Collecting...
                  </>
                ) : (
                  <>
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Submit Feedback
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Satisfaction Survey */}
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Satisfaction Survey
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Collect structured satisfaction survey data.
          </p>
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Overall Rating
                </label>
                <div className="flex space-x-2">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      onClick={() => setSurveyForm(prev => ({ ...prev, overall_rating: rating }))}
                      className={`p-2 rounded-full ${
                        surveyForm.overall_rating >= rating
                          ? 'text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    >
                      <Star className="h-6 w-6" />
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Onboarding Time (minutes)
                </label>
                <input
                  type="number"
                  className="input"
                  value={surveyForm.onboarding_time_minutes}
                  onChange={(e) => setSurveyForm(prev => ({ ...prev, onboarding_time_minutes: parseInt(e.target.value) }))}
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Comments
              </label>
              <textarea
                className="input min-h-[100px]"
                placeholder="Any additional comments about your experience..."
                value={surveyForm.additional_comments}
                onChange={(e) => setSurveyForm(prev => ({ ...prev, additional_comments: e.target.value }))}
              />
            </div>
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  checked={surveyForm.would_recommend}
                  onChange={(e) => setSurveyForm(prev => ({ ...prev, would_recommend: e.target.checked }))}
                />
                <span className="ml-2 text-sm text-gray-700">Would recommend to others</span>
              </label>
            </div>
            <button
              onClick={handleCollectSurvey}
              disabled={isCollecting || loading}
              className="btn btn-primary px-4 py-2"
            >
              {isCollecting ? (
                <>
                  <Activity className="animate-spin h-4 w-4 mr-2" />
                  Submitting...
                </>
              ) : (
                <>
                  <ThumbsUp className="h-4 w-4 mr-2" />
                  Submit Survey
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderAnalytics = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Analytics & Insights
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Analyze feedback data and generate insights.
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <button
              onClick={handleAnalyzeSatisfaction}
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
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Analyze Satisfaction
                </>
              )}
            </button>
            <button
              onClick={handleAnalyzePerformance}
              disabled={isAnalyzing || loading}
              className="btn btn-secondary px-4 py-2"
            >
              {isAnalyzing ? (
                <>
                  <Activity className="animate-spin h-4 w-4 mr-2" />
                  Analyzing...
                </>
              ) : (
                <>
                  <BarChart3 className="h-4 w-4 mr-2" />
                  Analyze Performance
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Analytics Results */}
      {feedbackData?.satisfactionTrends && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Satisfaction Trends
            </h3>
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-md p-4">
                <pre className="text-sm text-dark-text whitespace-pre-wrap">
                  {JSON.stringify(feedbackData.satisfactionTrends.trends, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {feedbackData?.performanceAnalysis && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Agent Performance Analysis
            </h3>
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-md p-4">
                <pre className="text-sm text-dark-text whitespace-pre-wrap">
                  {JSON.stringify(feedbackData.performanceAnalysis.performance, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderRetrain = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Model Retraining
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Retrain agent models based on feedback data.
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {['repository', 'environment', 'documentation', 'qna', 'walkthrough', 'cicd'].map((agent) => (
              <div key={agent} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-dark-text capitalize">
                    {agent} Agent
                  </h4>
                  <button
                    onClick={() => handleRetrain(agent)}
                    disabled={isRetraining || loading}
                    className="btn btn-primary px-3 py-1 text-sm"
                  >
                    {isRetraining ? (
                      <>
                        <Activity className="animate-spin h-4 w-4 mr-1" />
                        Retraining...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-4 w-4 mr-1" />
                        Retrain
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-dark-text-secondary">
                  Retrain {agent} model with latest feedback
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {feedbackData?.retrainResult && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Retraining Results
            </h3>
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <div className="flex">
                  <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
                  <div>
                    <h4 className="text-sm font-medium text-green-800">Retraining Completed</h4>
                    <p className="text-sm text-green-700 mt-1">
                      {feedbackData.retrainResult.message}
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 rounded-md p-4">
                <pre className="text-sm text-dark-text whitespace-pre-wrap">
                  {JSON.stringify(feedbackData.retrainResult.result, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderDashboard = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Performance Dashboard
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Visualize feedback analytics and performance metrics.
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center">
                <MessageSquare className="h-5 w-5 text-blue-500 mr-2" />
                <span className="text-sm font-medium text-blue-800">Total Feedback</span>
              </div>
              <p className="text-2xl font-bold text-blue-900 mt-1">1,234</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center">
                <Star className="h-5 w-5 text-green-500 mr-2" />
                <span className="text-sm font-medium text-green-800">Avg Rating</span>
              </div>
              <p className="text-2xl font-bold text-green-900 mt-1">4.2</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center">
                <TrendingUp className="h-5 w-5 text-purple-500 mr-2" />
                <span className="text-sm font-medium text-purple-800">Satisfaction</span>
              </div>
              <p className="text-2xl font-bold text-purple-900 mt-1">87%</p>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center">
                <Brain className="h-5 w-5 text-orange-500 mr-2" />
                <span className="text-sm font-medium text-orange-800">Models Retrained</span>
              </div>
              <p className="text-2xl font-bold text-orange-900 mt-1">12</p>
            </div>
          </div>
        </div>
      </div>

      {/* Sample Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Satisfaction Over Time
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={[
                  { month: 'Jan', satisfaction: 4.2 },
                  { month: 'Feb', satisfaction: 4.3 },
                  { month: 'Mar', satisfaction: 4.1 },
                  { month: 'Apr', satisfaction: 4.4 },
                  { month: 'May', satisfaction: 4.5 },
                  { month: 'Jun', satisfaction: 4.3 }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="satisfaction" stroke="#3b82f6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Agent Performance
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[
                  { agent: 'Repository', performance: 85 },
                  { agent: 'Environment', performance: 78 },
                  { agent: 'Documentation', performance: 92 },
                  { agent: 'Q&A', performance: 88 },
                  { agent: 'Walkthrough', performance: 81 },
                  { agent: 'CI/CD', performance: 76 }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="agent" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="performance" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-dark-text sm:text-3xl sm:truncate">
            Feedback & Learning
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Analytics, learning, and model retraining
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
        {selectedTab === 'collect' && renderCollect()}
        {selectedTab === 'analytics' && renderAnalytics()}
        {selectedTab === 'retrain' && renderRetrain()}
        {selectedTab === 'dashboard' && renderDashboard()}
      </motion.div>
    </div>
  );
};

export default Feedback;
