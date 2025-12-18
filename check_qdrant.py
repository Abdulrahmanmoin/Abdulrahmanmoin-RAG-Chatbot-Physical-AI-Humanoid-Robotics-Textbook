#!/usr/bin/env python3
"""Debug script to check Qdrant collection status"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.config.settings import settings
from qdrant_client import QdrantClient

def main():
    print("=== Qdrant Debug Info ===")
    print(f"Qdrant URL: {settings.qdrant_url or 'NOT SET'}")
    print(f"Qdrant API Key: {'***SET***' if settings.qdrant_api_key else 'NOT SET'}")
    print(f"Collection Name: {settings.qdrant_collection_name}")
    
    if not settings.qdrant_url:
        print("\nERROR: QDRANT_URL is not configured in .env file!")
        return
    
    try:
        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            prefer_grpc=False
        )
        
        # Check if collection exists
        try:
            collection_info = client.get_collection(settings.qdrant_collection_name)
            print(f"\n=== Collection '{settings.qdrant_collection_name}' Info ===")
            print(f"Points count: {collection_info.points_count}")
            print(f"Indexed vectors count: {collection_info.indexed_vectors_count}")
            print(f"Status: {collection_info.status}")
            
            if collection_info.points_count == 0:
                print("\n⚠️  WARNING: The collection is EMPTY!")
                print("   You need to ingest documents before querying.")
                print("   Run: python -m src.scripts.ingest_documents <path_to_docs>")
        except Exception as e:
            print(f"\nCollection '{settings.qdrant_collection_name}' not found or error: {e}")
            print("The collection will be created when you ingest documents.")
            
    except Exception as e:
        print(f"\nERROR connecting to Qdrant: {e}")

if __name__ == "__main__":
    main()
