# ==============================
# rag_pipeline.py
# Comprehensive RAG Pipeline for QnA Agent
# Integrates Repository Analysis, Environment Setup, and Documentation Agents
# ==============================

import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

try:
    from agents.documentation.doc_generator import call_openrouter_llm, LLM_MODELS
    from utils.embeddings import get_weaviate_client, embed_text
    from agents.repo_analysis.analysis import analyze_repository
    from agents.environment_setup.container_builder import run_environment_setup
    from agents.documentation.doc_generator import DocumentationAgent
    from config import ENABLE_WEAVIATE, WEAVIATE_URL
except ImportError:
    # Allow running when executed as a script
    import os as _os, sys as _sys
    _BACKEND_DIR = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
    _PROJECT_ROOT = _os.path.dirname(_BACKEND_DIR)
    if _PROJECT_ROOT not in _sys.path:
        _sys.path.insert(0, _PROJECT_ROOT)
    from agents.documentation.doc_generator import call_openrouter_llm, LLM_MODELS  # type: ignore
    from utils.embeddings import get_weaviate_client, embed_text  # type: ignore
    from agents.repo_analysis.analysis import analyze_repository  # type: ignore
    from agents.environment_setup.container_builder import run_environment_setup  # type: ignore
    from agents.documentation.doc_generator import DocumentationAgent  # type: ignore
    from config import ENABLE_WEAVIATE, WEAVIATE_URL  # type: ignore


def _get_rfc3339_timestamp() -> str:
    """Get current timestamp in RFC3339 format for Weaviate."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class RAGPipeline:
    """
    Comprehensive RAG Pipeline that integrates:
    - Repository Analysis Agent (Phase 1)
    - Environment Setup Agent (Phase 2) 
    - Documentation Agent (Phase 3)
    
    Provides unified conversational interface for project understanding.
    """

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            raise ValueError(f"Base path {self.base_path} does not exist.")
        
        self.weaviate_client = None
        self.class_name = "ProjectKnowledge"
        self.doc_agent = DocumentationAgent(base_path)
        
        # Initialize Weaviate if enabled
        if ENABLE_WEAVIATE:
            self.weaviate_client = get_weaviate_client()
            if self.weaviate_client:
                self._ensure_schema_exists()

    def _ensure_schema_exists(self):
        """Ensure Weaviate schema exists, create if it doesn't."""
        try:
            # Check if using v4 API
            if hasattr(self.weaviate_client, 'collections'):
                # v4 API - check if collection exists
                try:
                    collection = self.weaviate_client.collections.get(self.class_name)
                    print(f"Schema {self.class_name} already exists - using existing schema (v4)")
                    return True
                except:
                    # Collection doesn't exist, create it
                    return self._create_schema()
            else:
                # v3 API - check if class exists
                existing_schema = self.weaviate_client.schema.get(self.class_name)
                print(f"Schema {self.class_name} already exists - using existing schema (v3)")
                
                # Check if the existing schema has the required fields
                required_fields = ["content", "source_type", "source_file", "timestamp"]
                existing_properties = [prop["name"] for prop in existing_schema.get("properties", [])]
                
                missing_fields = [field for field in required_fields if field not in existing_properties]
                if missing_fields:
                    print(f"Warning: Existing schema missing fields: {missing_fields}")
                    print("Some features may not work optimally. Consider using /qna/reset to recreate schema.")
                
                return True
        except Exception as e:
            print(f"Schema check failed: {e}")
            # Create new schema
            return self._create_schema()

    def _create_schema(self):
        """Create Weaviate schema for project knowledge."""
        try:
            # Check if using v4 API
            if hasattr(self.weaviate_client, 'collections'):
                # v4 API - create collection
                from weaviate.classes.config import Property, DataType
                self.weaviate_client.collections.create(
                    name=self.class_name,
                    description="Comprehensive project knowledge base",
                    properties=[
                        Property(name="content", data_type=DataType.TEXT),
                        Property(name="source_type", data_type=DataType.TEXT),
                        Property(name="source_file", data_type=DataType.TEXT),
                        Property(name="component_type", data_type=DataType.TEXT),
                        Property(name="file_type", data_type=DataType.TEXT),
                        Property(name="timestamp", data_type=DataType.DATE),
                    ]
                )
                print(f"Created new schema: {self.class_name} (v4)")
            else:
                # v3 API - create class
                schema = {
                    "class": self.class_name,
                    "description": "Comprehensive project knowledge base",
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "The text content"
                        },
                        {
                            "name": "source_type",
                            "dataType": ["string"],
                            "description": "Type of source (repo_analysis, env_setup, documentation, code)"
                        },
                        {
                            "name": "source_file",
                            "dataType": ["string"],
                            "description": "Source file or component"
                        },
                        {
                            "name": "component_type",
                            "dataType": ["string"],
                            "description": "Type of component (structure, component, dependencies, etc.)"
                        },
                        {
                            "name": "file_type",
                            "dataType": ["string"],
                            "description": "File extension or type"
                        },
                        {
                            "name": "timestamp",
                            "dataType": ["date"],
                            "description": "When this knowledge was indexed"
                        }
                    ]
                }
                self.weaviate_client.schema.create_class(schema)
                print(f"Created new schema: {self.class_name} (v3)")
            return True
        except Exception as e:
            print(f"Failed to create schema: {e}")
            return False

    def _clear_schema(self):
        """Clear existing schema and data (for development/testing)."""
        if not self.weaviate_client:
            return
        
        try:
            # Check if using v4 API
            if hasattr(self.weaviate_client, 'collections'):
                # v4 API - delete collection
                self.weaviate_client.collections.delete(self.class_name)
                print(f"Deleted schema: {self.class_name} (v4)")
            else:
                # v3 API - delete class
                self.weaviate_client.schema.delete(self.class_name)
                print(f"Deleted schema: {self.class_name} (v3)")
        except Exception as e:
            print(f"Error deleting schema: {e}")

    def reset_knowledge_base(self):
        """Reset the knowledge base by clearing schema and recreating it."""
        if not self.weaviate_client:
            print("Weaviate not available")
            return
        
        print("Resetting knowledge base...")
        self._clear_schema()
        self._ensure_schema_exists()
        print("Knowledge base reset complete")

    def index_project_knowledge(self) -> Dict[str, Any]:
        """
        Step 1: Comprehensive project indexing
        Integrates all three agents to build complete knowledge base.
        """
        results = {
            "repo_analysis": None,
            "env_setup": None,
            "documentation": None,
            "total_chunks": 0,
            "errors": []
        }

        try:
            # Phase 1: Repository Analysis
            print("Analyzing repository structure...")
            repo_analysis = analyze_repository(str(self.base_path))
            results["repo_analysis"] = repo_analysis
            self._index_repo_analysis(repo_analysis)
            results["total_chunks"] += self._count_chunks_in_analysis(repo_analysis)

        except Exception as e:
            error_msg = f"Repository analysis failed: {str(e)}"
            results["errors"].append(error_msg)
            print(f"ERROR: {error_msg}")

        try:
            # Phase 2: Environment Setup Analysis
            print("Analyzing environment setup...")
            env_result = run_environment_setup(str(self.base_path), build=False)
            results["env_setup"] = env_result.to_dict()
            self._index_env_setup(env_result)
            results["total_chunks"] += 3  # Dockerfile, devcontainer, sanity checks

        except Exception as e:
            error_msg = f"Environment setup analysis failed: {str(e)}"
            results["errors"].append(error_msg)
            print(f"ERROR: {error_msg}")

        try:
            # Phase 3: Documentation Analysis
            print("Analyzing documentation...")
            docs = self.doc_agent.collect_docs()
            docstrings = []
            for doc in docs:
                if doc.suffix == ".py":
                    docstrings.extend(self.doc_agent.extract_docstrings(doc))
            
            results["documentation"] = {
                "files_found": len(docs),
                "docstrings_extracted": len(docstrings)
            }
            self._index_documentation(docs, docstrings)
            results["total_chunks"] += len(docs) + len(docstrings)

        except Exception as e:
            error_msg = f"Documentation analysis failed: {str(e)}"
            results["errors"].append(error_msg)
            print(f"ERROR: {error_msg}")

        print(f"SUCCESS: Project knowledge indexed: {results['total_chunks']} chunks")
        return results

    def _index_repo_analysis(self, analysis: Dict[str, Any]):
        """Index repository analysis results."""
        if not self.weaviate_client:
            return

        # Index project structure
        if "structure" in analysis:
            structure_text = f"Project Structure: {json.dumps(analysis['structure'], indent=2)}"
            self._store_chunk(
                content=structure_text,
                source_type="repo_analysis",
                source_file="project_structure",
                metadata={"component": "structure"}
            )

        # Index components
        if "components" in analysis:
            for component in analysis["components"]:
                component_text = f"Component: {component.get('name', 'Unknown')}\nType: {component.get('type', 'Unknown')}\nDescription: {component.get('description', 'No description')}"
                self._store_chunk(
                    content=component_text,
                    source_type="repo_analysis",
                    source_file=component.get('file', 'unknown'),
                    metadata={"component": "component", "component_type": component.get('type')}
                )

        # Index dependencies
        if "dependencies" in analysis:
            deps_text = f"Dependencies: {json.dumps(analysis['dependencies'], indent=2)}"
            self._store_chunk(
                content=deps_text,
                source_type="repo_analysis",
                source_file="dependencies",
                metadata={"component": "dependencies"}
            )

    def _index_env_setup(self, env_result):
        """Index environment setup results."""
        if not self.weaviate_client:
            return

        # Index Dockerfile
        if env_result.dockerfile_path and Path(env_result.dockerfile_path).exists():
            dockerfile_content = Path(env_result.dockerfile_path).read_text(encoding="utf-8", errors="ignore")
            self._store_chunk(
                content=f"Dockerfile Configuration:\n{dockerfile_content}",
                source_type="env_setup",
                source_file="Dockerfile",
                metadata={"component": "containerization"}
            )

        # Index DevContainer config
        if env_result.devcontainer_path and Path(env_result.devcontainer_path).exists():
            devcontainer_content = Path(env_result.devcontainer_path).read_text(encoding="utf-8", errors="ignore")
            self._store_chunk(
                content=f"DevContainer Configuration:\n{devcontainer_content}",
                source_type="env_setup",
                source_file=".devcontainer/devcontainer.json",
                metadata={"component": "devcontainer"}
            )

        # Index sanity check results
        if env_result.sanity_logs:
            sanity_text = f"Environment Sanity Checks:\n{json.dumps(env_result.sanity_logs, indent=2)}"
            self._store_chunk(
                content=sanity_text,
                source_type="env_setup",
                source_file="sanity_checks",
                metadata={"component": "validation"}
            )

    def _index_documentation(self, docs: List[Path], docstrings: List[Dict]):
        """Index documentation and docstrings."""
        if not self.weaviate_client:
            return

        # Index documentation files
        for doc in docs:
            try:
                content = self.doc_agent.read_file(doc)
                if content.strip():
                    self._store_chunk(
                        content=content,
                        source_type="documentation",
                        source_file=str(doc.relative_to(self.base_path)),
                        metadata={"file_type": doc.suffix, "file_name": doc.name}
                    )
            except Exception as e:
                print(f"Error indexing {doc}: {e}")

        # Index docstrings
        for ds in docstrings:
            docstring_text = f"{ds['type'].title()}: {ds['name']}\nFile: {ds['file']}\n\n{ds['docstring']}"
            self._store_chunk(
                content=docstring_text,
                source_type="code_documentation",
                source_file=ds['file'],
                metadata={"type": ds['type'], "name": ds['name']}
            )

    def _store_chunk(self, content: str, source_type: str, source_file: str, metadata: Dict[str, Any] = None):
        """Store a knowledge chunk in Weaviate."""
        if not self.weaviate_client:
            return

        try:
            # Extract metadata fields
            component_type = metadata.get("component", "") if metadata else ""
            file_type = metadata.get("file_type", "") if metadata else ""
            
            # Build data object with only the fields that exist in the schema
            data_object = {
                "content": content,
                "source_type": source_type,
                "source_file": source_file,
                "timestamp": _get_rfc3339_timestamp()
            }
            
            # Add optional fields if they exist in the schema
            try:
                # Try to add component_type and file_type
                if component_type:
                    data_object["component_type"] = component_type
                if file_type:
                    data_object["file_type"] = file_type
            except:
                # If these fields don't exist in the schema, continue without them
                pass
            
            # Check if using v4 API
            if hasattr(self.weaviate_client, 'collections'):
                # v4 API
                collection = self.weaviate_client.collections.get(self.class_name)
                collection.data.insert(data_object)
            else:
                # v3 API
                self.weaviate_client.data_object.create(
                    data_object=data_object,
                    class_name=self.class_name
                )
        except Exception as e:
            print(f"Error storing chunk: {e}")

    def _count_chunks_in_analysis(self, analysis: Dict[str, Any]) -> int:
        """Count estimated chunks from analysis."""
        count = 0
        if "structure" in analysis:
            count += 1
        if "components" in analysis:
            count += len(analysis["components"])
        if "dependencies" in analysis:
            count += 1
        return count

    def retrieve_relevant_context(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Step 2: Retrieve relevant context from all knowledge sources
        """
        if not self.weaviate_client:
            return []

        try:
            # Try to get all fields, but handle cases where some might not exist
            fields = ["content", "source_type", "source_file"]
            
            # Try to add optional fields
            try:
                fields.extend(["component_type", "file_type"])
            except:
                pass
            
            # Check if using v4 API
            if hasattr(self.weaviate_client, 'collections'):
                # v4 API
                collection = self.weaviate_client.collections.get(self.class_name)
                response = collection.query.near_text(
                    query=query,
                    limit=top_k
                )
                chunks = []
                for obj in response.objects:
                    chunks.append(obj.properties)
                return chunks
            else:
                # v3 API
                response = (
                    self.weaviate_client.query
                    .get(self.class_name, fields)
                    .with_near_text({"concepts": [query]})
                    .with_limit(top_k)
                    .do()
                )
                chunks = response.get("data", {}).get("Get", {}).get(self.class_name, [])
                return chunks
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []

    def generate_comprehensive_answer(self, query: str, context_chunks: List[Dict[str, Any]], conversation_history: List[Dict] = None) -> str:
        """
        Step 3: Generate comprehensive answer using RAG + LLM reasoning
        """
        # Build context from retrieved chunks
        context_text = ""
        source_types = set()
        
        for chunk in context_chunks:
            source_type = chunk.get("source_type", "unknown")
            source_file = chunk.get("source_file", "unknown")
            component_type = chunk.get("component_type", "")
            file_type = chunk.get("file_type", "")
            content = chunk.get("content", "")
            source_types.add(source_type)
            
            # Build descriptive header
            header = f"{source_type.upper()}: {source_file}"
            if component_type:
                header += f" ({component_type})"
            if file_type:
                header += f" [{file_type}]"
            
            context_text += f"\n\n--- {header} ---\n{content}"

        # Build conversation history context
        history_context = ""
        if conversation_history:
            history_context = "\n\nPrevious conversation:\n"
            for conv in conversation_history[-3:]:  # Last 3 exchanges
                history_context += f"Q: {conv.get('question', '')}\nA: {conv.get('answer', '')}\n"

        # Create comprehensive prompt
        prompt = f"""You are an expert AI assistant with comprehensive knowledge of this project. 
You have access to repository analysis, environment setup, and documentation information.

{history_context}

User Question: {query}

Relevant Project Context:
{context_text[:8000]}

Instructions:
1. Provide a comprehensive, accurate answer based on the project context
2. If the question relates to:
   - Code structure/architecture → Use repository analysis data
   - Environment setup/Docker → Use environment setup data  
   - Documentation/APIs → Use documentation data
3. Include specific file paths, code snippets, or commands when relevant
4. If you need to suggest actions, provide step-by-step instructions
5. Be conversational but professional
6. If information is incomplete, mention what's missing

Answer:"""

        return call_openrouter_llm(prompt, temperature=0.3, max_tokens=1500)

    def answer_query(self, query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Main method: Complete RAG pipeline for answering queries
        """
        try:
            # Step 2: Retrieve relevant context
            context_chunks = self.retrieve_relevant_context(query)
            
            if not context_chunks:
                # Fallback to documentation agent if no context found
                return {
                    "answer": self.doc_agent.query_docs(query),
                    "sources": [],
                    "method": "fallback_documentation"
                }

            # Step 3: Generate comprehensive answer
            answer = self.generate_comprehensive_answer(query, context_chunks, conversation_history)
            
            # Extract sources
            sources = []
            for chunk in context_chunks:
                sources.append({
                    "type": chunk.get("source_type", "unknown"),
                    "file": chunk.get("source_file", "unknown"),
                    "component_type": chunk.get("component_type", ""),
                    "file_type": chunk.get("file_type", "")
                })

            return {
                "answer": answer,
                "sources": sources,
                "method": "rag_comprehensive",
                "context_chunks_used": len(context_chunks)
            }

        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "method": "error"
            }

    def get_project_summary(self) -> Dict[str, Any]:
        """Get a comprehensive project summary."""
        try:
            # Quick analysis without full indexing
            docs = self.doc_agent.collect_docs()
            docstrings = []
            for doc in docs:
                if doc.suffix == ".py":
                    docstrings.extend(self.doc_agent.extract_docstrings(doc))

            return {
                "project_path": str(self.base_path),
                "documentation_files": len(docs),
                "code_docstrings": len(docstrings),
                "weaviate_enabled": self.weaviate_client is not None,
                "knowledge_base_ready": self.weaviate_client is not None
            }
        except Exception as e:
            return {
                "project_path": str(self.base_path),
                "error": str(e),
                "knowledge_base_ready": False
            }


# ==============================
# 🚀 CLI / Example usage
# ==============================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python rag_pipeline.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    rag = RAGPipeline(project_path)
    
    print("🔍 Indexing project knowledge...")
    results = rag.index_project_knowledge()
    print(f"✅ Indexed {results['total_chunks']} knowledge chunks")
    
    print("\n💬 Q&A Session (type 'quit' to exit):")
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() in ['quit', 'exit']:
            break
        
        result = rag.answer_query(question)
        print(f"\nAnswer: {result['answer']}")
        if result['sources']:
            print(f"\nSources: {len(result['sources'])} relevant chunks")
