"""
PDF ingestion module for loading PDFs into ChromaDB
Used by database initialization scripts
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from pypdf import PdfReader
from chromadb_client import ChromaDBClient

logger = logging.getLogger(__name__)


class PDFIngestion:
    """Handle PDF ingestion into ChromaDB vector store"""
    
    def __init__(
        self,
        chromadb_client: ChromaDBClient,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize PDF ingestion
        
        Args:
            chromadb_client: ChromaDB client instance
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks
        """
        self.chromadb_client = chromadb_client
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
    
    def chunk_text(self, text: str) -> List[str]:
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
    
    def ingest_pdf(
        self,
        pdf_path: str,
        collection_name: str = "knowledge_base",
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Ingest a single PDF file into ChromaDB
        
        Args:
            pdf_path: Path to PDF file
            collection_name: Name of the ChromaDB collection
            metadata: Optional metadata to add to all chunks
            
        Returns:
            Number of chunks ingested
        """
        try:
            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            
            if not text.strip():
                logger.warning(f"No text extracted from {pdf_path}")
                return 0
            
            # Chunk text
            chunks = self.chunk_text(text)
            
            # Prepare metadata
            pdf_name = Path(pdf_path).stem
            pdf_dir = Path(pdf_path).parent.name
            
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    "source": pdf_path,
                    "source_name": pdf_name,
                    "source_dir": pdf_dir,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                documents.append(chunk)
                metadatas.append(chunk_metadata)
                ids.append(f"{pdf_name}_{i}")
            
            # Add to ChromaDB
            self.chromadb_client.add_documents(
                collection_name=collection_name,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Ingested {len(chunks)} chunks from {pdf_path} into '{collection_name}'")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Failed to ingest PDF {pdf_path}: {e}")
            raise
    
    def ingest_directory(
        self,
        directory_path: str,
        collection_name: str = "knowledge_base",
        recursive: bool = True
    ) -> Dict[str, int]:
        """
        Ingest all PDFs from a directory
        
        Args:
            directory_path: Path to directory containing PDFs
            collection_name: Name of the ChromaDB collection
            recursive: Whether to search subdirectories
            
        Returns:
            Dictionary mapping PDF paths to number of chunks ingested
        """
        results = {}
        pdf_files = []
        
        # Find all PDF files
        path = Path(directory_path)
        if recursive:
            pdf_files = list(path.rglob("*.pdf"))
        else:
            pdf_files = list(path.glob("*.pdf"))
        
        logger.info(f"Found {len(pdf_files)} PDF files in {directory_path}")
        
        for pdf_path in pdf_files:
            try:
                chunks_count = self.ingest_pdf(
                    str(pdf_path),
                    collection_name=collection_name
                )
                results[str(pdf_path)] = chunks_count
            except Exception as e:
                logger.error(f"Failed to ingest {pdf_path}: {e}")
                results[str(pdf_path)] = 0
        
        total_chunks = sum(results.values())
        logger.info(f"Ingested {total_chunks} total chunks from {len(pdf_files)} PDFs")
        return results

