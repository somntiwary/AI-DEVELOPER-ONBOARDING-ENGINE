# doc_routes.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, List

try:
    # Try importing as if running from project root
    from agents.documentation.doc_generator import DocumentationAgent
    from agents.documentation.query_engine import QueryEngine
    from utils.embeddings import get_weaviate_client
    from config import WEAVIATE_URL, ENABLE_WEAVIATE
except ImportError:
    # Import directly when running from backend directory
    from agents.documentation.doc_generator import DocumentationAgent
    from agents.documentation.query_engine import QueryEngine
    from utils.embeddings import get_weaviate_client
    from config import WEAVIATE_URL, ENABLE_WEAVIATE

router = APIRouter(prefix="/documentation", tags=["Documentation Agent"])

# ==============================
# Request models
# ==============================
class GenerateDocsRequest(BaseModel):
    project_path: str  # Path to the user's project repo

class QueryDocsRequest(BaseModel):
    project_path: str
    question: str


# ==============================
# Routes
# ==============================
@router.post("/generate")
def generate_docs(request: GenerateDocsRequest):
    """
    Generates comprehensive documentation (README, API docs) for a given project path.
    """
    project_path = Path(request.project_path)
    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid project path.")

    agent = DocumentationAgent(base_path=project_path)
    try:
        # Generate README
        readme_path = agent.generate_readme()
        
        # Generate API documentation
        api_docs_path = agent.generate_api_docs()
        
        return {
            "status": "success", 
            "message": "Documentation generated successfully.", 
            "readme_path": str(readme_path),
            "api_docs_path": str(api_docs_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate documentation: {str(e)}")


@router.post("/query")
def query_docs(request: QueryDocsRequest):
    """
    Answers a question about the project's documentation using RAG or fallback to LLM.
    """
    project_path = Path(request.project_path)
    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid project path.")

    try:
        if ENABLE_WEAVIATE:
            # Try RAG with Weaviate first
            try:
                query_engine = QueryEngine(weaviate_url=WEAVIATE_URL)
                answer = query_engine.query(request.question)
                
                # Check if we got a meaningful answer
                if "❌ No relevant documentation chunks found" in answer:
                    # Fallback to LLM with project context
                    agent = DocumentationAgent(base_path=project_path)
                    answer = agent.query_docs(request.question)
            except Exception as rag_error:
                # If RAG fails, fallback to LLM
                agent = DocumentationAgent(base_path=project_path)
                answer = agent.query_docs(request.question)
        else:
            # Use LLM directly
            agent = DocumentationAgent(base_path=project_path)
            answer = agent.query_docs(request.question)
        
        return {"status": "success", "question": request.question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query documentation: {str(e)}")


@router.post("/ingest")
def ingest_docs(request: GenerateDocsRequest):
    """
    Ingests project documentation into Weaviate for RAG queries.
    """
    if not ENABLE_WEAVIATE:
        raise HTTPException(status_code=400, detail="Weaviate is not enabled. Enable it in config to use RAG features.")
    
    project_path = Path(request.project_path)
    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid project path.")

    try:
        print(f"Starting documentation ingestion for path: {project_path}")
        agent = DocumentationAgent(base_path=project_path)
        print(f"DocumentationAgent created successfully")
        
        # Collect all documentation files
        docs = agent.collect_docs()
        print(f"Found {len(docs)} documentation files")
        ingested_count = 0
        
        # Get Weaviate client
        print("Getting Weaviate client...")
        client = get_weaviate_client()
        if not client:
            print("ERROR: Weaviate client not available")
            raise HTTPException(status_code=500, detail="Weaviate client not available")
        print("Weaviate client obtained successfully")
        
        # Ensure schema exists (create if it doesn't)
        class_name = "DocsChunk"
        try:
            print(f"Managing schema for class: {class_name}")
            
            # Check if we're using the new Weaviate v4 client or old v3 client
            if hasattr(client, 'collections'):
                # New Weaviate v4 API
                with client:
                    if client.collections.exists(class_name):
                        print(f"Schema {class_name} already exists - using existing schema")
                    else:
                        print(f"Schema {class_name} not found, creating new schema")
                        # Create the schema using Weaviate v4 API
                        from weaviate.classes.config import Property, DataType
                        client.collections.create(
                            name=class_name,
                            properties=[
                                Property(name="text", data_type=DataType.TEXT),
                                Property(name="source", data_type=DataType.TEXT),
                                Property(name="category", data_type=DataType.TEXT)
                            ]
                        )
                        print(f"Created new schema: {class_name}")
            else:
                # Old Weaviate v3 API
                if client.schema.exists(class_name):
                    print(f"Schema {class_name} already exists - using existing schema")
                else:
                    print(f"Schema {class_name} not found, creating new schema")
                    # Create the schema using Weaviate v3 API
                    schema = {
                        "class": class_name,
                        "properties": [
                            {"name": "text", "dataType": ["text"]},
                            {"name": "source", "dataType": ["text"]},
                            {"name": "category", "dataType": ["text"]}
                        ]
                    }
                    client.schema.create_class(schema)
                    print(f"Created new schema: {class_name}")
        except Exception as e:
            print(f"Error managing schema: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to manage Weaviate schema: {str(e)}")
        
        # Process and ingest documents
        if hasattr(client, 'collections'):
            # New Weaviate v4 API
            with client:
                collection = client.collections.get(class_name)
                
                for doc in docs:
                    try:
                        content = agent.read_file(doc)
                        if not content.strip():
                            continue
                        
                        # Determine category
                        category = "code_doc" if doc.suffix == ".py" else "readme" if doc.name.lower() == "readme.md" else "other"
                        
                        # Split content into chunks (simple chunking for now)
                        chunks = _split_into_chunks(content, max_length=1000)
                        
                        for i, chunk in enumerate(chunks):
                            if chunk.strip():
                                data_object = {
                                    "text": chunk,
                                    "source": str(doc.relative_to(project_path)),
                                    "category": category
                                }
                                
                                # Use Weaviate v4 API
                                collection.data.insert(properties=data_object)
                                ingested_count += 1
                                
                    except Exception as e:
                        print(f"Error processing {doc}: {e}")
                        continue
        else:
            # Old Weaviate v3 API
            for doc in docs:
                try:
                    content = agent.read_file(doc)
                    if not content.strip():
                        continue
                    
                    # Determine category
                    category = "code_doc" if doc.suffix == ".py" else "readme" if doc.name.lower() == "readme.md" else "other"
                    
                    # Split content into chunks (simple chunking for now)
                    chunks = _split_into_chunks(content, max_length=1000)
                    
                    for i, chunk in enumerate(chunks):
                        if chunk.strip():
                            data_object = {
                                "text": chunk,
                                "source": str(doc.relative_to(project_path)),
                                "category": category
                            }
                            
                            # Use Weaviate v3 API
                            client.data_object.create(
                                data_object=data_object,
                                class_name=class_name
                            )
                            ingested_count += 1
                            
                except Exception as e:
                    print(f"Error processing {doc}: {e}")
                    continue
        
        return {
            "status": "success", 
            "message": f"Successfully ingested {ingested_count} documentation chunks into Weaviate.",
            "chunks_ingested": ingested_count,
            "files_processed": len(docs)
        }
        
    except Exception as e:
        print(f"CRITICAL ERROR in ingestion: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to ingest documentation: {str(e)}")


def _split_into_chunks(text: str, max_length: int = 1000) -> List[str]:
    """Split text into chunks of maximum length."""
    chunks = []
    words = text.split()
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > max_length and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks


@router.post("/reset")
def reset_docs_schema(request: GenerateDocsRequest):
    """
    Reset the documentation schema by clearing existing DocsChunk class and data.
    Use this if you encounter schema conflicts or want to start fresh.
    """
    if not ENABLE_WEAVIATE:
        raise HTTPException(status_code=400, detail="Weaviate is not enabled. Enable it in config to use RAG features.")
    
    project_path = Path(request.project_path)
    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid project path.")

    try:
        client = get_weaviate_client()
        if not client:
            raise HTTPException(status_code=500, detail="Weaviate client not available")
        
        # Delete the existing DocsChunk class
        try:
            if hasattr(client, 'collections'):
                # New Weaviate v4 API
                with client:
                    if client.collections.exists("DocsChunk"):
                        client.collections.delete("DocsChunk")
                        print("Deleted existing DocsChunk schema")
                    else:
                        print("DocsChunk schema does not exist")
            else:
                # Old Weaviate v3 API
                if client.schema.exists("DocsChunk"):
                    client.schema.delete_class("DocsChunk")
                    print("Deleted existing DocsChunk schema")
                else:
                    print("DocsChunk schema does not exist")
        except Exception as e:
            print(f"Error deleting schema (may not exist): {e}")
        
        return {
            "status": "success",
            "message": "Documentation schema reset successfully. Call /documentation/ingest to rebuild."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset documentation schema: {str(e)}")


@router.get("/download/{file_type}")
def download_docs(file_type: str, project_path: str):
    """
    Download generated documentation files (README or API docs).
    """
    if file_type not in ["readme", "api_docs"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Use 'readme' or 'api_docs'.")
    
    project_path_obj = Path(project_path)
    if not project_path_obj.exists() or not project_path_obj.is_dir():
        raise HTTPException(status_code=400, detail="Invalid project path.")
    
    try:
        # Define output directory
        output_dir = project_path_obj / "docs" / "auto_generated"
        
        if file_type == "readme":
            file_path = output_dir / "README_AUTO.md"
            filename = "README_AUTO.md"
        else:  # api_docs
            file_path = output_dir / "API_DOCS.md"
            filename = "API_DOCUMENTATION.md"
        
        # Check if file exists, if not, generate it
        if not file_path.exists():
            agent = DocumentationAgent(base_path=project_path_obj)
            if file_type == "readme":
                file_path = Path(agent.generate_readme())
            else:  # api_docs
                file_path = Path(agent.generate_api_docs())
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"{file_type} file not found.")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='text/markdown'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download {file_type}: {str(e)}")


@router.get("/")
def root():
    return {
        "message": "Documentation Agent API is running. Use /generate_docs, /query_docs, or /ingest endpoints.",
        "endpoints": {
            "generate": "POST /documentation/generate - Generate documentation",
            "query": "POST /documentation/query - Query documentation", 
            "ingest": "POST /documentation/ingest - Ingest docs into Weaviate",
            "reset": "POST /documentation/reset - Reset documentation schema",
            "download": "GET /documentation/download/{file_type}?project_path=... - Download documentation files"
        }
    }


# ==============================
# Example: Run with
# uvicorn doc_routes:app --host 0.0.0.0 --port 8080 --reload
# ==============================
