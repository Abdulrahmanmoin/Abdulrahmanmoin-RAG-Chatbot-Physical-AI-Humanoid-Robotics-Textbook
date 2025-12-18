from sqlalchemy import Column, String, Text, DateTime, Integer, UUID, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from ..config.database import Base
import uuid


class Document(Base):
    __tablename__ = "documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)  # 'chapter', 'section', 'appendix', etc.
    source_path = Column(Text, nullable=False)  # path in the book structure
    metadata = Column(
        Text
    )  # JSONB stored as text, additional metadata like page numbers, authors
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    version = Column(Integer, default=1)