#!/usr/bin/env python3
"""
Document ingestion script for the Physical AI & Humanoid Robotics book.
This script processes book content, chunks it, generates embeddings, and stores in the database and vector store.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import uuid
import hashlib
from sqlalchemy.orm import sessionmaker
from ..config.database import engine, Base
from ..models.document import Document
from ..models.chunk import DocumentChunk
from ..services.embedding_service import EmbeddingService
from ..services.retrieval_service import RetrievalService
from ..config.settings import settings


class DocumentIngestionPipeline:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.retrieval_service = RetrievalService()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    async def ingest_book_content(self, source_path: str):
        """
        Main method to ingest book content from a given source path
        """
        print(f"Starting ingestion of book content from: {source_path}")

        # Create all tables if they don't exist
        Base.metadata.create_all(bind=engine)

        # Parse and process the book content
        documents_data = await self._parse_book_content(source_path)

        # Process each document
        for doc_data in documents_data:
            await self._process_document(doc_data)

        print("Document ingestion completed successfully!")

    async def _parse_book_content(self, source_path: str) -> List[Dict[str, Any]]:
        """
        Parse the book content from the source path.
        This method handles different file formats and structures the content appropriately.
        """
        source_path = Path(source_path)
        documents = []

        if source_path.is_file():
            # Process single file
            content = await self._read_file_content(source_path)
            doc_id = str(uuid.uuid4())
            documents.append({
                "id": doc_id,
                "title": source_path.stem,
                "content_type": self._get_content_type(source_path.suffix),
                "source_path": str(source_path),
                "content": content,
                "metadata": {"file_path": str(source_path), "file_size": source_path.stat().st_size}
            })
        elif source_path.is_dir():
            # Process directory of files
            for file_path in source_path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.md', '.txt', '.pdf']:
                    content = await self._read_file_content(file_path)
                    doc_id = str(uuid.uuid4())
                    documents.append({
                        "id": doc_id,
                        "title": file_path.stem,
                        "content_type": self._get_content_type(file_path.suffix),
                        "source_path": str(file_path),
                        "content": content,
                        "metadata": {"file_path": str(file_path), "file_size": file_path.stat().st_size}
                    })

        return documents

    async def _read_file_content(self, file_path: Path) -> str:
        """
        Read content from a file based on its type
        """
        if file_path.suffix.lower() == '.pdf':
            # For PDF files, we would use a PDF library like PyPDF2 or pdfplumber
            # For now, we'll simulate reading a text file
            print(f"Warning: PDF processing not implemented, simulating for {file_path}")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        else:
            # For text-based files (md, txt)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Clean up the content
                content = self._clean_content(content)
                return content

    def _clean_content(self, content: str) -> str:
        """
        Clean up the content by removing unnecessary whitespace and formatting
        """
        # Remove extra whitespace
        content = ' '.join(content.split())
        # You can add more cleaning rules as needed
        return content

    def _get_content_type(self, file_extension: str) -> str:
        """
        Determine content type based on file extension
        """
        type_mapping = {
            '.md': 'markdown',
            '.txt': 'text',
            '.pdf': 'pdf'
        }
        return type_mapping.get(file_extension.lower(), 'unknown')

    async def _process_document(self, doc_data: Dict[str, Any]):
        """
        Process a single document: chunk it, generate embeddings, and store in DB and vector store
        """
        print(f"Processing document: {doc_data['title']}")

        # Create document record in database
        db = self.SessionLocal()
        try:
            # Check if document already exists based on content hash
            content_hash = hashlib.md5(doc_data['content'].encode()).hexdigest()
            existing_doc = db.query(Document).filter(
                Document.metadata['content_hash'].astext == content_hash
            ).first()

            if existing_doc:
                print(f"Document {doc_data['title']} already exists, skipping...")
                return

            # Create new document record
            document = Document(
                title=doc_data['title'],
                content_type=doc_data['content_type'],
                source_path=doc_data['source_path'],
                metadata=doc_data['metadata'] | {"content_hash": content_hash}  # Merge metadata
            )
            db.add(document)
            db.commit()
            db.refresh(document)

            # Chunk the document content
            chunks = await self._chunk_content(doc_data['content'], document.id)

            # Process each chunk
            chunk_data_list = []
            for i, chunk in enumerate(chunks):
                chunk_data = {
                    "chunk_id": str(uuid.uuid4()),
                    "document_id": document.id,
                    "content": chunk,
                    "content_length": len(chunk),
                    "embedding_id": str(uuid.uuid4()),  # Will be updated with actual embedding ID
                    "token_count": len(chunk.split()),  # Simple token count
                    "metadata": {"chunk_index": i, "source_path": doc_data['source_path']},
                    "chunk_index": i
                }
                chunk_data_list.append(chunk_data)

            # Generate embeddings for all chunks
            chunk_contents = [chunk_data["content"] for chunk_data in chunk_data_list]
            embeddings = await self.embedding_service.generate_embeddings_batch(chunk_contents)

            # Update chunk data with actual embedding IDs and store embeddings
            for i, chunk_data in enumerate(chunk_data_list):
                chunk_data["embedding_id"] = f"emb_{document.id}_{i}"
                # Update the embedding_id in the chunk_data to match what will be used in vector store

            # Store chunks in database
            for chunk_data in chunk_data_list:
                chunk = DocumentChunk(
                    document_id=chunk_data["document_id"],
                    chunk_index=chunk_data["chunk_index"],
                    content=chunk_data["content"],
                    content_length=chunk_data["content_length"],
                    embedding_id=chunk_data["embedding_id"],
                    token_count=chunk_data["token_count"],
                    metadata=chunk_data["metadata"]
                )
                db.add(chunk)

            db.commit()

            # Store embeddings in vector store (Qdrant)
            await self.retrieval_service.add_document_chunks(chunk_data_list)

            print(f"Successfully processed document: {doc_data['title']} with {len(chunks)} chunks")

        except Exception as e:
            db.rollback()
            print(f"Error processing document {doc_data['title']}: {str(e)}")
            raise
        finally:
            db.close()

    async def _chunk_content(self, content: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Chunk the content into smaller pieces while preserving semantic meaning
        """
        chunks = []
        start = 0

        while start < len(content):
            # Determine the end position
            end = start + max_chunk_size

            # If we're at the end, take the remaining content
            if end >= len(content):
                chunks.append(content[start:])
                break

            # Try to break at a sentence or paragraph boundary
            chunk = content[start:end]

            # Find the last sentence/paragraph break before the max size
            for separator in ['\n\n', '. ', '! ', '? ', '; ']:
                last_separator = chunk.rfind(separator)
                if last_separator != -1 and last_separator > len(content) // 10:  # Ensure we're not cutting too early
                    end = start + last_separator + len(separator)
                    break

            chunk = content[start:end]
            chunks.append(chunk)

            # Move start position with overlap
            start = end - overlap if end - overlap > start else end

        # Filter out empty chunks
        chunks = [chunk for chunk in chunks if chunk.strip()]

        return chunks


async def main():
    """
    Main function to run the ingestion pipeline
    """
    if len(sys.argv) != 2:
        print("Usage: python ingest_documents.py <path_to_book_content>")
        sys.exit(1)

    source_path = sys.argv[1]

    if not os.path.exists(source_path):
        print(f"Error: Path does not exist: {source_path}")
        sys.exit(1)

    pipeline = DocumentIngestionPipeline()
    await pipeline.ingest_book_content(source_path)


if __name__ == "__main__":
    asyncio.run(main())