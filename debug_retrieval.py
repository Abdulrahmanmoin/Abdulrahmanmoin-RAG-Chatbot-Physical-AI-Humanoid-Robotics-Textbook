
import os
import sys
import logging
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_retrieval():
    print("--- Debugging Retrieval ---")
    
    # 1. Configuration
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "book_content_v2")
    print(f"URL: {qdrant_url}")
    print(f"Collection: {collection_name}")

    # 2. Connect to Qdrant
    try:
        client = QdrantClient(url=qdrant_url)
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        print(f"Available Collections: {collection_names}")
        
        if collection_name not in collection_names:
            print(f"ERROR: Collection '{collection_name}' NOT found!")
            return
    except Exception as e:
        print(f"ERROR Connecting to Qdrant: {e}")
        return

    # 3. Check Collection Info
    try:
        info = client.get_collection(collection_name)
        print(f"Collection Info: Points Count = {info.points_count}, Status = {info.status}")
        
        if info.points_count == 0:
            print("WARNING: Collection is empty!")
    except Exception as e:
        print(f"ERROR getting collection info: {e}")

    # 4. Generate Embedding
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query = "What is Huminoid Robots?"
    embedding = model.encode(query).tolist()
    print(f"Generated embedding (first 5 dim): {embedding[:5]}")

    # 5. Perform Search
    print(f"Searching for: '{query}'")
    try:
        results = client.search(
            collection_name=collection_name,
            query_vector=embedding,
            limit=5,
            with_payload=True
        )
        
        print(f"Found {len(results)} results:")
        for res in results:
            print(f" - Score: {res.score}, DocID: {res.payload.get('document_id', 'N/A')}")
            print(f"   Content Preview: {res.payload.get('content', '')[:100]}...")
            
    except Exception as e:
        print(f"ERROR performing search: {e}")

if __name__ == "__main__":
    debug_retrieval()
