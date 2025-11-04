import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  GitBranch,
  Settings,
  FileText,
  MessageCircle,
  Play,
  Workflow,
  MessageSquare,
  Menu,
  X,
  Wifi,
  WifiOff,
  AlertCircle
} from 'lucide-react';
import { useApp } from '../context/AppContext';

const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Repository Analysis', href: '/repository', icon: GitBranch },
  { name: 'Environment Setup', href: '/environment', icon: Settings },
  { name: 'Documentation', href: '/documentation', icon: FileText },
  { name: 'Q&A Assistant', href: '/qna', icon: MessageCircle },
  { name: 'Walkthrough', href: '/walkthrough', icon: Play },
  { name: 'CI/CD', href: '/cicd', icon: Workflow },
  { name: 'Feedback', href: '/feedback', icon: MessageSquare },
];

function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { isConnected, connectionError, currentProject } = useApp();

  return (
    <div className="h-screen flex overflow-hidden bg-dark-bg">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 flex z-40 md:hidden">
          <div className="fixed inset-0 bg-black bg-opacity-75" onClick={() => setSidebarOpen(false)} />
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-dark-surface">
            <div className="absolute top-0 right-0 -mr-12 pt-2">
              <button
                type="button"
                className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-dark-border"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="h-6 w-6 text-dark-text" />
              </button>
            </div>
            <SidebarContent />
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden md:flex md:flex-shrink-0">
        <div className="flex flex-col w-64">
          <SidebarContent />
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        {/* Top bar */}
        <div className="relative z-10 flex-shrink-0 flex h-16 bg-dark-surface border-b border-dark-border shadow">
          <button
            type="button"
            className="px-4 border-r border-dark-border text-dark-text-secondary focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 md:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>
          
          <div className="flex-1 px-4 flex justify-between">
            <div className="flex-1 flex">
              <div className="w-full flex md:ml-0">
                <div className="relative w-full text-dark-text-secondary focus-within:text-dark-text">
                  <div className="absolute inset-y-0 left-0 flex items-center pointer-events-none">
                    <span className="text-sm font-medium text-dark-text">
                      AI Developer Onboarding Engine
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="ml-4 flex items-center md:ml-6">
              {/* Connection status */}
              <div className="flex items-center space-x-2">
                {isConnected ? (
                  <div className="flex items-center text-green-400">
                    <Wifi className="h-4 w-4 mr-1" />
                    <span className="text-sm">Connected</span>
                  </div>
                ) : (
                  <div className="flex items-center text-red-400">
                    <WifiOff className="h-4 w-4 mr-1" />
                    <span className="text-sm">Disconnected</span>
                  </div>
                )}
              </div>
              
              {/* Current project */}
              {currentProject && (
                <div className="ml-4 flex items-center text-sm text-dark-text-secondary">
                  <span>Project: {currentProject.name || 'Untitled'}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Connection error banner */}
        {connectionError && (
          <div className="bg-red-900/20 border-l-4 border-red-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertCircle className="h-5 w-5 text-red-400" />
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-300">{connectionError}</p>
              </div>
            </div>
          </div>
        )}

        {/* Page content */}
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function SidebarContent() {
  const location = useLocation();
  const { currentProject } = useApp();

  return (
    <div className="flex flex-col h-0 flex-1 border-r border-dark-border bg-dark-surface">
      {/* Logo */}
      <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
        <div className="flex items-center flex-shrink-0 px-4">
          <div className="w-full flex justify-center">
            <img 
              src="/aide_logo__.png" 
              alt="AIDE Logo" 
              className="w-full max-w-48 h-auto"
            />
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="mt-5 flex-1 px-2 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`${
                  isActive
                    ? 'bg-primary-900/30 border-primary-500 text-primary-300'
                    : 'border-transparent text-dark-text-secondary hover:bg-dark-accent hover:text-dark-text'
                } group flex items-center px-2 py-2 text-sm font-medium rounded-md border-l-4 transition-colors duration-200`}
              >
                <item.icon
                  className={`${
                    isActive ? 'text-primary-400' : 'text-dark-text-secondary group-hover:text-dark-text'
                  } mr-3 flex-shrink-0 h-5 w-5`}
                />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
      
      {/* Current project info */}
      {currentProject && (
        <div className="flex-shrink-0 flex border-t border-dark-border p-4">
          <div className="flex-shrink-0 w-full group block">
            <div className="flex items-center">
              <div className="ml-3">
                <p className="text-sm font-medium text-dark-text-secondary group-hover:text-dark-text">
                  Current Project
                </p>
                <p className="text-xs font-medium text-dark-text-secondary group-hover:text-dark-text">
                  {currentProject.name || 'Untitled Project'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Layout;
