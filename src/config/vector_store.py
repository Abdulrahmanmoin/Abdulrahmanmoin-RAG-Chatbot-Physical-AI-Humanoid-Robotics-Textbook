from qdrant_client import QdrantClient
from qdrant_client.http import models
from pydantic_settings import BaseSettings
from pydantic import Field
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VectorStoreSettings(BaseSettings):
    # qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    # qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    # collection_name: str = os.getenv("QDRANT_COLLECTION_NAME", "book_content")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    collection_name: str = Field(default="book_content", alias="QDRANT_COLLECTION_NAME")

    class Config:
        env_file = ".env"
        extra = "ignore"


class VectorStore:
    def __init__(self):
        self.settings = VectorStoreSettings()

        # Initialize Qdrant client
        # Handle case where env var is set to empty string
        actual_url = self.settings.qdrant_url
        if not actual_url:
            actual_url = "http://localhost:6333"
        if self.settings.qdrant_api_key:
            self.client = QdrantClient(
                url=actual_url,
                api_key=self.settings.qdrant_api_key,
                #   prefer_grpc=True  # Use gRPC for better performance if available
                prefer_grpc=False  # Disable gRPC to avoid connection timeouts
            )
        else:
            self.client = QdrantClient(url=actual_url)

        self.collection_name = self.settings.collection_name
        self._initialize_collection()

    def _initialize_collection(self):
        """Initialize the Qdrant collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection with appropriate settings
                # Using all-MiniLM-L6-v2 embedding size (384 dimensions)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,  # all-MiniLM-L6-v2 embedding size
                        distance=models.Distance.COSINE
                    )
                )

                # Create payload index for efficient filtering
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="document_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )

                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection {self.collection_name} already exists")

        except Exception as e:
            # Log error but do NOT raise, to allow application to start even if Qdrant is temporarily down
            logger.error(f"Error initializing Qdrant collection: {e}")
            # raise

    def get_client(self):
        """Return the Qdrant client instance"""
        return self.client

    def get_collection_name(self):
        """Return the collection name"""
        return self.collection_name


# Global instance
vector_store = VectorStore()


def get_vector_store():
    """Dependency to get vector store instance"""
    return vector_store