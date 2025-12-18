
from qdrant_client import QdrantClient
import os
import sys

def check():
    try:
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        collection = os.getenv("QDRANT_COLLECTION_NAME", "book_content_v2")
        
        print(f"Connecting to {url}...", flush=True)
        client = QdrantClient(url=url)
        
        print(f"Checking collection: {collection}", flush=True)
        info = client.get_collection(collection)
        print(f"Points: {info.points_count}", flush=True)
        print(f"Status: {info.status}", flush=True)
        
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    check()
