# State Persistence Across Routes - Implementation Guide

## ✅ What Has Been Done

### 1. Enhanced AppContext (`src/context/AppContext.js`)
- **Added sessionStorage persistence** - State automatically saves to browser sessionStorage
- **Added state restoration** - State is restored when app reloads
- **Extended agent state structure** - Each agent now stores more comprehensive state
- **Added helper methods**:
  - `updateAgentDeep()` - Deep state updates
  - `clearAgentState()` - Clear an agent's state
  - `resetAllAgents()` - Reset all agents

### 2. Created useAgentState Hook (`src/hooks/useAgentState.js`)
A custom hook that makes it easy to manage persistent agent state:
```javascript
const agentState = useAgentState('repository');

// Access state
const data = agentState.state.analysisData;

// Update state
agentState.updateStateField('analysisData', newData);
```

### 3. Updated Pages
- ✅ **RepositoryAnalysis.js** - Now uses persistent state
- ✅ **QnA.js** - Now uses persistent state
- ⚠️ **Remaining pages need similar updates** (see below)

## 🔄 How to Update Remaining Pages

### Pattern to Follow

1. **Import the hook:**
```javascript
import useAgentState from '../hooks/useAgentState';
```

2. **Replace local state with persistent state:**
```javascript
// OLD WAY:
const [analysisData, setAnalysisData] = useState(null);

// NEW WAY:
const agentState = useAgentState('repository'); // or 'qna', 'environment', etc.
const analysisData = agentState.state.analysisData;
```

3. **Update state using the hook:**
```javascript
// OLD WAY:
setAnalysisData(result);

// NEW WAY:
agentState.updateStateField('analysisData', result);
agentState.updateStateField('initialized', true);
```

### Pages That Need Updates

#### Feedback.js
- Map `feedbackData` → `agents.feedback.feedbackData`
- Keep form state local (user input)
- Persist API results to context

#### Documentation.js
- Map `documentationData` → `agents.documentation.documentationData`
- Keep query/form state local
- Persist generated docs to context

#### EnvironmentSetup.js
- Map `environmentData` → `agents.environment.environmentData`
- Keep project path local
- Persist analysis results to context

#### Walkthrough.js
- Map `walkthroughData` → `agents.walkthrough.walkthroughData`
- Map `steps` → `agents.walkthrough.steps`
- Map `sessionStatus` → `agents.walkthrough.sessionStatus`
- Keep current step and UI state local

#### CICD.js
- Map `cicdData` → `agents.cicd.cicdData`
- Keep form credentials local (for security)
- Persist analysis results to context

## 🎯 How It Works

1. **State Storage**: All agent state is stored in `AppContext.agents`
2. **Automatic Persistence**: Every state change is saved to `sessionStorage`
3. **Automatic Restoration**: On page reload, state is restored from `sessionStorage`
4. **Route Navigation**: State persists when navigating between routes because it's in context

## 🧪 Testing

1. Open an agent page (e.g., Repository Analysis)
2. Perform an action that generates data
3. Navigate to a different route
4. Navigate back - **data should still be there!**
5. Refresh the page - **data should persist!**

## 🗑️ Clearing State

To clear state for a specific agent:
```javascript
agentState.replaceState({ initialized: false, data: null });
```

To clear all agent state:
```javascript
const { resetAllAgents } = useApp();
resetAllAgents();
```

## 🔧 Troubleshooting

### Issue: State not persisting
- Check browser console for errors
- Verify sessionStorage is enabled
- Check that `updateStateField` is being called correctly

### Issue: State persists after logout
- Call `resetAllAgents()` on logout
- Or clear `sessionStorage.removeItem('aide-app-state')`

## 📝 Notes

- **sessionStorage** is used instead of localStorage:
  - Clears when browser tab closes
  - More secure (doesn't persist across sessions)
  - Perfect for temporary app state

- **What Gets Persisted**:
  - Agent data and results
  - Initialization status
  - Conversation history (for QnA)
  - NOT persisted: loading states, error states, UI state

- **Performance**: 
  - State is debounced to avoid excessive writes
  - Uses JSON serialization (works with all standard types)

