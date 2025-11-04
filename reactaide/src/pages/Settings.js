import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import {
  Server,
  Save,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Activity,
  Zap,
  Shield,
  Bell
} from 'lucide-react';

const Settings = () => {
  const { 
    backendUrl,
    isConnected,
    connectionError,
    checkBackendConnection,
    addNotification 
  } = useApp();
  
  const [settings, setSettings] = useState({
    backendUrl: backendUrl || 'http://localhost:8000',
    weaviateUrl: 'http://localhost:8080',
    enableWeaviate: true,
    maxRepoSize: 100,
    cloneTimeout: 300,
    embedBatchSize: 10,
    embedTimeout: 30,
    logLevel: 'INFO'
  });
  
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResults, setTestResults] = useState(null);

  const handleSaveSettings = async () => {
    setIsSaving(true);
    try {
      // In a real app, you'd save these to localStorage or send to backend
      localStorage.setItem('aide-settings', JSON.stringify(settings));
      addNotification({ message: 'Settings saved successfully' });
    } catch (error) {
      addNotification({ message: 'Failed to save settings' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    try {
      await checkBackendConnection();
      setTestResults({ success: true, message: 'Connection test successful' });
    } catch (error) {
      setTestResults({ success: false, message: 'Connection test failed' });
    } finally {
      setIsTesting(false);
    }
  };

  const handleResetSettings = () => {
    setSettings({
      backendUrl: 'http://localhost:8000',
      weaviateUrl: 'http://localhost:8080',
      enableWeaviate: true,
      maxRepoSize: 100,
      cloneTimeout: 300,
      embedBatchSize: 10,
      embedTimeout: 30,
      logLevel: 'INFO'
    });
    addNotification({ message: 'Settings reset to defaults' });
  };

  const settingSections = [
    {
      id: 'connection',
      name: 'Connection',
      icon: Server,
      description: 'Backend and database connections'
    },
    {
      id: 'performance',
      name: 'Performance',
      icon: Zap,
      description: 'Performance and optimization settings'
    },
    {
      id: 'security',
      name: 'Security',
      icon: Shield,
      description: 'Security and authentication settings'
    },
    {
      id: 'notifications',
      name: 'Notifications',
      icon: Bell,
      description: 'Notification preferences'
    }
  ];

  const renderConnectionSettings = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Backend Connection
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Backend URL
              </label>
              <input
                type="text"
                className="input"
                value={settings.backendUrl}
                onChange={(e) => setSettings(prev => ({ ...prev, backendUrl: e.target.value }))}
                placeholder="http://localhost:8000"
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                {isConnected ? (
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                )}
                <span className="text-sm text-gray-700">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <button
                onClick={handleTestConnection}
                disabled={isTesting}
                className="btn btn-secondary px-3 py-1 text-sm"
              >
                {isTesting ? (
                  <>
                    <Activity className="animate-spin h-4 w-4 mr-1" />
                    Testing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Test
                  </>
                )}
              </button>
            </div>
            {connectionError && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-800">{connectionError}</p>
              </div>
            )}
            {testResults && (
              <div className={`border rounded-md p-3 ${
                testResults.success 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <p className={`text-sm ${
                  testResults.success ? 'text-green-800' : 'text-red-800'
                }`}>
                  {testResults.message}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Weaviate Configuration
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Weaviate URL
              </label>
              <input
                type="text"
                className="input"
                value={settings.weaviateUrl}
                onChange={(e) => setSettings(prev => ({ ...prev, weaviateUrl: e.target.value }))}
                placeholder="http://localhost:8080"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                checked={settings.enableWeaviate}
                onChange={(e) => setSettings(prev => ({ ...prev, enableWeaviate: e.target.checked }))}
              />
              <label className="ml-2 text-sm text-gray-700">
                Enable Weaviate for RAG queries
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPerformanceSettings = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Repository Analysis Limits
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Repository Size (MB)
              </label>
              <input
                type="number"
                className="input"
                value={settings.maxRepoSize}
                onChange={(e) => setSettings(prev => ({ ...prev, maxRepoSize: parseInt(e.target.value) }))}
                min="1"
                max="1000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Clone Timeout (seconds)
              </label>
              <input
                type="number"
                className="input"
                value={settings.cloneTimeout}
                onChange={(e) => setSettings(prev => ({ ...prev, cloneTimeout: parseInt(e.target.value) }))}
                min="60"
                max="1800"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Embedding Settings
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Embed Batch Size
              </label>
              <input
                type="number"
                className="input"
                value={settings.embedBatchSize}
                onChange={(e) => setSettings(prev => ({ ...prev, embedBatchSize: parseInt(e.target.value) }))}
                min="1"
                max="100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Embed Timeout (seconds)
              </label>
              <input
                type="number"
                className="input"
                value={settings.embedTimeout}
                onChange={(e) => setSettings(prev => ({ ...prev, embedTimeout: parseInt(e.target.value) }))}
                min="10"
                max="300"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Logging
          </h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Log Level
            </label>
            <select
              className="input"
              value={settings.logLevel}
              onChange={(e) => setSettings(prev => ({ ...prev, logLevel: e.target.value }))}
            >
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSecuritySettings = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Authentication
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                GitHub Token (Optional)
              </label>
              <input
                type="password"
                className="input"
                placeholder="Enter GitHub personal access token"
              />
              <p className="text-xs text-dark-text-secondary mt-1">
                Used for accessing private repositories and higher rate limits
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Keys
              </label>
              <div className="space-y-2">
                <input
                  type="password"
                  className="input"
                  placeholder="OpenAI API Key"
                />
                <input
                  type="password"
                  className="input"
                  placeholder="Anthropic API Key"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Data Privacy
          </h3>
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                defaultChecked
              />
              <label className="ml-2 text-sm text-gray-700">
                Store analysis data locally
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                defaultChecked
              />
              <label className="ml-2 text-sm text-gray-700">
                Allow anonymous usage analytics
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <label className="ml-2 text-sm text-gray-700">
                Share feedback data for model improvement
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderNotificationSettings = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Notification Preferences
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-dark-text">Analysis Complete</h4>
                <p className="text-sm text-dark-text-secondary">Notify when repository analysis is finished</p>
              </div>
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                defaultChecked
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-dark-text">Environment Ready</h4>
                <p className="text-sm text-dark-text-secondary">Notify when development environment is set up</p>
              </div>
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                defaultChecked
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-dark-text">CI/CD Status</h4>
                <p className="text-sm text-dark-text-secondary">Notify about CI/CD pipeline status changes</p>
              </div>
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-dark-text">System Updates</h4>
                <p className="text-sm text-dark-text-secondary">Notify about system updates and maintenance</p>
              </div>
              <input
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                defaultChecked
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const [selectedSection, setSelectedSection] = useState('connection');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-dark-text sm:text-3xl sm:truncate">
            Settings
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Configure your AI Developer Onboarding Engine
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* Settings Navigation */}
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {settingSections.map((section) => (
              <button
                key={section.id}
                onClick={() => setSelectedSection(section.id)}
                className={`${
                  selectedSection === section.id
                    ? 'bg-primary-50 border-primary-500 text-primary-700'
                    : 'border-transparent text-dark-text-secondary hover:bg-gray-50 hover:text-dark-text'
                } w-full flex items-center px-3 py-2 text-sm font-medium border-l-4 transition-colors duration-200`}
              >
                <section.icon className="h-5 w-5 mr-3" />
                <div className="text-left">
                  <div>{section.name}</div>
                  <div className="text-xs text-dark-text-secondary">{section.description}</div>
                </div>
              </button>
            ))}
          </nav>
        </div>

        {/* Settings Content */}
        <div className="lg:col-span-3">
          <motion.div
            key={selectedSection}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
          >
            {selectedSection === 'connection' && renderConnectionSettings()}
            {selectedSection === 'performance' && renderPerformanceSettings()}
            {selectedSection === 'security' && renderSecuritySettings()}
            {selectedSection === 'notifications' && renderNotificationSettings()}
          </motion.div>

          {/* Action Buttons */}
          <div className="mt-8 bg-dark-surface shadow rounded-lg border border-dark-border">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg leading-6 font-medium text-dark-text">
                    Save Settings
                  </h3>
                  <p className="text-sm text-dark-text-secondary">
                    Save your configuration changes
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={handleResetSettings}
                    className="btn btn-secondary px-4 py-2"
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Reset
                  </button>
                  <button
                    onClick={handleSaveSettings}
                    disabled={isSaving}
                    className="btn btn-primary px-4 py-2"
                  >
                    {isSaving ? (
                      <>
                        <Activity className="animate-spin h-4 w-4 mr-2" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        Save Settings
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
