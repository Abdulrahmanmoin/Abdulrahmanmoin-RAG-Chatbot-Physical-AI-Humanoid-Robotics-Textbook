
from qdrant_client import QdrantClient
import os

print("--- Checking Qdrant Data ---", flush=True)
url = "http://localhost:6333"
collection = "book_content_v2"
print(f"Connecting to {url}...", flush=True)

try:
    client = QdrantClient(url=url)
    if client.collection_exists(collection):
        info = client.get_collection(collection)
        print(f"Collection '{collection}' exists.", flush=True)
        print(f"Points count: {info.points_count}", flush=True)
        
        # peek at data
        res = client.scroll(collection_name=collection, limit=1)
        if res[0]:
            print(f"Sample point payload keys: {list(res[0][0].payload.keys())}", flush=True)
        else:
            print("Collection is empty (no points found via scroll).", flush=True)
    else:
        print(f"Collection '{collection}' does NOT exist.", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
