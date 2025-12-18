#!/usr/bin/env python3
"""
Simple script to ingest the Physical AI content directly into Qdrant
"""
import uuid
import asyncio
import os
import re
from typing import List
print("Imports starting...", flush=True)
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct, Distance, VectorParams
from dotenv import load_dotenv

load_dotenv()


def chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into chunks while preserving semantic meaning
    """
    chunks = []
    start = 0

    while start < len(text):
        # Determine the end position
        end = start + max_chunk_size

        # If we're at the end, take the remaining content
        if end >= len(text):
            chunks.append(text[start:])
            break

        # Try to break at a sentence or paragraph boundary
        chunk = text[start:end]

        # Find the last sentence/paragraph break before the max size
        for separator in ['\n\n', '. ', '! ', '? ', '; ', '\n']:
            last_separator = chunk.rfind(separator)
            if last_separator != -1 and last_separator > len(text) // 10:  # Ensure we're not cutting too early
                end = start + last_separator + len(separator)
                break

        chunk = text[start:end]
        chunks.append(chunk)

        # Move start position with overlap
        start = end - overlap if end - overlap > start else end

    # Filter out empty chunks
    chunks = [chunk for chunk in chunks if chunk.strip()]
    return chunks


def main():
    print("Imports starting...", flush=True)
    try:
        from sentence_transformers import SentenceTransformer
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import PointStruct, Distance, VectorParams
        
        # Initialize the sentence transformer model
        print("Loading embedding model...", flush=True)
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize Qdrant client
        print("Connecting to Qdrant...", flush=True)
        qdrant_url = os.getenv("QDRANT_URL")
        if not qdrant_url:
            qdrant_url = "http://localhost:6333"
            
        qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
        # Update default to match user's expectation
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "book_content_v2")
        print(f"Target Collection: {collection_name} at {qdrant_url}", flush=True)

        if qdrant_api_key:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            client = QdrantClient(url=qdrant_url)

        # Read the Physical AI content
        print("Reading Physical AI content...", flush=True)
        with open("physical_ai_content.txt", "r", encoding="utf-8") as f:
            content = f.read()

        # Chunk the content
        print("Chunking content...", flush=True)
        chunks = chunk_text(content)
        print(f"Created {len(chunks)} chunks", flush=True)

        # Generate embeddings for each chunk
        print("Generating embeddings...", flush=True)
        embeddings = model.encode(chunks)

        # Prepare points for Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={
                    "chunk_id": str(uuid.uuid4()),
                    "document_id": "physical_ai_course",
                    "content": chunk,
                    "content_type": "text",
                    "source_path": "physical_ai_content.txt",
                    "chunk_index": i,
                    "token_count": len(chunk.split()),
                    "metadata": {
                        "title": "Physical AI & Humanoid Robotics Course Content",
                        "section": extract_section_title(chunk)
                    }
                }
            )
            points.append(point)

        # Create collection if it doesn't exist
        print(f"Creating/updating collection: {collection_name}", flush=True)
        try:
            client.get_collection(collection_name)
            print("Collection already exists", flush=True)
        except:
            # Create collection with appropriate vector size (all-MiniLM-L6-v2 produces 384-dim vectors)
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            print("Collection created", flush=True)

        # Upload points to Qdrant
        print(f"Uploading {len(points)} points to Qdrant...", flush=True)
        client.upsert(
            collection_name=collection_name,
            points=points
        )

        print(f"Successfully ingested Physical AI content into Qdrant collection '{collection_name}'", flush=True)
        print(f"Total chunks: {len(chunks)}", flush=True)
        
        # Write success flag
        with open("ingest_success.txt", "w") as f:
            f.write(f"Successfully ingested {len(chunks)} chunks into {collection_name}")
            
    except Exception as e:
        error_msg = f"Ingestion failed: {str(e)}"
        print(error_msg, flush=True)
        with open("ingest_error.txt", "w") as f:
            f.write(error_msg)


def extract_section_title(chunk: str) -> str:
    """
    Extract a meaningful section title from a chunk
    """
    # Look for headers or section titles in the content
    lines = chunk.split('\n')
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if line and not line.startswith(' ') and len(line) < 100:
            # If it looks like a header (all caps, or ends with colon)
            if line.isupper() or line.endswith(':') or line.count(' ') < 5:
                return line
    return "Physical AI & Humanoid Robotics Content"


if __name__ == "__main__":
    main()