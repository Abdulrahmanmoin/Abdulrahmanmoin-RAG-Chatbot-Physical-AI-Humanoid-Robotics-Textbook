from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID


class DocumentMetadata(BaseModel):
    title: str
    content_type: str  # "chapter", "section", "appendix"
    source_path: str
    metadata: Dict[str, Any] = {}


class DocumentChunk(BaseModel):
    document_id: UUID
    chunk_index: int
    content: str
    content_length: int
    embedding_id: str
    token_count: int
    metadata: Dict[str, Any] = {}


class RetrievedChunk(BaseModel):
    chunk_id: UUID
    document_id: UUID
    content: str
    similarity_score: float  # 0.0 to 1.0
    source_path: str
    chunk_index: int


class RetrievalResult(BaseModel):
    chunks: List[RetrievedChunk]
    query_embedding: List[float]
    retrieval_time_ms: int