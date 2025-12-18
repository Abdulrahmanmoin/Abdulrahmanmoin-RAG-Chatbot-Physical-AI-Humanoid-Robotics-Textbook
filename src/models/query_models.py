from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID


class QueryRequest(BaseModel):
    query: str
    query_type: str  # "full_book" or "selection_based"
    selected_text: Optional[str] = None
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    response: str
    status: str  # "success", "refused", "error"
    sources: List[str]  # references to source chunks
    confidence: float  # 0.0 to 1.0
    query_id: str


class DocumentMetadata(BaseModel):
    title: str
    content_type: str  # "chapter", "section", "appendix"
    source_path: str
    metadata: dict = {}


class DocumentChunk(BaseModel):
    document_id: str
    chunk_index: int
    content: str
    content_length: int
    embedding_id: str
    token_count: int
    metadata: dict = {}


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    similarity_score: float  # 0.0 to 1.0
    source_path: str
    chunk_index: int


class RetrievalResult(BaseModel):
    chunks: List[RetrievedChunk]
    query_embedding: List[float]
    retrieval_time_ms: int