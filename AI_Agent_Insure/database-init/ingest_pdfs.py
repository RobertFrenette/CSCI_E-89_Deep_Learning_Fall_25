#!/usr/bin/env python3
"""
Script to ingest PDFs into ChromaDB
Can ingest a single PDF or all PDFs from a directory
"""
import os
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from chromadb_client import ChromaDBClient
from pdf_ingestion import PDFIngestion

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ingest_single_pdf(pdf_path: str, collection_name: str = "knowledge_base"):
    """Ingest a single PDF file"""
    try:
        client = ChromaDBClient()
        
        # Check health
        if not client.check_health():
            logger.error("ChromaDB is not accessible")
            sys.exit(1)
        
        ingestion = PDFIngestion(client)
        chunks_count = ingestion.ingest_pdf(pdf_path, collection_name=collection_name)
        
        logger.info(f"Successfully ingested {chunks_count} chunks from {pdf_path}")
        return chunks_count
    except Exception as e:
        logger.error(f"Failed to ingest PDF: {e}")
        sys.exit(1)


def ingest_directory(directory_path: str, collection_name: str = "knowledge_base", recursive: bool = True):
    """Ingest all PDFs from a directory"""
    try:
        client = ChromaDBClient()
        
        # Check health
        if not client.check_health():
            logger.error("ChromaDB is not accessible")
            sys.exit(1)
        
        ingestion = PDFIngestion(client)
        results = ingestion.ingest_directory(directory_path, collection_name=collection_name, recursive=recursive)
        
        total_chunks = sum(results.values())
        successful = sum(1 for v in results.values() if v > 0)
        
        logger.info(f"Successfully ingested {total_chunks} chunks from {successful} PDFs")
        return results
    except Exception as e:
        logger.error(f"Failed to ingest directory: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest PDFs into ChromaDB")
    parser.add_argument("path", help="Path to PDF file or directory")
    parser.add_argument(
        "--collection",
        default="knowledge_base",
        help="ChromaDB collection name (default: knowledge_base)"
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't search subdirectories (only for directories)"
    )
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if not path.exists():
        logger.error(f"Path does not exist: {path}")
        sys.exit(1)
    
    if path.is_file():
        if path.suffix.lower() != ".pdf":
            logger.error(f"File is not a PDF: {path}")
            sys.exit(1)
        ingest_single_pdf(str(path), args.collection)
    elif path.is_dir():
        ingest_directory(str(path), args.collection, recursive=not args.no_recursive)
    else:
        logger.error(f"Path is neither a file nor a directory: {path}")
        sys.exit(1)

