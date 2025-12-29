"""
ChromaDB client module for vector store operations
"""
import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """Client for interacting with ChromaDB vector store"""
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """
        Initialize ChromaDB client
        
        Args:
            host: ChromaDB host (default: from env or 'localhost')
            port: ChromaDB port (default: from env or 8000)
        """
        self.host = host or os.getenv('CHROMADB_HOST', 'localhost')
        self.port = port or int(os.getenv('CHROMADB_PORT', '8000'))
        
        # Determine if we're connecting to a remote server or local
        # Use HttpClient if:
        # 1. CHROMADB_USE_HTTP is set to true
        # 2. Port is 8000 (default ChromaDB server port) - indicates server connection
        # 3. Host is not localhost/127.0.0.1 (remote server)
        use_http = os.getenv('CHROMADB_USE_HTTP', '').lower() in ('true', '1', 'yes')
        use_persistent = os.getenv('CHROMADB_USE_PERSISTENT', '').lower() in ('true', '1', 'yes')
        
        if use_persistent:
            # Local persistent client (explicitly requested)
            persist_directory = os.getenv('CHROMADB_PERSIST_DIR', './chroma_db')
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        elif use_http or self.port == 8000 or (self.host != 'localhost' and self.host != '127.0.0.1'):
            # Remote server connection via HTTP (default for port 8000)
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        else:
            # Local persistent client (fallback for local development)
            persist_directory = os.getenv('CHROMADB_PERSIST_DIR', './chroma_db')
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        
        logger.info(f"ChromaDB client initialized: {self.host}:{self.port}")
    
    def check_health(self) -> bool:
        """Check if ChromaDB is accessible"""
        try:
            self.client.heartbeat()
            return True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False
    
    def get_or_create_collection(self, collection_name: str) -> chromadb.Collection:
        """
        Get existing collection or create a new one
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            ChromaDB Collection object
        """
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": f"Collection for {collection_name}"}
            )
            logger.info(f"Collection '{collection_name}' ready")
            return collection
        except Exception as e:
            logger.error(f"Failed to get/create collection '{collection_name}': {e}")
            raise
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ) -> None:
        """
        Add documents to a collection
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of unique IDs for documents
        """
        collection = self.get_or_create_collection(collection_name)
        
        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to '{collection_name}'")
        except Exception as e:
            logger.error(f"Failed to add documents to '{collection_name}': {e}")
            raise
    
    def query(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query the vector store for similar documents
        
        Args:
            collection_name: Name of the collection to query
            query_texts: List of query text strings
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dictionary with 'ids', 'documents', 'metadatas', 'distances'
        """
        collection = self.get_or_create_collection(collection_name)
        
        try:
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where
            )
            logger.info(f"Query returned {len(results.get('ids', [])[0] if results.get('ids') else [])} results")
            return results
        except Exception as e:
            logger.error(f"Query failed for '{collection_name}': {e}")
            raise
    
    def get_collection_count(self, collection_name: str) -> int:
        """Get the number of documents in a collection"""
        try:
            collection = self.get_or_create_collection(collection_name)
            count = collection.count()
            return count
        except Exception as e:
            logger.error(f"Failed to get count for '{collection_name}': {e}")
            return 0
    
    def list_collections(self) -> List[str]:
        """List all collection names"""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection"""
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
        except Exception as e:
            logger.error(f"Failed to delete collection '{collection_name}': {e}")
            raise
    
    def reset(self) -> None:
        """Reset the entire database (use with caution)"""
        try:
            self.client.reset()
            logger.warning("ChromaDB database reset")
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            raise

