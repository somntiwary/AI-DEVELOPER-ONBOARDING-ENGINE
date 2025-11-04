# ==============================
# qna_agent.py
# Professional QnA Agent with Conversational Memory
# Integrates all three phases into cohesive conversational layer
# ==============================

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from agents.qna_agent.rag_pipeline import RAGPipeline
    from agents.qna_agent.memory_manager import MemoryManager
    from agents.documentation.doc_generator import call_openrouter_llm
except ImportError:
    # Allow running when executed as a script
    import os as _os, sys as _sys
    _BACKEND_DIR = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
    _PROJECT_ROOT = _os.path.dirname(_BACKEND_DIR)
    if _PROJECT_ROOT not in _sys.path:
        _sys.path.insert(0, _PROJECT_ROOT)
    from agents.qna_agent.rag_pipeline import RAGPipeline  # type: ignore
    from agents.qna_agent.memory_manager import MemoryManager  # type: ignore
    from agents.documentation.doc_generator import call_openrouter_llm  # type: ignore


class QnAAgent:
    """
    Professional QnA Agent that provides conversational interface to project knowledge.
    
    Features:
    - Integrates Repository Analysis, Environment Setup, and Documentation
    - Conversational memory for follow-up queries
    - Context-aware responses using RAG
    - Professional project understanding
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        if not self.project_path.exists():
            raise ValueError(f"Project path {self.project_path} does not exist.")
        
        # Initialize components
        self.rag_pipeline = RAGPipeline(str(self.project_path))
        self.memory_manager = MemoryManager(str(self.project_path))
        
        # Session state
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.conversation_history = []
        self.knowledge_indexed = False

    def initialize_knowledge_base(self) -> Dict[str, Any]:
        """
        Initialize the comprehensive knowledge base by indexing all project information.
        This integrates all three agents (Repository Analysis, Environment Setup, Documentation).
        """
        print("Initializing comprehensive project knowledge base...")
        
        try:
            # Index all project knowledge
            results = self.rag_pipeline.index_project_knowledge()
            self.knowledge_indexed = True
            
            # Store initialization in memory
            self.memory_manager.add_conversation(
                question="[SYSTEM] Knowledge base initialization",
                answer=f"Successfully indexed {results['total_chunks']} knowledge chunks from repository analysis, environment setup, and documentation."
            )
            
            return {
                "status": "success",
                "message": "Knowledge base initialized successfully",
                "chunks_indexed": results["total_chunks"],
                "errors": results.get("errors", []),
                "session_id": self.session_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to initialize knowledge base: {str(e)}",
                "session_id": self.session_id
            }

    def ask_question(self, question: str, include_sources: bool = True) -> Dict[str, Any]:
        """
        Main method for asking questions about the project.
        
        Args:
            question: The user's question
            include_sources: Whether to include source information in response
            
        Returns:
            Comprehensive answer with context and sources
        """
        try:
            # Load conversation history for context
            recent_conversations = self.memory_manager.get_recent_conversations(limit=5)
            
            # Get answer using RAG pipeline
            result = self.rag_pipeline.answer_query(question, recent_conversations)
            
            # Store in conversation history
            self.conversation_history.append({
                "question": question,
                "answer": result["answer"],
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "method": result.get("method", "unknown")
            })
            
            # Store in persistent memory
            self.memory_manager.add_conversation(question, result["answer"])
            
            # Prepare response
            response = {
                "question": question,
                "answer": result["answer"],
                "session_id": self.session_id,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "method": result.get("method", "unknown")
            }
            
            if include_sources and result.get("sources"):
                response["sources"] = result["sources"]
                response["context_chunks_used"] = result.get("context_chunks_used", 0)
            
            return response
            
        except Exception as e:
            error_response = {
                "question": question,
                "answer": f"Sorry, I encountered an error processing your question: {str(e)}",
                "session_id": self.session_id,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "method": "error"
            }
            
            # Store error in memory
            self.memory_manager.add_conversation(question, error_response["answer"])
            
            return error_response

    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        return self.memory_manager.get_recent_conversations(limit)

    def get_project_summary(self) -> Dict[str, Any]:
        """Get comprehensive project summary."""
        summary = self.rag_pipeline.get_project_summary()
        summary.update({
            "session_id": self.session_id,
            "knowledge_indexed": self.knowledge_indexed,
            "conversation_count": len(self.conversation_history)
        })
        return summary

    def suggest_follow_up_questions(self, current_question: str, current_answer: str) -> List[str]:
        """
        Generate intelligent follow-up question suggestions based on current context.
        """
        try:
            prompt = f"""Based on this Q&A exchange, suggest 3-5 intelligent follow-up questions that would help the user understand the project better.

Current Question: {current_question}
Current Answer: {current_answer}

Suggest follow-up questions that:
1. Dive deeper into specific aspects mentioned
2. Ask about related components or features
3. Request practical examples or next steps
4. Explore connections to other parts of the project

Return only the questions, one per line, without numbering or bullets."""

            suggestions_text = call_openrouter_llm(prompt, temperature=0.7, max_tokens=300)
            
            # Parse suggestions
            suggestions = [q.strip() for q in suggestions_text.split('\n') if q.strip()]
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            # Fallback suggestions
            return [
                "Can you explain more about the project structure?",
                "How do I set up the development environment?",
                "What are the main API endpoints?",
                "How do I run the tests?",
                "What dependencies does this project have?"
            ]

    def analyze_question_intent(self, question: str) -> Dict[str, Any]:
        """
        Analyze the intent of the question to provide better context.
        """
        try:
            prompt = f"""Analyze this question about a software project and determine its intent:

Question: "{question}"

Classify the intent into one of these categories:
- code_structure: Questions about code organization, architecture, modules
- environment_setup: Questions about setup, installation, configuration
- documentation: Questions about APIs, usage, examples
- troubleshooting: Questions about errors, debugging, issues
- workflow: Questions about development process, CI/CD, deployment
- general: General questions about the project

Also identify key topics and suggest which agent (repo_analysis, env_setup, documentation) would be most relevant.

Respond in JSON format:
{{
    "intent": "category",
    "topics": ["topic1", "topic2"],
    "relevant_agent": "agent_name",
    "complexity": "simple|medium|complex"
}}"""

            analysis_text = call_openrouter_llm(prompt, temperature=0.2, max_tokens=200)
            
            # Try to parse JSON response
            try:
                return json.loads(analysis_text)
            except:
                # Fallback analysis
                return {
                    "intent": "general",
                    "topics": ["project"],
                    "relevant_agent": "documentation",
                    "complexity": "medium"
                }
                
        except Exception as e:
            return {
                "intent": "general",
                "topics": ["project"],
                "relevant_agent": "documentation",
                "complexity": "medium",
                "error": str(e)
            }

    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get information about what the QnA agent can do."""
        return {
            "capabilities": [
                "Repository structure analysis",
                "Environment setup guidance",
                "Documentation queries",
                "Code explanation",
                "API endpoint discovery",
                "Dependency analysis",
                "Development workflow guidance",
                "Troubleshooting assistance"
            ],
            "integrated_agents": [
                "Repository Analysis Agent (Phase 1)",
                "Environment Setup Agent (Phase 2)",
                "Documentation Agent (Phase 3)"
            ],
            "features": [
                "Conversational memory",
                "Context-aware responses",
                "RAG-based knowledge retrieval",
                "Follow-up question suggestions",
                "Intent analysis",
                "Source attribution"
            ],
            "knowledge_base_ready": self.knowledge_indexed
        }


# ==============================
# 🚀 CLI / Example usage
# ==============================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python qna_agent.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    # Initialize QnA Agent
    agent = QnAAgent(project_path)
    
    # Initialize knowledge base
    print("Initializing knowledge base...")
    init_result = agent.initialize_knowledge_base()
    print(f"SUCCESS: {init_result['message']}")
    
    if init_result['status'] == 'success':
        print(f"Indexed {init_result['chunks_indexed']} knowledge chunks")
    
    # Interactive Q&A session
    print("\nInteractive Q&A Session")
    print("Type 'quit' to exit, 'summary' for project summary, 'capabilities' for agent info")
    
    while True:
        question = input("\nYour question: ").strip()
        
        if question.lower() in ['quit', 'exit']:
            break
        elif question.lower() == 'summary':
            summary = agent.get_project_summary()
            print(f"\n📋 Project Summary: {json.dumps(summary, indent=2)}")
            continue
        elif question.lower() == 'capabilities':
            capabilities = agent.get_agent_capabilities()
            print(f"\n🛠️ Agent Capabilities: {json.dumps(capabilities, indent=2)}")
            continue
        
        if not question:
            continue
        
        # Analyze question intent
        intent = agent.analyze_question_intent(question)
        print(f"\nIntent: {intent['intent']} | Topics: {', '.join(intent['topics'])}")
        
        # Get answer
        result = agent.ask_question(question)
        print(f"\nAnswer: {result['answer']}")
        
        if result.get('sources'):
            print(f"\nSources: {len(result['sources'])} relevant chunks")
        
        # Suggest follow-ups
        suggestions = agent.suggest_follow_up_questions(question, result['answer'])
        if suggestions:
            print(f"\nSuggested follow-ups:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. {suggestion}")
