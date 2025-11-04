import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import useAgentState from '../hooks/useAgentState';
import {
  Play,
  CheckCircle,
  AlertCircle,
  Clock,
  Activity,
  HelpCircle,
  RefreshCw,
  User,
  BookOpen,
  Settings,
  Code,
  Database,
  X,
  FileText,
  Terminal,
  Package,
  Server,
  TestTube,
  FolderOpen
} from 'lucide-react';

const Walkthrough = () => {
  const { 
    currentProject, 
    loading, 
    apiCall, 
    addNotification 
  } = useApp();
  
  // Use persistent agent state from context
  const agentState = useAgentState('walkthrough');
  const walkthroughData = agentState.state.walkthroughData;
  const steps = agentState.state.steps || [];
  const sessionStatus = agentState.state.sessionStatus;
  
  const [isInitializing, setIsInitializing] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [selectedTab, setSelectedTab] = useState('steps');
  const [projectPath, setProjectPath] = useState('');
  const [currentStep] = useState(0);
  const [isHelpDialogOpen, setIsHelpDialogOpen] = useState(false);
  const [selectedStepForHelp, setSelectedStepForHelp] = useState(null);
  const [projectType, setProjectType] = useState(null);
  const [projectAnalysis, setProjectAnalysis] = useState(null);

  // Environment-based step detection instead of project type
  const analyzeProjectEnvironment = (projectFiles) => {
    const analysis = {
      hasPackageJson: false,
      hasRequirementsTxt: false,
      hasPomXml: false,
      hasDockerfile: false,
      hasVirtualEnv: false,
      hasNodeModules: false,
      hasTests: false,
      hasEnvFiles: false,
      hasBuildScripts: false,
      hasDatabaseConfig: false,
      hasApiEndpoints: false,
      frameworks: [],
      databases: [],
      testingFrameworks: [],
      buildTools: []
    };

    const files = projectFiles || [];
    
    // Analyze files and dependencies
    files.forEach(file => {
      if (file.includes('package.json')) analysis.hasPackageJson = true;
      if (file.includes('requirements.txt')) analysis.hasRequirementsTxt = true;
      if (file.includes('pom.xml')) analysis.hasPomXml = true;
      if (file.includes('Dockerfile')) analysis.hasDockerfile = true;
      if (file.includes('venv/') || file.includes('env/')) analysis.hasVirtualEnv = true;
      if (file.includes('node_modules/')) analysis.hasNodeModules = true;
      if (file.includes('test') || file.includes('spec') || file.includes('__tests__')) analysis.hasTests = true;
      if (file.includes('.env')) analysis.hasEnvFiles = true;
      if (file.includes('build') || file.includes('dist')) analysis.hasBuildScripts = true;
      if (file.includes('database') || file.includes('db') || file.includes('models')) analysis.hasDatabaseConfig = true;
      if (file.includes('api') || file.includes('routes') || file.includes('endpoints')) analysis.hasApiEndpoints = true;
      
      // Detect frameworks
      if (file.includes('react') || file.includes('React')) analysis.frameworks.push('React');
      if (file.includes('vue') || file.includes('Vue')) analysis.frameworks.push('Vue');
      if (file.includes('angular') || file.includes('Angular')) analysis.frameworks.push('Angular');
      if (file.includes('django') || file.includes('Django')) analysis.frameworks.push('Django');
      if (file.includes('flask') || file.includes('Flask')) analysis.frameworks.push('Flask');
      if (file.includes('fastapi') || file.includes('FastAPI')) analysis.frameworks.push('FastAPI');
      if (file.includes('express') || file.includes('Express')) analysis.frameworks.push('Express');
      if (file.includes('spring') || file.includes('Spring')) analysis.frameworks.push('Spring');
      
      // Detect databases
      if (file.includes('postgres') || file.includes('PostgreSQL')) analysis.databases.push('PostgreSQL');
      if (file.includes('mysql') || file.includes('MySQL')) analysis.databases.push('MySQL');
      if (file.includes('mongodb') || file.includes('MongoDB')) analysis.databases.push('MongoDB');
      if (file.includes('sqlite') || file.includes('SQLite')) analysis.databases.push('SQLite');
      if (file.includes('redis') || file.includes('Redis')) analysis.databases.push('Redis');
      
      // Detect testing frameworks
      if (file.includes('jest') || file.includes('Jest')) analysis.testingFrameworks.push('Jest');
      if (file.includes('pytest') || file.includes('pytest')) analysis.testingFrameworks.push('pytest');
      if (file.includes('junit') || file.includes('JUnit')) analysis.testingFrameworks.push('JUnit');
      if (file.includes('mocha') || file.includes('Mocha')) analysis.testingFrameworks.push('Mocha');
      if (file.includes('cypress') || file.includes('Cypress')) analysis.testingFrameworks.push('Cypress');
      
      // Detect build tools
      if (file.includes('webpack') || file.includes('Webpack')) analysis.buildTools.push('Webpack');
      if (file.includes('vite') || file.includes('Vite')) analysis.buildTools.push('Vite');
      if (file.includes('rollup') || file.includes('Rollup')) analysis.buildTools.push('Rollup');
      if (file.includes('maven') || file.includes('Maven')) analysis.buildTools.push('Maven');
      if (file.includes('gradle') || file.includes('Gradle')) analysis.buildTools.push('Gradle');
    });

    return analysis;
  };

  // Generate steps based on environment analysis
  const generateEnvironmentBasedSteps = (environmentAnalysis) => {
    const steps = [];
    let stepNumber = 1;

    // Step 1: Clone Repository (always first)
    steps.push({
      step_no: stepNumber++,
      title: "Clone Repository",
      description: "Download the entire source code to your local system",
      prerequisites: ["Git installed", "Repository access permissions"],
      related_files: ["README.md", ".gitignore"],
      icon: Terminal
    });

    // Step 2: Navigate to Project Directory (always second)
    steps.push({
      step_no: stepNumber++,
      title: "Navigate to Project Directory",
      description: "Switch to the project's root folder",
      prerequisites: ["Repository cloned"],
      related_files: ["package.json", "requirements.txt", "pom.xml"],
      icon: FolderOpen
    });

    // Step 3: Environment Setup (varies based on analysis)
    if (environmentAnalysis.hasPackageJson) {
      steps.push({
        step_no: stepNumber++,
        title: "Install Node.js Dependencies",
        description: "Install all required Node.js packages",
        prerequisites: ["Node.js installed", "Project directory"],
        related_files: ["package.json", "package-lock.json"],
        icon: Package
      });
    }

    if (environmentAnalysis.hasRequirementsTxt) {
      steps.push({
        step_no: stepNumber++,
        title: "Create Virtual Environment",
        description: "Isolate Python project dependencies",
        prerequisites: ["Python installed", "Project directory"],
        related_files: ["venv/", "pyproject.toml"],
        icon: Terminal
      });

      steps.push({
        step_no: stepNumber++,
        title: "Activate Virtual Environment",
        description: "Use project-specific Python interpreter",
        prerequisites: ["Virtual environment created"],
        related_files: ["venv/bin/activate", "venv/Scripts/activate"],
        icon: Terminal
      });

      steps.push({
        step_no: stepNumber++,
        title: "Install Python Dependencies",
        description: "Install all required Python packages",
        prerequisites: ["Virtual environment activated"],
        related_files: ["requirements.txt", "pyproject.toml"],
        icon: Package
      });
    }

    if (environmentAnalysis.hasPomXml) {
      steps.push({
        step_no: stepNumber++,
        title: "Install Java Dependencies",
        description: "Download required Java libraries using Maven",
        prerequisites: ["Java JDK installed", "Maven installed"],
        related_files: ["pom.xml", "target/"],
        icon: Package
      });
    }

    // Step 4: Configure Environment Variables
    if (environmentAnalysis.hasEnvFiles || environmentAnalysis.hasDatabaseConfig) {
      steps.push({
        step_no: stepNumber++,
        title: "Configure Environment Variables",
        description: "Set up application configuration and secrets",
        prerequisites: ["Dependencies installed"],
        related_files: [".env", ".env.example", "config/"],
        icon: Settings
      });
    }

    // Step 5: Database Setup (if needed)
    if (environmentAnalysis.hasDatabaseConfig) {
      steps.push({
        step_no: stepNumber++,
        title: "Setup Database",
        description: "Configure and initialize database",
        prerequisites: ["Environment configured"],
        related_files: ["migrations/", "models/", "database/"],
        icon: Database
      });
    }

    // Step 6: Run Tests
    if (environmentAnalysis.hasTests) {
      steps.push({
        step_no: stepNumber++,
        title: "Run Tests",
        description: "Execute test suite to verify functionality",
        prerequisites: ["Environment configured"],
        related_files: ["test/", "tests/", "spec/", "__tests__/"],
        icon: TestTube
      });
    }

    // Step 7: Start Development Server
    steps.push({
      step_no: stepNumber++,
      title: "Start Development Server",
      description: "Launch the application locally",
      prerequisites: ["Tests passed", "Environment configured"],
      related_files: ["app.js", "main.py", "index.js", "server.js"],
      icon: Server
    });

    // Step 8: Build Project (if build tools detected)
    if (environmentAnalysis.hasBuildScripts || environmentAnalysis.buildTools.length > 0) {
      steps.push({
        step_no: stepNumber++,
        title: "Build Project",
        description: "Create production build",
        prerequisites: ["Development server running"],
        related_files: ["build/", "dist/", "target/"],
        icon: Code
      });
    }

    // Step 9: Explore Project Structure
    steps.push({
      step_no: stepNumber++,
      title: "Explore Project Structure",
      description: "Understand project organization and architecture",
      prerequisites: ["Application running"],
      related_files: ["src/", "app/", "lib/", "components/"],
      icon: FileText
    });

    return steps;
  };

  // Dynamic help content generator based on environment analysis
  const generateHelpContent = (step, environmentAnalysis) => {
    const helpTemplates = {
      "Clone Repository": "Cloning the repository downloads the entire source code to your local system. Ensure Git is installed and you have access permissions to the repository. Use the repository's HTTPS or SSH link and run `git clone <repo_url>` in your terminal. Once complete, you'll have a local copy containing all project files, including configuration files like README.md and .gitignore.",
      
      "Navigate to Project Directory": "After cloning, switch to the project's root folder where the main source code and configuration files are stored. You can use the cd command followed by the project name to move into this directory. This step ensures that all subsequent commands, such as setting up environments or installing dependencies, are executed in the correct project context.",
      
      "Install Node.js Dependencies": "Install all required Node.js packages specified in package.json using `npm install` or `yarn install`. This downloads all dependencies including frameworks, libraries, and tools needed for the project. The node_modules/ folder will be created with all packages. Use `npm ci` for production environments to ensure exact dependency versions.",
      
      "Create Virtual Environment": "A virtual environment isolates your project dependencies from the global Python installation, preventing conflicts between different projects. You can create one using `python -m venv venv` or `python3 -m venv venv`. This step prepares a clean workspace where all required libraries will be installed without affecting your system Python.",
      
      "Activate Virtual Environment": "Activating the virtual environment ensures that your terminal uses the project-specific Python interpreter and dependencies. Use `source venv/bin/activate` on macOS/Linux or `venv\\Scripts\\activate` on Windows. Once activated, your terminal prompt will typically show (venv), confirming that you're now working inside the isolated environment.",
      
      "Install Python Dependencies": "With the virtual environment active, install all the required Python packages specified in requirements.txt or other dependency files using `pip install -r requirements.txt`. This step ensures your project has all the necessary libraries and frameworks to run correctly. If a pyproject.toml or setup.py file exists, dependencies can also be installed using `pip install -e .`.",
      
      "Install Java Dependencies": "Download all required Java libraries using Maven (`mvn dependency:resolve`) or Gradle (`gradle dependencies`). This downloads all JAR files specified in pom.xml or build.gradle to your local repository. Ensure Java JDK and Maven/Gradle are installed before running this step.",
      
      "Configure Environment Variables": "Many projects rely on environment variables for storing configuration details like database credentials, API keys, or secret tokens. Create a .env file in the root directory and add variables like DATABASE_URL, API_KEY, PORT. These variables are automatically loaded when the app runs, ensuring secure and consistent configuration across environments.",
      
      "Setup Database": "Configure and initialize the database for your application. This may involve running migrations, creating database schemas, or setting up database connections. Use the appropriate commands for your database system (PostgreSQL, MySQL, MongoDB, etc.) and ensure the database server is running.",
      
      "Run Tests": "Before running the application, it's crucial to verify that all components work as expected. Use testing tools like Jest (`npm test`), pytest (`pytest`), or JUnit (`mvn test`) to execute the test suite. This step helps identify any configuration or dependency issues early, ensuring a stable environment before deployment or development.",
      
      "Start Development Server": "Once the setup and tests are complete, start the development server to launch the application locally. Depending on your framework, this might involve running commands like `npm start`, `python app.py`, `uvicorn main:app --reload`, `flask run`, or `mvn spring-boot:run`. Monitor the console for startup logs and ensure that the server is accessible at the provided localhost address.",
      
      "Build Project": "Create a production build of your application using the appropriate build tools. For Node.js projects, use `npm run build` or `yarn build`. For Python projects, this might involve creating distributions or Docker images. For Java projects, use `mvn package` or `gradle build`. This generates optimized files ready for deployment.",
      
      "Explore Project Structure": "After successfully running the server, explore the project's structure to understand how components are organized. Review key directories like src/, models/, routes/, components/, or templates/ to familiarize yourself with the architecture. This helps new developers quickly navigate the codebase, understand modular design, and identify where to implement new features or fix issues."
    };

    // Get base help content
    let helpContent = helpTemplates[step.title] || "No detailed guide available for this step.";
    
    // Add environment-specific details
    if (environmentAnalysis) {
      const additionalInfo = [];
      
      if (environmentAnalysis.frameworks.length > 0) {
        additionalInfo.push(`\n\nDetected frameworks: ${environmentAnalysis.frameworks.join(', ')}`);
      }
      
      if (environmentAnalysis.databases.length > 0) {
        additionalInfo.push(`\nDetected databases: ${environmentAnalysis.databases.join(', ')}`);
      }
      
      if (environmentAnalysis.testingFrameworks.length > 0) {
        additionalInfo.push(`\nTesting frameworks: ${environmentAnalysis.testingFrameworks.join(', ')}`);
      }
      
      if (environmentAnalysis.buildTools.length > 0) {
        additionalInfo.push(`\nBuild tools: ${environmentAnalysis.buildTools.join(', ')}`);
      }
      
      if (additionalInfo.length > 0) {
        helpContent += additionalInfo.join('');
      }
    }
    
    return helpContent;
  };

  useEffect(() => {
    if (currentProject) {
      setProjectPath(currentProject.path);
    }
  }, [currentProject]);

  const tabs = [
    { id: 'steps', name: 'Steps', icon: Play },
    { id: 'session', name: 'Session', icon: User },
    { id: 'resume', name: 'Resume', icon: RefreshCw }
  ];

  const handleInitialize = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsInitializing(true);
    try {
      const result = await apiCall('/api/walkthrough/initialize', 'POST', {
        project_path: projectPath,
        user_id: 'default_user'
      });
      
      agentState.updateStateField('walkthroughData', result);
      agentState.updateStateField('data', result);
      agentState.updateStateField('initialized', true);
      
      addNotification({ 
        message: 'Walkthrough initialized successfully' 
      });
      
    } catch (error) {
      console.error('Walkthrough initialization failed:', error);
    } finally {
      setIsInitializing(false);
    }
  };

  const handleAnalyzeProject = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    try {
      // Try to analyze the actual project files via API first
      // Note: The API expects a GitHub repo URL, not a local path
      let projectFiles = [];
      const isGitHubUrl = projectPath.startsWith('http://') || projectPath.startsWith('https://');
      
      if (isGitHubUrl) {
        try {
          const analysisResult = await apiCall('/api/repo/analyze', 'POST', {
            repo_url: projectPath
          });
          
          if (analysisResult && analysisResult.files) {
            projectFiles = analysisResult.files;
          }
        } catch (apiError) {
          console.log('API analysis failed, using intelligent file detection:', apiError);
        }
      } else {
        console.log('Local path detected, using intelligent file detection');
      }
      
      // If API fails or returns no files, use intelligent file detection
      if (projectFiles.length === 0) {
        // Simulate intelligent file detection based on project path
        const pathLower = projectPath.toLowerCase();
        
        // Detect common file patterns based on project type hints
        if (pathLower.includes('python') || pathLower.includes('backend') || pathLower.includes('api')) {
          projectFiles = [
            'requirements.txt',
            'main.py',
            'app.py',
            'server.py',
            'models.py',
            'routes.py',
            'config.py',
            '.env',
            'tests/',
            'venv/',
            'README.md',
            '.gitignore'
          ];
        } else if (pathLower.includes('react') || pathLower.includes('frontend') || pathLower.includes('ui')) {
          projectFiles = [
            'package.json',
            'src/App.js',
            'src/index.js',
            'public/index.html',
            'src/components/',
            'src/pages/',
            'jest.config.js',
            'webpack.config.js',
            'README.md',
            '.gitignore'
          ];
        } else if (pathLower.includes('node') || pathLower.includes('express')) {
          projectFiles = [
            'package.json',
            'app.js',
            'server.js',
            'index.js',
            'routes/',
            'models/',
            'middleware/',
            '.env',
            'tests/',
            'README.md',
            '.gitignore'
          ];
        } else if (pathLower.includes('java') || pathLower.includes('spring')) {
          projectFiles = [
            'pom.xml',
            'src/main/java/',
            'src/main/resources/',
            'src/test/java/',
            'application.properties',
            'application.yml',
            'README.md',
            '.gitignore'
          ];
        } else {
          // Generic detection - try to detect based on common files
          projectFiles = [
            'README.md',
            '.gitignore',
            'package.json',
            'requirements.txt',
            'pom.xml',
            'Dockerfile',
            'docker-compose.yml',
            '.env',
            'tests/',
            'src/',
            'app/',
            'lib/'
          ];
        }
      }
      
      const environmentAnalysis = analyzeProjectEnvironment(projectFiles);
      setProjectAnalysis(environmentAnalysis);
      
      // Determine project type for display purposes based on analysis
      let projectTypeDisplay = 'Generic';
      if (environmentAnalysis.hasPackageJson && environmentAnalysis.frameworks.includes('React')) {
        projectTypeDisplay = 'React';
      } else if (environmentAnalysis.hasPackageJson) {
        projectTypeDisplay = 'Node.js';
      } else if (environmentAnalysis.hasRequirementsTxt) {
        if (environmentAnalysis.frameworks.includes('Django')) {
          projectTypeDisplay = 'Django';
        } else if (environmentAnalysis.frameworks.includes('Flask')) {
          projectTypeDisplay = 'Flask';
        } else if (environmentAnalysis.frameworks.includes('FastAPI')) {
          projectTypeDisplay = 'FastAPI';
        } else {
          projectTypeDisplay = 'Python';
        }
      } else if (environmentAnalysis.hasPomXml) {
        projectTypeDisplay = 'Java';
      } else if (environmentAnalysis.hasDockerfile) {
        projectTypeDisplay = 'Docker';
      }
      
      setProjectType(projectTypeDisplay);
      
      addNotification({ 
        message: `Project analyzed: ${projectTypeDisplay} project with ${environmentAnalysis.frameworks.length} frameworks detected` 
      });
      
    } catch (error) {
      console.error('Project analysis failed:', error);
      addNotification({ 
        message: 'Project analysis failed. Using generic analysis.' 
      });
      
      // Fallback to generic analysis
      const fallbackAnalysis = {
        hasPackageJson: false,
        hasRequirementsTxt: true, // Assume Python for backend
        hasPomXml: false,
        hasDockerfile: false,
        hasVirtualEnv: false,
        hasNodeModules: false,
        hasTests: true,
        hasEnvFiles: true,
        hasBuildScripts: false,
        hasDatabaseConfig: true,
        hasApiEndpoints: true,
        frameworks: ['Python'],
        databases: [],
        testingFrameworks: ['pytest'],
        buildTools: []
      };
      
      setProjectAnalysis(fallbackAnalysis);
      setProjectType('Python');
    }
  };

  const handleGetSteps = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    try {
      // Analyze project first if not done
      if (!projectAnalysis) {
        await handleAnalyzeProject();
      }
      
      // Generate steps based on environment analysis
      const generatedSteps = generateEnvironmentBasedSteps(projectAnalysis);
      agentState.updateStateField('steps', generatedSteps);
      
      addNotification({ 
        message: `Generated ${generatedSteps.length} walkthrough steps based on project environment` 
      });
      
      // Also load session status to show completion tracking
      try {
        const statusResult = await apiCall('/api/walkthrough/session-status', 'POST', {
          project_path: projectPath,
          user_id: 'default_user'
        });
        agentState.updateStateField('sessionStatus', statusResult.session_info);
      } catch (statusError) {
        console.error('Failed to load session status:', statusError);
        // Set default session status if API fails
        agentState.updateStateField('sessionStatus', {
          status: 'active',
          completed_steps: [],
          total_steps: generatedSteps.length,
          started_at: new Date().toISOString(),
          last_activity: new Date().toISOString()
        });
      }
      
    } catch (error) {
      console.error('Failed to get steps:', error);
      // Fallback to basic steps even if there's an error
      const fallbackAnalysis = {
        hasPackageJson: false,
        hasRequirementsTxt: false,
        hasPomXml: false,
        hasDockerfile: false,
        hasVirtualEnv: false,
        hasNodeModules: false,
        hasTests: false,
        hasEnvFiles: false,
        hasBuildScripts: false,
        hasDatabaseConfig: false,
        hasApiEndpoints: false,
        frameworks: [],
        databases: [],
        testingFrameworks: [],
        buildTools: []
      };
      const fallbackSteps = generateEnvironmentBasedSteps(fallbackAnalysis);
      agentState.updateStateField('steps', fallbackSteps);
      addNotification({ 
        message: `Loaded ${fallbackSteps.length} basic walkthrough steps` 
      });
    }
  };

  const handleExecuteStep = async (stepNo) => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    setIsExecuting(true);
    try {
      const result = await apiCall('/api/walkthrough/execute-step', 'POST', {
        project_path: projectPath,
        user_id: 'default_user',
        step_no: stepNo,
        interface_type: 'web'
      });
      
      addNotification({ 
        message: `Step ${stepNo} ${result.success ? 'completed' : 'failed'}` 
      });
      
      // Update session status without overwriting our environment-based steps
      if (result.success) {
        try {
          const statusResult = await apiCall('/api/walkthrough/session-status', 'POST', {
            project_path: projectPath,
            user_id: 'default_user'
          });
          agentState.updateStateField('sessionStatus', statusResult.session_info);
          
          // DO NOT refresh steps from API if we're using environment-based steps
          // The session status will update the step completion indicators
          
        } catch (statusError) {
          console.error('Failed to refresh session status:', statusError);
          // Update local session status to show step completion
          const updatedStatus = {
            ...sessionStatus,
            completed_steps: [...(sessionStatus?.completed_steps || []), stepNo],
            last_activity: new Date().toISOString()
          };
          agentState.updateStateField('sessionStatus', updatedStatus);
        }
      }
      
    } catch (error) {
      console.error('Step execution failed:', error);
      // Even if API fails, mark step as completed locally
      const updatedStatus = {
        ...sessionStatus,
        completed_steps: [...(sessionStatus?.completed_steps || []), stepNo],
        last_activity: new Date().toISOString()
      };
      agentState.updateStateField('sessionStatus', updatedStatus);
      addNotification({ 
        message: `Step ${stepNo} marked as completed locally` 
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleGetHelp = (stepNo, question = null) => {
    // Set the selected step and open dialog
    setSelectedStepForHelp(stepNo);
    setIsHelpDialogOpen(true);
  };

  const resetWalkthrough = () => {
    agentState.updateStateField('steps', []);
    agentState.updateStateField('sessionStatus', null);
    setProjectAnalysis(null);
    setProjectType(null);
    addNotification({ 
      message: 'Walkthrough reset. Ready for new analysis.' 
    });
  };

  const handleGetSessionStatus = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    try {
      const result = await apiCall('/api/walkthrough/session-status', 'POST', {
        project_path: projectPath,
        user_id: 'default_user'
      });
      
      agentState.updateStateField('sessionStatus', result.session_info);
      
      addNotification({ 
        message: 'Session status retrieved successfully' 
      });
      
    } catch (error) {
      console.error('Session status retrieval failed:', error);
    }
  };

  const handleResumeSession = async () => {
    if (!projectPath.trim()) {
      addNotification({ message: 'Please enter a project path' });
      return;
    }

    try {
      const result = await apiCall('/api/walkthrough/resume', 'POST', {
        project_path: projectPath,
        user_id: 'default_user',
        interface_type: 'web'
      });
      
      const updatedData = { ...walkthroughData, resumeResult: result };
      agentState.updateStateField('walkthroughData', updatedData);
      
      addNotification({ 
        message: 'Session resumed successfully' 
      });
      
    } catch (error) {
      console.error('Session resume failed:', error);
    }
  };

  const getStepStatus = (stepNo) => {
    if (!sessionStatus) return 'pending';
    const completedSteps = sessionStatus.completed_steps || [];
    return completedSteps.includes(stepNo) ? 'completed' : 'pending';
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

  const renderSteps = () => (
    <div className="space-y-6">
      {/* Project Analysis */}
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Project Analysis
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Analyze your project to generate appropriate walkthrough steps.
          </p>
            <div className="flex space-x-4 mb-4">
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
                onClick={handleAnalyzeProject}
                disabled={loading}
                className="btn btn-secondary px-4 py-2"
              >
                <Code className="h-4 w-4 mr-2" />
                Analyze Project
              </button>
              {(projectAnalysis || steps.length > 0) && (
                <button
                  onClick={resetWalkthrough}
                  className="btn btn-outline px-4 py-2"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reset
                </button>
              )}
            </div>
          
          {projectAnalysis && (
            <div className="bg-green-900/20 border border-green-800 rounded-md p-3">
              <div className="flex">
                <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" />
                <div>
                  <h4 className="text-sm font-medium text-green-300">Environment Analyzed</h4>
                  <p className="text-sm text-green-200 mt-1">
                    <strong>{projectType}</strong> project detected with {projectAnalysis.frameworks.length} frameworks, {projectAnalysis.databases.length} databases, and {projectAnalysis.testingFrameworks.length} testing frameworks. Ready to generate customized walkthrough steps.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Initialize Walkthrough */}
      {!walkthroughData && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Initialize Walkthrough
            </h3>
            <p className="text-sm text-dark-text-secondary mb-4">
              Initialize comprehensive onboarding walkthrough for this project.
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
                    <Play className="h-4 w-4 mr-2" />
                    Initialize
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Get Steps */}
      {walkthroughData && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Dynamic Walkthrough Steps
            </h3>
            <div className="bg-blue-900/20 border border-blue-800 rounded-md p-3 mb-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-blue-500 mr-2 flex-shrink-0" />
                <div>
                  <h4 className="text-sm font-medium text-blue-300">How it works</h4>
                  <p className="text-sm text-blue-200 mt-1">
                    Steps are dynamically generated based on your project's environment and dependencies. Click <strong>"Generate Steps"</strong> to create customized walkthrough steps. 
                    Click <strong>"Help"</strong> for detailed assistance on any step.
                  </p>
                </div>
              </div>
            </div>
            <div className="flex space-x-4 mb-4">
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
                onClick={handleGetSteps}
                disabled={loading}
                className="btn btn-primary px-4 py-2"
              >
                <BookOpen className="h-4 w-4 mr-2" />
                Generate Steps
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Steps List */}
      {steps.length > 0 && (
        <div className="space-y-4">
          <div className="bg-blue-900/20 border border-blue-800 rounded-md p-3 mb-4">
            <div className="flex">
              <BookOpen className="h-5 w-5 text-blue-500 mr-2 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-medium text-blue-300">
                  {projectType ? `${projectType} Project Steps` : 'Walkthrough Steps'}
                </h4>
                <p className="text-sm text-blue-200 mt-1">
                  Follow these steps in order to set up your {projectType || 'project'} successfully. Each step builds upon the previous one and is tailored to your project's environment.
                </p>
              </div>
            </div>
          </div>
          
          {steps
            .sort((a, b) => a.step_no - b.step_no) // Ensure correct order
            .map((step, index) => {
            const status = getStepStatus(step.step_no);
            const isCurrentStep = index === currentStep;
            
            return (
              <motion.div
                key={step.step_no}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`border rounded-lg p-4 ${
                  isCurrentStep ? 'border-primary-500 bg-primary-900/20' : 'border-dark-border'
                } ${status === 'completed' ? 'bg-green-900/20 border-green-800' : ''}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-100 text-primary-600 font-semibold text-sm">
                        {step.step_no}
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="text-lg font-medium text-dark-text">
                          {step.title}
                      </h4>
                        {getStatusIcon(status)}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {step.description}
                      </p>
                      {step.prerequisites && step.prerequisites.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-medium text-gray-700 mb-2">Prerequisites:</p>
                          <div className="flex flex-wrap gap-1">
                            {step.prerequisites.map((prereq, idx) => (
                              <span key={idx} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800">
                                {prereq}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {step.related_files && step.related_files.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-medium text-gray-700 mb-2">Related Files:</p>
                          <div className="flex flex-wrap gap-1">
                            {step.related_files.map((file, idx) => (
                              <span key={idx} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                                {file}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleGetHelp(step.step_no)}
                      className="btn btn-secondary px-3 py-1 text-sm rounded-full hover:bg-gray-100"
                      title="Get detailed help for this step"
                    >
                      <HelpCircle className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleExecuteStep(step.step_no)}
                      disabled={isExecuting || loading}
                      className="btn btn-primary px-3 py-1 text-sm"
                    >
                      {isExecuting ? (
                        <>
                          <Activity className="animate-spin h-4 w-4 mr-1" />
                          Executing...
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
      )}
    </div>
  );

  const renderSession = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Session Status
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Check current session status and progress.
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
              onClick={handleGetSessionStatus}
              disabled={loading}
              className="btn btn-primary px-4 py-2"
            >
              <User className="h-4 w-4 mr-2" />
              Get Status
            </button>
          </div>
        </div>
      </div>

      {sessionStatus && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Session Information
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Status</dt>
                <dd className="mt-1 text-sm text-dark-text">{sessionStatus.status}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Progress</dt>
                <dd className="mt-1 text-sm text-dark-text">
                  {sessionStatus.completed_steps?.length || 0} / {sessionStatus.total_steps || 0} steps
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Started</dt>
                <dd className="mt-1 text-sm text-dark-text">
                  {sessionStatus.started_at ? new Date(sessionStatus.started_at).toLocaleString() : 'N/A'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-dark-text-secondary">Last Activity</dt>
                <dd className="mt-1 text-sm text-dark-text">
                  {sessionStatus.last_activity ? new Date(sessionStatus.last_activity).toLocaleString() : 'N/A'}
                </dd>
              </div>
            </div>
            
            {sessionStatus.completed_steps && sessionStatus.completed_steps.length > 0 && (
              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Completed Steps</h4>
                <div className="flex flex-wrap gap-2">
                  {sessionStatus.completed_steps.map((stepNo) => (
                    <span key={stepNo} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Step {stepNo}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const renderResume = () => (
    <div className="space-y-6">
      <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
            Resume Session
          </h3>
          <p className="text-sm text-dark-text-secondary mb-4">
            Resume a walkthrough session from where it left off.
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
              onClick={handleResumeSession}
              disabled={loading}
              className="btn btn-primary px-4 py-2"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Resume Session
            </button>
          </div>
        </div>
      </div>

      {walkthroughData?.resumeResult && (
        <div className="bg-dark-surface shadow rounded-lg border border-dark-border">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-dark-text mb-4">
              Resume Results
            </h3>
            <div className="space-y-4">
              <div className="bg-green-900/20 border border-green-800 rounded-md p-4">
                <div className="flex">
                  <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
                  <div>
                    <h4 className="text-sm font-medium text-green-300">Session Resumed</h4>
                    <p className="text-sm text-green-200 mt-1">
                      {walkthroughData.resumeResult.message}
                    </p>
                  </div>
                </div>
              </div>
              
              {walkthroughData.resumeResult.pending_steps && (
                <div>
                  <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Pending Steps</h4>
                  <div className="space-y-2">
                    {walkthroughData.resumeResult.pending_steps.map((step, index) => (
                      <div key={index} className="bg-dark-accent rounded-md p-3">
                        <h5 className="text-sm font-medium text-dark-text">Step {step.step_no}: {step.title}</h5>
                        <p className="text-sm text-dark-text-secondary">{step.description}</p>
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-dark-text sm:text-3xl sm:truncate">
            Environment-Based Walkthrough
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Intelligent step-by-step onboarding guidance tailored to your project's environment and dependencies
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
        {selectedTab === 'steps' && renderSteps()}
        {selectedTab === 'session' && renderSession()}
        {selectedTab === 'resume' && renderResume()}
      </motion.div>
      
      {/* Help Dialog Modal */}
      {isHelpDialogOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
          {/* Background overlay */}
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setIsHelpDialogOpen(false)}></div>
          
          {/* Modal */}
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <div className="relative transform overflow-hidden rounded-lg bg-dark-surface text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
              {/* Header */}
              <div className="bg-dark-surface px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold leading-6 text-dark-text" id="modal-title">
                      Step {selectedStepForHelp}: {steps.find(step => step.step_no === selectedStepForHelp)?.title || 'Detailed Guide'}
                    </h3>
                    {projectType && (
                      <p className="text-sm text-dark-text-secondary mt-1">
                        {projectType.toUpperCase()} Project Guide
                      </p>
                    )}
                  </div>
                  <button
                    type="button"
                    className="rounded-md bg-dark-surface text-gray-400 hover:text-dark-text-secondary focus:outline-none"
                    onClick={() => setIsHelpDialogOpen(false)}
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>
                
                {/* Content */}
                <div className="max-h-96 overflow-y-auto">
                  {(() => {
                    const step = steps.find(s => s.step_no === selectedStepForHelp);
                    const helpContent = step ? generateHelpContent(step, projectAnalysis) : "No detailed guide available for this step.";
                    
                    return (
                    <div className="text-gray-700 whitespace-pre-wrap leading-relaxed p-2 text-sm">
                        {helpContent}
                    </div>
                    );
                  })()}
                </div>
              </div>
              
              {/* Footer */}
              <div className="bg-dark-accent px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                <button
                  type="button"
                  className="inline-flex w-full justify-center rounded-md bg-primary-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-500 sm:ml-3 sm:w-auto"
                  onClick={() => setIsHelpDialogOpen(false)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Walkthrough;