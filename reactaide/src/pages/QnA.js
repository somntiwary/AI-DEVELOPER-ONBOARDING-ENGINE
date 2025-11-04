import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import useAgentState from '../hooks/useAgentState';
import {
  MessageCircle,
  Send,
  Bot,
  User,
  Activity,
  Lightbulb,
  History,
  Zap
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const QnA = () => {
  const { 
    currentProject, 
    loading, 
    apiCall, 
    addNotification 
  } = useApp();
  
  // Use persistent agent state from context
  const agentState = useAgentState('qna');
  const qnaData = agentState.state.qnaData;
  const conversation = agentState.state.conversation || [];
  const followUpQuestions = agentState.state.followUpQuestions || [];
  
  const [isInitializing, setIsInitializing] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedTab, setSelectedTab] = useState('chat');
  const [projectPath, setProjectPath] = useState('');
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState([]);
  const [isLoadingFollowUps, setIsLoadingFollowUps] = useState(false);

  useEffect(() => {
    if (currentProject) {
      setProjectPath(currentProject.path);
    }
  }, [currentProject]);

  const tabs = [
    { id: 'chat', name: 'Chat', icon: MessageCircle },
    { id: 'analyze', name: 'Analyze Intent', icon: Lightbulb },
    { id: 'history', name: 'History', icon: History },
    { id: 'summary', name: 'Summary', icon: Bot }
  ];

  const handleInitialize = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsInitializing(true);
    try {
      const result = await apiCall('/api/qna/initialize', 'POST', {
        project_path: projectPath
      });
      
      agentState.updateStateField('qnaData', result);
      agentState.updateStateField('data', result);
      agentState.updateStateField('initialized', true);
      
      addNotification({ 
        message: 'Knowledge base initialized successfully' 
      });
      
    } catch (error) {
      console.error('Knowledge base initialization failed:', error);
    } finally {
      setIsInitializing(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!projectPath.trim() || !question.trim()) {
      addNotification({ message: 'Please enter both project path and question' });
      return;
    }

    setIsAsking(true);
    try {
      const result = await apiCall('/api/qna/ask', 'POST', {
        project_path: projectPath,
        question: question,
        include_sources: true
      });
      
      const newMessage = {
        id: Date.now(),
        question: question,
        answer: result.answer,
        sources: result.sources || [],
        timestamp: new Date().toISOString()
      };
      
      const updatedConversation = [...conversation, newMessage];
      agentState.updateStateField('conversation', updatedConversation);
      setQuestion('');
      
      // Get follow-up questions after successful answer
      setTimeout(() => {
        handleGetFollowUpQuestions();
      }, 1000);
      
      addNotification({ 
        message: 'Question answered successfully' 
      });
      
    } catch (error) {
      console.error('Question asking failed:', error);
    } finally {
      setIsAsking(false);
    }
  };

  const handleAnalyzeIntent = async () => {
    if (!projectPath.trim() || !question.trim()) {
      addNotification({ message: 'Please enter both project path and question' });
      return;
    }

    setIsAnalyzing(true);
    try {
      const result = await apiCall('/api/qna/analyze-intent', 'POST', {
        project_path: projectPath,
        question: question
      });
      
      const updatedData = { ...qnaData, intentAnalysis: result };
      agentState.updateStateField('qnaData', updatedData);
      
      addNotification({ 
        message: 'Intent analysis completed successfully' 
      });
      
    } catch (error) {
      console.error('Intent analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGetHistory = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    try {
      const result = await apiCall('/api/qna/history', 'POST', {
        project_path: projectPath,
        limit: 10
      });
      
      setHistory(result.conversation_history || []);
      
      addNotification({ 
        message: 'Conversation history retrieved successfully' 
      });
      
    } catch (error) {
      console.error('History retrieval failed:', error);
    }
  };

  const handleResetHistory = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    try {
      await apiCall('/api/qna/reset-history', 'POST', {
        project_path: projectPath
      });
      
      setHistory([]);
      agentState.updateStateField('conversation', []);
      agentState.updateStateField('followUpQuestions', []);
      
      addNotification({ 
        message: 'Conversation history cleared successfully' 
      });
      
    } catch (error) {
      console.error('History reset failed:', error);
    }
  };

  const handleGetSummary = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    try {
      const result = await apiCall('/api/qna/summary', 'POST', {
        project_path: projectPath
      });
      
      const updatedData = { ...qnaData, summary: result };
      agentState.updateStateField('qnaData', updatedData);
      
      addNotification({ 
        message: 'Project summary retrieved successfully' 
      });
      
    } catch (error) {
      console.error('Summary retrieval failed:', error);
    }
  };

  const handleGetFollowUpQuestions = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsLoadingFollowUps(true);
    try {
      const result = await apiCall('/api/qna/suggest-followups', 'POST', {
        project_path: projectPath,
        question: conversation[conversation.length - 1]?.question || ''
      });
      
      console.log('Follow-up API response:', result);
      
      if (result.suggested_followups && result.suggested_followups.length > 0) {
        agentState.updateStateField('followUpQuestions', result.suggested_followups);
        addNotification({ 
          message: `Generated ${result.suggested_followups.length} follow-up questions` 
        });
      } else {
        agentState.updateStateField('followUpQuestions', []);
        addNotification({ 
          message: 'No follow-up questions available' 
        });
      }
      
    } catch (error) {
      console.error('Follow-up questions retrieval failed:', error);
      agentState.updateStateField('followUpQuestions', []);
      addNotification({ 
        message: 'Failed to get follow-up questions' 
      });
    } finally {
      setIsLoadingFollowUps(false);
    }
  };

  const handleFollowUpClick = (followUpQuestion) => {
    setQuestion(followUpQuestion);
    agentState.updateStateField('followUpQuestions', []);
  };


  const renderChat = () => (
    <div className="space-y-6">
      {/* Initialize Knowledge Base */}
      {!qnaData && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Initialize Knowledge Base
            </h3>
            <p className="text-sm text-dark-text-secondary mb-4">
              Initialize the comprehensive knowledge base for this project.
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
                onClick={handleInitialize}
                disabled={isInitializing || loading}
                className="btn btn-primary px-4 py-2"
              >
                {isInitializing ? (
                  <>
                    <Activity className="animate-spin h-4 w-4 mr-2" />
                    Initializing...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Initialize
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chat Interface */}
      {qnaData && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Ask Questions About Your Project
            </h3>
            
            {/* Conversation */}
            <div className="space-y-4 mb-6 max-h-96 overflow-y-auto">
              {conversation.map((message) => (
                <div key={message.id} className="space-y-3">
                  {/* Question */}
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <User className="h-6 w-6 text-blue-500" />
                    </div>
                    <div className="flex-1">
                      <div className="bg-blue-900/20 rounded-lg p-3">
                        <p className="text-sm text-blue-300">{message.question}</p>
                      </div>
                    </div>
                  </div>
                  
                  {/* Answer */}
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <Bot className="h-6 w-6 text-green-500" />
                    </div>
                    <div className="flex-1">
                      <div className="bg-green-900/20 rounded-lg p-3">
                        <div className="prose prose-sm max-w-none prose-invert">
                          <ReactMarkdown>{message.answer}</ReactMarkdown>
                        </div>
                        {message.sources && message.sources.length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs text-dark-text-secondary mb-1">Sources:</p>
                            <div className="space-y-1">
                              {message.sources.map((source, index) => (
                                <div key={index} className="text-xs text-dark-text-secondary bg-dark-accent rounded px-2 py-1">
                                  {source}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Follow-up Questions */}
              {followUpQuestions.length > 0 && (
                <div className="mt-4 p-4 bg-dark-accent rounded-lg border border-dark-border">
                  <h4 className="text-sm font-medium text-dark-text-secondary mb-3 flex items-center">
                    <Lightbulb className="h-4 w-4 mr-2" />
                    Suggested Follow-up Questions
                  </h4>
                  <div className="space-y-2">
                    {followUpQuestions.map((followUp, index) => (
                      <button
                        key={index}
                        onClick={() => handleFollowUpClick(followUp)}
                        className="block w-full text-left p-3 bg-dark-surface hover:bg-dark-border rounded-md border border-dark-border transition-colors duration-200"
                      >
                        <p className="text-sm text-dark-text">{followUp}</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Question Input */}
            <div className="space-y-4">
              <div className="flex space-x-4">
                <div className="flex-1">
                  <textarea
                    className="input min-h-[80px]"
                    placeholder="Ask a question about your project..."
                    value={question}
                    onChange={(e) => {
                      setQuestion(e.target.value);
                      // Clear follow-up questions when typing new question
                      if (followUpQuestions.length > 0) {
                        agentState.updateStateField('followUpQuestions', []);
                      }
                    }}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleAskQuestion();
                      }
                    }}
                  />
                </div>
                <button
                  onClick={handleAskQuestion}
                  disabled={isAsking || loading}
                  className="btn btn-primary px-4 py-2"
                >
                  {isAsking ? (
                    <>
                      <Activity className="animate-spin h-4 w-4 mr-2" />
                      Asking...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Ask
                    </>
                  )}
                </button>
              </div>
              
              {/* Follow-up Questions Controls */}
              {conversation.length > 0 && (
                <div className="flex justify-between items-center">
                  <button
                    onClick={handleGetFollowUpQuestions}
                    disabled={isLoadingFollowUps || loading}
                    className="btn btn-secondary px-3 py-2 text-sm"
                  >
                    {isLoadingFollowUps ? (
                      <>
                        <Activity className="animate-spin h-4 w-4 mr-2" />
                        Loading...
                      </>
                    ) : (
                      <>
                        <Lightbulb className="h-4 w-4 mr-2" />
                        Get Follow-up Questions
                      </>
                    )}
                  </button>
                  
                  {followUpQuestions.length > 0 && (
                    <button
                      onClick={() => agentState.updateStateField('followUpQuestions', [])}
                      className="text-sm text-dark-text-secondary hover:text-dark-text"
                    >
                      Clear suggestions
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderAnalyzeIntent = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Analyze Question Intent
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Analyze the intent of a question to understand what type of information is being requested.
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
                placeholder="Enter a question to analyze..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              />
            </div>
            <button
              onClick={handleAnalyzeIntent}
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
                  <Lightbulb className="h-4 w-4 mr-2" />
                  Analyze Intent
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {qnaData?.intentAnalysis && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Intent Analysis Result
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Question</h4>
                <p className="text-sm text-dark-text bg-dark-accent rounded-md p-3">
                  {qnaData.intentAnalysis.question}
                </p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Intent Analysis</h4>
                <div className="bg-blue-900/20 rounded-md p-4">
                  <pre className="text-sm text-blue-300 whitespace-pre-wrap">
                    {JSON.stringify(qnaData.intentAnalysis.intent_analysis, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderHistory = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Conversation History
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            View conversation history for this project.
          </p>
          <div className="space-y-4">
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
                onClick={handleGetHistory}
                disabled={loading}
                className="btn btn-primary px-4 py-2"
              >
                <History className="h-4 w-4 mr-2" />
                Get History
              </button>
            </div>
            
            {history.length > 0 && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-dark-text-secondary">
                  {history.length} conversation{history.length !== 1 ? 's' : ''} found
                </span>
                <button
                  onClick={handleResetHistory}
                  disabled={loading}
                  className="btn btn-danger px-3 py-2 text-sm"
                >
                  <Activity className="h-4 w-4 mr-2" />
                  Reset History
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {history.length > 0 && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Recent Conversations
            </h3>
            <div className="space-y-4">
              {history.map((conv, index) => (
                <div key={index} className="shadow rounded-lg border border-dark-border rounded-lg p-4">
                  <div className="space-y-2">
                    <div>
                      <h4 className="text-sm font-medium text-dark-text">Question:</h4>
                      <p className="text-sm text-dark-text-secondary">{conv.question}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-dark-text">Answer:</h4>
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>{conv.answer}</ReactMarkdown>
                      </div>
                    </div>
                    <div className="text-xs text-dark-text-secondary">
                      {new Date(conv.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderSummary = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Project Summary
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Get comprehensive project summary including knowledge base status.
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
              onClick={handleGetSummary}
              disabled={loading}
              className="btn btn-primary px-4 py-2"
            >
              <Bot className="h-4 w-4 mr-2" />
              Get Summary
            </button>
          </div>
        </div>
      </div>

      {qnaData?.summary && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Project Summary
            </h3>
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{JSON.stringify(qnaData.summary, null, 2)}</ReactMarkdown>
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
            Q&A Assistant
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Conversational interface with project knowledge
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
        {selectedTab === 'chat' && renderChat()}
        {selectedTab === 'analyze' && renderAnalyzeIntent()}
        {selectedTab === 'history' && renderHistory()}
        {selectedTab === 'summary' && renderSummary()}
      </motion.div>
    </div>
  );
};

export default QnA;
