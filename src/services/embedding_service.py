import os
import asyncio
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from ..config.settings import settings


class EmbeddingService:
    def __init__(self):
        # Load the pre-trained sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.model_name = "all-MiniLM-L6-v2"

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using local model
        """
        try:
            # Generate embedding using the local model
            embedding = self.model.encode([text])
            return embedding[0].tolist()
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts
        """
        try:
            # Generate embeddings for all texts at once for efficiency
            embeddings = self.model.encode(texts)
            return [embedding.tolist() for embedding in embeddings]
        except Exception as e:
            print(f"Error generating batch embeddings: {str(e)}")
            raise

    async def get_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query (optimized for retrieval)
        """
        try:
            # Generate embedding for the query using the local model
            embedding = self.model.encode([query])
            return embedding[0].tolist()
        except Exception as e:
            print(f"Error generating query embedding: {str(e)}")
            raise