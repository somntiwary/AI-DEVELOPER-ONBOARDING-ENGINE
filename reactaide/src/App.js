import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { motion } from 'framer-motion';

// Components
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import RepositoryAnalysis from './pages/RepositoryAnalysis';
import EnvironmentSetup from './pages/EnvironmentSetup';
import Documentation from './pages/Documentation';
import QnA from './pages/QnA';
import Walkthrough from './pages/Walkthrough';
import CICD from './pages/CICD';
import Feedback from './pages/Feedback';
import Settings from './pages/Settings';

// Context
import { AppProvider } from './context/AppContext';

function App() {
  return (
    <AppProvider>
      <Router>
        <div className="min-h-screen bg-dark-bg">
          <Layout>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/repository" element={<RepositoryAnalysis />} />
                <Route path="/environment" element={<EnvironmentSetup />} />
                <Route path="/documentation" element={<Documentation />} />
                <Route path="/qna" element={<QnA />} />
                <Route path="/walkthrough" element={<Walkthrough />} />
                <Route path="/cicd" element={<CICD />} />
                <Route path="/feedback" element={<Feedback />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </motion.div>
          </Layout>
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
        </div>
      </Router>
    </AppProvider>
  );
}

export default App;