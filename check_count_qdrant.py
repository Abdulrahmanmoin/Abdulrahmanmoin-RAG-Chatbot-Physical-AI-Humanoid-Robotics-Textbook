
from qdrant_client import QdrantClient
import os
import time

def check():
    output_file = "count_status.txt"
    try:
        url = "http://localhost:6333"
        collection = "book_content_v2"
        
        with open(output_file, "w") as f:
            f.write(f"Connecting to {url}...\n")
            client = QdrantClient(url=url)
            
            f.write(f"Checking collection: {collection}\n")
            if client.collection_exists(collection):
                info = client.get_collection(collection)
                f.write(f"Points: {info.points_count}\n")
            else:
                f.write("Collection does not exist.\n")
                
    except Exception as e:
        with open(output_file, "w") as f:
            f.write(f"Error: {e}\n")

if __name__ == "__main__":
    check()
