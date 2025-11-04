# AI Developer Onboarding Engine (AIDE) - Frontend

A comprehensive React.js frontend for the AI Developer Onboarding Engine, providing an intuitive interface for all backend AI agents and features.

## 🚀 Features

### Core Agents Integration
- **Repository Analysis Agent** - Analyze code structure, dependencies, and frameworks
- **Environment Setup Agent** - Docker containers, DevContainer, and runtime setup
- **Documentation Agent** - Generate docs and RAG-based knowledge queries
- **Q&A Assistant** - Conversational interface with project knowledge
- **Walkthrough Agent** - Step-by-step onboarding guidance
- **CI/CD Agent** - GitHub Actions, Jenkins, and diagnostics
- **Feedback Agent** - Analytics, learning, and model retraining

### UI/UX Features
- **Modern Design** - Clean, professional interface with Tailwind CSS
- **Responsive Layout** - Works on desktop, tablet, and mobile devices
- **Real-time Updates** - Live connection status and progress tracking
- **Interactive Components** - Rich forms, charts, and data visualization
- **Smooth Animations** - Framer Motion for polished user experience
- **Dark/Light Theme** - Customizable appearance (ready for implementation)

## 🛠️ Technology Stack

- **React 19** - Latest React with modern features
- **React Router DOM** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Framer Motion** - Animation library
- **Axios** - HTTP client for API calls
- **React Hot Toast** - Notification system
- **React Markdown** - Markdown rendering
- **React Syntax Highlighter** - Code syntax highlighting
- **Recharts** - Data visualization charts
- **Lucide React** - Modern icon library

## 📦 Installation

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm start
   ```

3. **Build for Production**
   ```bash
   npm run build
   ```

## 🏗️ Project Structure

```
src/
├── components/
│   └── Layout.js              # Main layout with sidebar navigation
├── context/
│   └── AppContext.js          # Global state management
├── pages/
│   ├── Dashboard.js           # Main dashboard overview
│   ├── RepositoryAnalysis.js  # Repository analysis interface
│   ├── EnvironmentSetup.js    # Environment setup wizard
│   ├── Documentation.js       # Documentation generation & queries
│   ├── QnA.js                # Q&A chat interface
│   ├── Walkthrough.js        # Step-by-step walkthrough
│   ├── CICD.js               # CI/CD management
│   ├── Feedback.js           # Feedback collection & analytics
│   └── Settings.js           # Application settings
├── App.js                    # Main application component
├── index.css                 # Global styles with Tailwind
└── index.js                  # Application entry point
```

## 🎨 Design System

### Color Palette
- **Primary**: Blue (#3b82f6) - Main actions and highlights
- **Secondary**: Gray (#64748b) - Secondary elements
- **Success**: Green (#10b981) - Success states
- **Warning**: Yellow (#f59e0b) - Warning states
- **Error**: Red (#ef4444) - Error states

### Typography
- **Headings**: Inter font family
- **Body**: System font stack
- **Code**: Monaco, Consolas, monospace

### Components
- **Buttons**: Primary, secondary, and ghost variants
- **Cards**: Consistent shadow and border radius
- **Forms**: Accessible input components
- **Navigation**: Sidebar with active states
- **Charts**: Responsive data visualization

## 🔌 Backend Integration

The frontend integrates with the AIDE backend through RESTful APIs:

### API Endpoints
- `GET /healthz` - Health check
- `GET /readyz` - Readiness check
- `POST /api/repo/analyze` - Repository analysis
- `POST /api/env/environment/*` - Environment setup
- `POST /api/documentation/*` - Documentation management
- `POST /api/qna/*` - Q&A operations
- `POST /api/walkthrough/*` - Walkthrough management
- `POST /api/ci-cd/*` - CI/CD operations
- `POST /api/feedback/*` - Feedback collection

### State Management
- **Context API** - Global application state
- **Local State** - Component-specific state
- **API Integration** - Centralized API calls
- **Error Handling** - Comprehensive error management
- **Loading States** - User feedback during operations

## 📱 Responsive Design

### Breakpoints
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

### Layout Adaptations
- **Mobile**: Stacked layout, collapsible sidebar
- **Tablet**: Sidebar overlay, optimized spacing
- **Desktop**: Full sidebar, multi-column layouts

## 🎯 Key Features

### Dashboard
- **System Overview** - Backend connection status
- **Agent Status** - Individual agent initialization status
- **Project Selection** - Easy project path input
- **Quick Actions** - Direct access to main features

### Repository Analysis
- **Multi-tab Interface** - Overview, Structure, Dependencies, Frameworks, CI/CD
- **Statistics Cards** - Files scanned, parsed, embedded
- **Code Highlighting** - Syntax-highlighted code blocks
- **Error Reporting** - Detailed error and skipped file information

### Environment Setup
- **Step-by-step Wizard** - Guided environment setup
- **Runtime Detection** - Automatic runtime and dependency detection
- **Docker Integration** - Container build and validation
- **Status Monitoring** - Real-time setup progress

### Documentation
- **Generate Docs** - README and API documentation generation
- **Query Interface** - RAG-based documentation queries
- **Ingest Management** - Weaviate integration for knowledge base
- **Schema Management** - Reset and manage documentation schemas

### Q&A Assistant
- **Chat Interface** - Conversational project understanding
- **Intent Analysis** - Question intent recognition
- **Follow-up Suggestions** - Intelligent question suggestions
- **Conversation History** - Persistent chat history
- **Source Attribution** - RAG source references

### Walkthrough
- **Interactive Steps** - Guided onboarding process
- **Session Management** - Resume and track progress
- **Context Help** - Step-specific assistance
- **Progress Tracking** - Visual progress indicators

### CI/CD Management
- **GitHub Actions** - Workflow analysis and triggering
- **Jenkins Integration** - Pipeline analysis and job management
- **Failure Diagnosis** - LLM-powered error analysis
- **Validation Tools** - Configuration validation

### Feedback & Learning
- **Feedback Collection** - Multi-type feedback forms
- **Analytics Dashboard** - Performance metrics and trends
- **Model Retraining** - Automated model improvement
- **Data Visualization** - Charts and performance graphs

### Settings
- **Connection Management** - Backend and database configuration
- **Performance Tuning** - Optimization settings
- **Security Settings** - Authentication and privacy controls
- **Notification Preferences** - User notification management

## 🚀 Getting Started

1. **Prerequisites**
   - Node.js 18+ 
   - npm or yarn
   - AIDE Backend running on localhost:8000

2. **Installation**
   ```bash
   cd reactaide
   npm install
   ```

3. **Development**
   ```bash
   npm start
   ```
   Opens http://localhost:3000

4. **Production Build**
   ```bash
   npm run build
   ```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_WEAVIATE_URL=http://localhost:8080
REACT_APP_ENABLE_WEAVIATE=true
```

### Backend Connection
The frontend automatically connects to the backend on startup. Ensure the AIDE backend is running on the configured URL.

## 📊 Performance

### Optimization Features
- **Code Splitting** - Lazy loading of components
- **Memoization** - React.memo for expensive components
- **Bundle Analysis** - Webpack bundle analyzer integration
- **Image Optimization** - Responsive image loading
- **Caching** - API response caching

### Monitoring
- **Error Boundaries** - Graceful error handling
- **Performance Metrics** - Core Web Vitals tracking
- **User Analytics** - Usage pattern analysis
- **API Monitoring** - Backend connection health

## 🧪 Testing

### Test Setup
```bash
npm test
```

### Test Coverage
- **Unit Tests** - Component testing
- **Integration Tests** - API integration testing
- **E2E Tests** - Full user workflow testing
- **Accessibility Tests** - WCAG compliance testing

## 🚀 Deployment

### Build for Production
```bash
npm run build
```

### Deployment Options
- **Static Hosting** - Netlify, Vercel, GitHub Pages
- **Docker** - Containerized deployment
- **CDN** - Global content delivery
- **Cloud Platforms** - AWS, GCP, Azure

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- **Documentation** - Check the README and inline comments
- **Issues** - GitHub Issues for bug reports
- **Discussions** - GitHub Discussions for questions
- **Community** - Join our developer community

## 🔮 Roadmap

### Upcoming Features
- **Dark Mode** - Theme switching capability
- **Offline Support** - Progressive Web App features
- **Advanced Analytics** - Enhanced data visualization
- **Plugin System** - Extensible architecture
- **Multi-language** - Internationalization support
- **Voice Interface** - Speech-to-text integration
- **Mobile App** - React Native companion app

---

**Built with ❤️ for the developer community**