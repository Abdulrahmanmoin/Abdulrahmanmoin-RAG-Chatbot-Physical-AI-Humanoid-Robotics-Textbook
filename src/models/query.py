from sqlalchemy import Column, String, Text, DateTime, Integer, UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from ..config.database import Base
import uuid
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID as PydanticUUID


class QueryLog(Base):
    __tablename__ = "queries"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        PG_UUID(as_uuid=True)
    )  # for potential conversation tracking (though stateless by default)
    query_text = Column(Text, nullable=False)
    query_type = Column(String(20), nullable=False)  # 'full_book', 'selection_based'
    selected_text = Column(
        Text
    )  # if selection-based query
    response_text = Column(
        Text
    )  # the generated response
    response_status = Column(String(20), nullable=False)  # 'success', 'refused', 'error'
    retrieved_chunks = Column(
        JSONB
    )  # references to chunks used in response (stored as JSONB)
    confidence_score = Column(
        String(5)
    )  # DECIMAL(3,2) stored as string to preserve precision
    processing_time_ms = Column(Integer)  # processing time in milliseconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes will be handled by Alembic migrations


class QueryRequest(BaseModel):
    query: str
    query_type: str  # "full_book" or "selection_based"
    selected_text: Optional[str] = None
    session_id: Optional[PydanticUUID] = None


class QueryResponse(BaseModel):
    response: str
    status: str  # "success", "refused", "error"
    sources: List[str]  # references to source chunks
    confidence: float  # 0.0 to 1.0
    query_id: PydanticUUID