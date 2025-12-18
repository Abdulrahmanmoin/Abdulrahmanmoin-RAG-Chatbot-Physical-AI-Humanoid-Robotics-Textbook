import os
import logging
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct, Distance, VectorParams
from ..models.document_models import RetrievedChunk
from ..services.embedding_service import EmbeddingService
from ..config.settings import settings
import uuid


logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self):
        # Initialize Qdrant client
        # Handle case where env var is set to empty string (common issue)
        qdrant_url = settings.qdrant_url
        if not qdrant_url:
            qdrant_url = "http://localhost:6333"
            logger.warning("settings.qdrant_url is empty, defaulting to http://localhost:6333")

        self.client = QdrantClient(
            url=qdrant_url,
            api_key=settings.qdrant_api_key,
            prefer_grpc=False  # Using HTTP for simplicity
        )
        self.collection_name = settings.qdrant_collection_name
        self.embedding_service = EmbeddingService()

        # Initialize the collection if it doesn't exist
        self._initialize_collection()

    def _initialize_collection(self):
        """
        Initialize the Qdrant collection for book content
        """
        try:
            # Check if collection exists
            self.client.get_collection(self.collection_name)
        except:
            # Create collection if it doesn't exist
            # Create collection if it doesn't exist
            self.client.create_collection(
                collection_name=self.collection_name,
                # vectors_config=VectorParams(size=768, distance=Distance.COSINE),  # Using 768 for Google's embedding m
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),  # Using 384 for all-MiniLM-L6-v2
            )

    async def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """
        Retrieve the most relevant chunks for a given query
        """
        # Generate embedding for the query
        query_embedding = await self.embedding_service.get_query_embedding(query)

        try:
            # Perform similarity search in Qdrant using search (standard API)
            print(f"DEBUG: Querying Qdrant collection '{self.collection_name}' with top_k={top_k}", flush=True)
            # print(f"DEBUG: Query embedding (first 5): {query_embedding[:5]}", flush=True)
            
            # Perform similarity search in Qdrant using query_points (reverted from search due to version compatibility)
            print(f"DEBUG: Querying Qdrant collection '{self.collection_name}' with top_k={top_k}", flush=True)
            
            # Note: query_points returns a slightly different structure (ScoredPoint) inside groups or straight points depending on args.
            # providing 'query' arg for vector.
            search_results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                with_payload=True
            )
            print(f"DEBUG: Raw search results count: {len(search_results.points)}", flush=True)
            if len(search_results.points) > 0:
                print(f"DEBUG: First result score: {search_results.points[0].score}", flush=True)

        except Exception as e:
            print(f"Error executing Qdrant query: {e}")
            logger.error(f"Error executing Qdrant query: {e}")
            return []

        # Convert search results to RetrievedChunk objects
        retrieved_chunks = []
        # query_points returns an object with a 'points' attribute
        for result in search_results.points:
            payload = result.payload
            try:
                chunk_id_val = payload.get("chunk_id")
                document_id_val = payload.get("document_id")
                
                # Handle potential non-string values or missing keys gracefully
                if not chunk_id_val:
                    chunk_id_val = str(uuid.uuid4())
                if not document_id_val:
                    document_id_val = str(uuid.uuid4())

                # Ensure we strictly pass a string to uuid.UUID
                try:
                    document_id_obj = uuid.UUID(str(document_id_val))
                except ValueError:
                    # If document_id is not a valid UUID (e.g., "physical_ai_course"), generate a deterministic UUID
                    # namespace_dns is just a default namespace to use for name-based UUIDs
                    document_id_obj = uuid.uuid5(uuid.NAMESPACE_DNS, str(document_id_val))
                
                chunk = RetrievedChunk(
                    chunk_id=uuid.UUID(str(chunk_id_val)),
                    document_id=document_id_obj,
                    content=payload.get("content", ""),
                    similarity_score=result.score,
                    source_path=payload.get("source_path", ""),
                    chunk_index=payload.get("chunk_index", 0)
                )
                retrieved_chunks.append(chunk)
            except Exception as e:
                logger.error(f"Error processing chunk from Qdrant: {e}. Payload partial: {str(payload)[:100]}...", exc_info=True)
                continue

        return retrieved_chunks

    async def retrieve_from_selected_text(self, selected_text: str, top_k: int = 5) -> List[RetrievedChunk]:
        """
        Retrieve chunks specifically from the selected text (for selection-based queries)
        """
        # For selection-based queries, we just return the selected text as a single chunk
        # since the context is limited to the user's selection
        query_embedding = await self.embedding_service.get_query_embedding(selected_text)

        # In selection-based mode, we don't perform a search but return the selected text as context
        # This is a simplified approach - in a real implementation, you might want to store
        # the selected text in a temporary manner or validate it differently
        chunk = RetrievedChunk(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),  # Placeholder
            content=selected_text,
            similarity_score=1.0,  # Perfect match since it's the selected text
            source_path="user_selection",  # Indicate this came from user selection
            chunk_index=0
        )

        return [chunk]

    async def add_document_chunks(self, chunks: List[dict]):
        """
        Add document chunks to the vector store
        Each chunk should have: chunk_id, document_id, content, source_path, chunk_index, metadata
        """
        points = []
        for chunk in chunks:
            point = PointStruct(
                id=chunk["embedding_id"],  # Using the embedding_id as the point ID
                vector=await self.embedding_service.generate_embedding(chunk["content"]),
                payload={
                    "chunk_id": str(chunk["chunk_id"]),
                    "document_id": str(chunk["document_id"]),
                    "content": chunk["content"],
                    "content_type": chunk.get("content_type", ""),
                    "source_path": chunk["source_path"],
                    "chunk_index": chunk["chunk_index"],
                    "token_count": chunk.get("token_count", 0),
                    "metadata": chunk.get("metadata", {})
                }
            )
            points.append(point)

        # Upload points to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def verify_chunk_exists(self, chunk_id: str) -> bool:
        """
        Verify if a chunk exists in the vector store
        """
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[chunk_id],
                with_payload=True
            )
            return len(result) > 0
        except:
            return False