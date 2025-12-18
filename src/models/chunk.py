from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint
from ..config.database import Base
import uuid


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index = Column(Integer, nullable=False)  # order within the document
    content = Column(Text, nullable=False)  # the actual text content
    content_length = Column(Integer, nullable=False)
    embedding_id = Column(String(255), nullable=False)  # reference to Qdrant vector ID
    token_count = Column(Integer, nullable=False)
    metadata = Column(
        Text
    )  # JSONB stored as text, additional chunk-specific metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="unique_doc_chunk"),
    )