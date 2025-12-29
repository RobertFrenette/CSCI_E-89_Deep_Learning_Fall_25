"""
PDF ingestion service for AI Agent
Handles PDF upload and ingestion into ChromaDB
"""
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict
from pypdf import PdfReader
from src.chromadb_client import ChromaDBClient

logger = logging.getLogger(__name__)


class PDFService:
    """Service for handling PDF ingestion into ChromaDB"""
    
    def __init__(
        self,
        chromadb_client: Optional[ChromaDBClient] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize PDF service
        
        Args:
            chromadb_client: ChromaDB client instance
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks
        """
        self.chromadb_client = chromadb_client or ChromaDBClient()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from a PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            reader = PdfReader(pdf_path)
            text_parts = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(full_text)} characters from {pdf_path}")
            return full_text
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            raise
    
    def chunk_text(self, text: str) -> list[str]:
        """
        Split text into chunks for embedding
        
        Args:
            text: Full text to chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence endings near the chunk boundary
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > self.chunk_size * 0.5:  # Only break if we're past halfway
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= text_length:
                break
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def ingest_pdf_file(
        self,
        file_content: bytes,
        filename: str,
        collection_name: str = "knowledge_base",
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Ingest a PDF file from bytes into ChromaDB
        
        Args:
            file_content: PDF file content as bytes
            filename: Original filename
            collection_name: Name of the ChromaDB collection
            metadata: Optional metadata to add to all chunks
            
        Returns:
            Number of chunks ingested
        """
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
        
        try:
            # Extract text
            text = self.extract_text_from_pdf(tmp_path)
            
            if not text.strip():
                logger.warning(f"No text extracted from {filename}")
                return 0
            
            # Chunk text
            chunks = self.chunk_text(text)
            
            # Prepare metadata
            pdf_name = Path(filename).stem
            timestamp = Path(tmp_path).stat().st_mtime
            
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    "source": filename,
                    "source_name": pdf_name,
                    "uploaded": True,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                documents.append(chunk)
                metadatas.append(chunk_metadata)
                # Use timestamp in ID to avoid conflicts
                ids.append(f"{pdf_name}_{int(timestamp)}_{i}")
            
            # Add to ChromaDB
            self.chromadb_client.add_documents(
                collection_name=collection_name,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Ingested {len(chunks)} chunks from {filename} into '{collection_name}'")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Failed to ingest PDF {filename}: {e}")
            raise
        finally:
            # Clean up temporary file
            try:
                Path(tmp_path).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {tmp_path}: {e}")

