from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List, Optional
import os


class Settings(BaseSettings):
    # API Keys
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="google/gemini-pro", alias="OPENROUTER_MODEL")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    
    # Keep gemini_api_key for backward compatibility during transition
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")

    # Qdrant Configuration
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    qdrant_collection_name: str = Field(default="book_content_v2", alias="QDRANT_COLLECTION_NAME")

    # Database Configuration
    database_url: str = Field(default="", alias="NEON_DATABASE_URL")

    # Application settings
    app_name: str = Field(default="RAG Chatbot for Physical AI & Humanoid Robotics Book", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="info", alias="LOG_LEVEL")
    debug: bool = Field(default=False, alias="DEBUG")
    max_query_length: int = Field(default=1000, alias="MAX_QUERY_LENGTH")
    max_response_tokens: int = Field(default=500, alias="MAX_RESPONSE_TOKENS")

    # CORS settings
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    # Retrieval Configuration
    retrieval_top_k: int = Field(default=5, alias="RETRIEVAL_TOP_K")
    retrieval_similarity_threshold: float = Field(default=0.7, alias="RETRIEVAL_SIMILARITY_THRESHOLD")

    # Generation Configuration
    generation_temperature: float = Field(default=0.1, alias="GENERATION_TEMPERATURE")

    @property
    def allowed_origins(self) -> List[str]:
        # Return a list of allowed origins for CORS
        origins = [self.frontend_url]
        # Add localhost for development
        if self.app_env == "development":
            origins.extend([
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",  # In case frontend runs on different port
                "http://127.0.0.1:3001"
            ])
        return origins

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Create settings instance
settings = Settings()