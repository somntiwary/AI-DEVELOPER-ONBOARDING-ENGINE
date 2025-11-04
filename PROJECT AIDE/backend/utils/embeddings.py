from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple
import time

try:
    # Try importing as if running from project root
    from config import WEAVIATE_URL, ENABLE_WEAVIATE, EMBED_TIMEOUT_SECONDS
except ImportError:
    # Import directly when running from backend directory
    from config import WEAVIATE_URL, ENABLE_WEAVIATE, EMBED_TIMEOUT_SECONDS


@lru_cache(maxsize=1)
def get_sentence_model():
    # Lazy import to avoid heavy init at app import time
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def get_weaviate_client():
    # Lazy import to avoid requiring Weaviate at app import time
    if not ENABLE_WEAVIATE:
        return None
    try:
        import weaviate
        
        # Try v4 API first (Method 1: connect_to_local)
        try:
            client = weaviate.connect_to_local(
                host="localhost", 
                port=8080,
                skip_init_checks=True
            )
            print("Connected to Weaviate using v4 API (connect_to_local)")
            return client
        except (AttributeError, TypeError) as e1:
            # If connect_to_local doesn't exist, try v4 API Method 2
            try:
                from weaviate.classes.init import AdditionalConfig
                client = weaviate.WeaviateClient(
                    connection_params={
                        "host": "localhost",
                        "port": 8080,
                        "http_secure": False
                    },
                    additional_config=AdditionalConfig(
                        timeout=(5, 15)  # (connect timeout, read timeout)
                    )
                )
                print("Connected to Weaviate using v4 API (WeaviateClient)")
                return client
            except (ImportError, AttributeError, TypeError) as e2:
                # Fallback to v3 API
                print(f"Weaviate v4 API not available, trying v3 API...")
                try:
                    client = weaviate.Client("http://localhost:8080")
                    print("Connected to Weaviate using v3 API (Client)")
                    return client
                except Exception as e3:
                    print(f"Weaviate v3 connection failed: {e3}")
                    raise e3
    except Exception as e:
        print(f"Weaviate connection completely failed: {e}")
        return None


def embed_text(text: str, timeout: Optional[int] = None) -> Tuple[List[float], bool]:
    """
    Generate embeddings for text with timeout.
    
    Returns:
        Tuple of (embeddings, success_flag)
    """
    if timeout is None:
        timeout = EMBED_TIMEOUT_SECONDS
    
    try:
        model = get_sentence_model()
        start_time = time.time()
        
        embeddings = model.encode(text).tolist()
        
        # Check timeout
        if time.time() - start_time > timeout:
            return [], False
            
        return embeddings, True
    except Exception:
        return [], False


def store_embedding(content: str, metadata: Optional[Dict[str, Any]] = None, vector: Optional[List[float]] = None) -> Tuple[bool, str]:
    """
    Store code/text embeddings in Weaviate with graceful error handling.
    
    Returns:
        Tuple of (success_flag, message)
    """
    if not ENABLE_WEAVIATE:
        return False, "Weaviate storage disabled"
    
    client = get_weaviate_client()
    if client is None:
        return False, "Weaviate client unavailable"
    
    try:
        data_obj: Dict[str, Any] = {"content": content, "metadata": metadata or {}}
        if vector is not None:
            data_obj["embedding"] = vector
        
        # Check if using v4 API (has 'collections' attribute)
        if hasattr(client, 'collections'):
            # Use Weaviate v4 API
            try:
                with client:
                    collection = client.collections.get("RepoChunk")
                    collection.data.insert(
                        properties=data_obj,
                        vector=vector
                    )
            except Exception as e:
                # If 'with client' fails, try without context manager
                collection = client.collections.get("RepoChunk")
                collection.data.insert(
                    properties=data_obj,
                    vector=vector
                )
        else:
            # Use Weaviate v3 API
            client.data_object.create(
                data_object=data_obj,
                class_name="RepoChunk",
                vector=vector
            )
        return True, "Success"
    except Exception as e:
        return False, f"Storage failed: {str(e)}"
