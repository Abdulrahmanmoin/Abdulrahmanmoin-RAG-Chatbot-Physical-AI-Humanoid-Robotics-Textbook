
from qdrant_client import QdrantClient
import os
import sys

def check():
    with open("db_status.txt", "w") as f:
        try:
            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            collection = os.getenv("QDRANT_COLLECTION_NAME", "book_content_v2")
            
            f.write(f"Connecting to {url}...\n")
            client = QdrantClient(url=url)
            
            f.write(f"Checking collection: {collection}\n")
            info = client.get_collection(collection)
            f.write(f"Points: {info.points_count}\n")
            f.write(f"Status: {info.status}\n")
            
        except Exception as e:
            f.write(f"Error: {e}\n")

if __name__ == "__main__":
    check()
