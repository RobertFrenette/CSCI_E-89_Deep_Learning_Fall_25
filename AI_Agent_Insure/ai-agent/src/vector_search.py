"""
Vector search module for similarity search operations
"""
import logging
from typing import List, Dict, Optional
from .chromadb_client import ChromaDBClient

logger = logging.getLogger(__name__)


class VectorSearch:
    """Handle vector similarity search operations"""
    
    def __init__(self, chromadb_client: ChromaDBClient):
        """
        Initialize vector search
        
        Args:
            chromadb_client: ChromaDB client instance
        """
        self.chromadb_client = chromadb_client
    
    def search(
        self,
        query: str,
        collection_name: str = "knowledge_base",
        n_results: int = 5,
        metadata_filter: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents
        
        Args:
            query: Search query text
            collection_name: Name of the collection to search
            n_results: Number of results to return
            metadata_filter: Optional metadata filter (e.g., {"source_dir": "agent_support"})
            
        Returns:
            List of result dictionaries with 'id', 'document', 'metadata', 'distance'
        """
        try:
            # Query ChromaDB
            results = self.chromadb_client.query(
                collection_name=collection_name,
                query_texts=[query],
                n_results=n_results,
                where=metadata_filter
            )
            
            # Format results
            formatted_results = []
            
            if results.get('ids') and len(results['ids']) > 0:
                ids = results['ids'][0]
                documents = results.get('documents', [[]])[0]
                metadatas = results.get('metadatas', [[]])[0]
                distances = results.get('distances', [[]])[0]
                
                for i in range(len(ids)):
                    formatted_results.append({
                        'id': ids[i],
                        'document': documents[i] if i < len(documents) else '',
                        'metadata': metadatas[i] if i < len(metadatas) else {},
                        'distance': distances[i] if i < len(distances) else None,
                        'similarity': 1 - distances[i] if i < len(distances) else None
                    })
            
            logger.info(f"Search for '{query[:50]}...' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def search_multiple(
        self,
        queries: List[str],
        collection_name: str = "knowledge_base",
        n_results: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Search for multiple queries
        
        Args:
            queries: List of query texts
            collection_name: Name of the collection to search
            n_results: Number of results per query
            
        Returns:
            Dictionary mapping queries to their results
        """
        results = {}
        
        for query in queries:
            results[query] = self.search(
                query=query,
                collection_name=collection_name,
                n_results=n_results
            )
        
        return results
    
    def get_collection_stats(self, collection_name: str = "knowledge_base") -> Dict:
        """
        Get statistics about a collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.chromadb_client.get_collection_count(collection_name)
            
            # Get sample documents to analyze metadata
            sample_results = self.chromadb_client.query(
                collection_name=collection_name,
                query_texts=["sample"],
                n_results=min(10, count)
            )
            
            sources = set()
            if sample_results.get('metadatas') and len(sample_results['metadatas']) > 0:
                for metadata in sample_results['metadatas'][0]:
                    if 'source' in metadata:
                        sources.add(metadata['source'])
            
            return {
                'collection_name': collection_name,
                'document_count': count,
                'unique_sources': len(sources),
                'sources': list(sources)
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                'collection_name': collection_name,
                'document_count': 0,
                'unique_sources': 0,
                'sources': []
            }

