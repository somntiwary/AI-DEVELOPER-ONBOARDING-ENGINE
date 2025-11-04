# query_engine.py
from weaviate import Client
from typing import List, Dict
import json

try:
    from agents.documentation.doc_generator import call_openrouter_llm, LLM_MODELS
except ImportError:
    # Allow running when executed as a script
    import os as _os, sys as _sys
    _BACKEND_DIR = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
    _PROJECT_ROOT = _os.path.dirname(_BACKEND_DIR)
    if _PROJECT_ROOT not in _sys.path:
        _sys.path.insert(0, _PROJECT_ROOT)
    from agents.documentation.doc_generator import call_openrouter_llm, LLM_MODELS  # type: ignore

class QueryEngine:
    """
    Retrieval-Augmented Generation (RAG) Query Engine for project documentation.
    Retrieves relevant docs from Weaviate and answers questions using LLMs.
    """

    def __init__(self, weaviate_url: str = "http://localhost:8080", class_name: str = "DocsChunk"):
        """
        Initialize Weaviate client.
        :param weaviate_url: URL of the running Weaviate instance
        :param class_name: Class name used for storing document chunks
        """
        try:
            from weaviate import Client
            self.client = Client(url=weaviate_url)
        except ImportError:
            import weaviate
            # Try to use v3 API
            self.client = weaviate.Client(url=weaviate_url)
        self.class_name = class_name

    def retrieve_chunks(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve top-k relevant document chunks from Weaviate.
        """
        try:
            # Check if we're using the new Weaviate v4 client or old v3 client
            if hasattr(self.client, 'collections'):
                # New Weaviate v4 API
                with self.client:
                    collection = self.client.collections.get(self.class_name)
                    response = collection.query.near_text(
                        query=query,
                        limit=top_k,
                        return_metadata=["distance"]
                    )
                    
                    chunks = []
                    for obj in response.objects:
                        chunks.append({
                            "text": obj.properties.get("text", ""),
                            "source": obj.properties.get("source", ""),
                            "category": obj.properties.get("category", "")
                        })
                    return chunks
            else:
                # Old Weaviate v3 API
                query_builder = self.client.query.get(self.class_name, ["text", "source", "category"])
                query_builder = query_builder.with_near_text({"concepts": [query]})
                query_builder = query_builder.with_limit(top_k)
                
                result = query_builder.do()
                
                chunks = []
                if result and "data" in result and "Get" in result["data"]:
                    for obj in result["data"]["Get"][self.class_name]:
                        chunks.append({
                            "text": obj.get("text", ""),
                            "source": obj.get("source", ""),
                            "category": obj.get("category", "")
                        })
                return chunks
        except Exception as e:
            print(f"❌ Error retrieving chunks: {e}")
            return []

    def generate_answer(self, query: str, context_chunks: List[Dict]) -> str:
        """
        Generates an answer using retrieved context and LLM.
        """
        context_text = "\n\n".join([f"{c['source']}: {c['text']}" for c in context_chunks])

        prompt = f"""
You are a professional Documentation QA Agent.
Answer the user's question based on the provided context from project docs.

Context:
{context_text[:8000]}  # truncate if too long

Question:
{query}

Answer concisely and clearly.
"""
        return call_openrouter_llm(prompt)

    def query(self, question: str, top_k: int = 5) -> str:
        """
        Full query pipeline: retrieve + LLM answer.
        """
        try:
            chunks = self.retrieve_chunks(question, top_k=top_k)
            if not chunks:
                return "❌ No relevant documentation chunks found. Try generating documentation first or check if Weaviate is properly configured."
            answer = self.generate_answer(question, chunks)
            return answer
        except Exception as e:
            return f"❌ Error querying documentation: {str(e)}"


# ==============================
# 🚀 CLI / Example usage
# ==============================
if __name__ == "__main__":
    engine = QueryEngine(weaviate_url="http://localhost:8080")

    print("💬 Welcome to the Documentation Query Engine")
    while True:
        q = input("\nEnter your question (or 'exit' to quit): ").strip()
        if q.lower() in ["exit", "quit"]:
            break
        answer = engine.query(q)
        print("\n✅ Answer:\n", answer)
