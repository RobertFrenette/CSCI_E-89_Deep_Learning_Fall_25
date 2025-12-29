"""
Query Service
Orchestrates query processing pipeline with intelligent routing
Coordinates SQL, MongoDB, RAG, and hybrid queries
"""
import logging
from typing import Optional, Dict, Any, Tuple
from app.routing.query_router import detect_query_type
from app.routing.sql_query_handler import SQLQueryHandler
from app.routing.mongo_query_handler import MongoQueryHandler
from app.services.postgres_service import PostgreSQLService
from app.services.mongodb_service import MongoDBService
from app.services.cache_service import get_cache_service
from src.rag_engine import RAGEngine

logger = logging.getLogger(__name__)


class QueryService:
    """
    Service that orchestrates the complete query processing pipeline.
    
    Coordinates:
    - Query routing (SQL vs MongoDB vs RAG vs Hybrid)
    - Query execution via domain processors
    - Response synthesis for hybrid queries
    """
    
    def __init__(
        self,
        postgres_service: Optional[PostgreSQLService],
        mongodb_service: Optional[MongoDBService],
        rag_engine: RAGEngine
    ):
        """
        Initialize the query service.
        
        Args:
            postgres_service: PostgreSQLService instance (can be None)
            mongodb_service: MongoDBService instance (can be None)
            rag_engine: RAGEngine instance for document queries
        """
        self.postgres_service = postgres_service
        self.mongodb_service = mongodb_service
        self.rag_engine = rag_engine
        self.sql_query_handler = SQLQueryHandler(postgres_service) if postgres_service else None
        self.mongo_query_handler = MongoQueryHandler(mongodb_service) if mongodb_service else None
        self.cache_service = get_cache_service()
    
    async def process_query(
        self,
        query: str,
        user_id: Optional[str] = None,
        policy_number: Optional[str] = None,
        collection_name: Optional[str] = None,
        top_k: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Process a query with intelligent routing.
        
        Args:
            query: User's question
            user_id: Optional user ID for context
            collection_name: Optional ChromaDB collection name
            top_k: Optional number of documents to retrieve
            temperature: Optional LLM temperature
            stream: Whether to stream the response
            
        Returns:
            Dictionary with answer, sources, query_type, and metadata
        """
        try:
            # Step 1: Route query
            query_type, cleaned_query = detect_query_type(query)
            logger.info(f"Query routed to: {query_type}")
            
            # Check cache first (only for non-streaming, non-user-specific queries)
            if not stream and not user_id:
                cached_result = self.cache_service.get(query, query_type)
                if cached_result:
                    logger.info(f"Returning cached result for query: {query[:50]}...")
                    return cached_result
            
            # Step 2: Access control
            is_admin = user_id and user_id.lower() == "admin"
            is_guest = user_id and user_id.lower() == "guest" or not user_id
            is_authenticated_client = user_id and not is_admin and not is_guest
            
            # Get account info (insured_id and policy_number) for authenticated client users
            insured_id = None
            # If policy_number is provided directly, use it; otherwise try to look it up
            if not policy_number and is_authenticated_client:
                # user_id could be policy_number or username
                # Try to get account info - if user_id is policy_number, look it up differently
                if self.mongodb_service:
                    try:
                        # First, try as username
                        account_info = await self.mongodb_service.get_account_info_from_username(user_id)
                        if account_info:
                            insured_id = account_info.get("insured_id")
                            policy_number = account_info.get("policy_number")
                        else:
                            # If not found as username, try as policy_number
                            # Look up user by policy_number
                            user = await self.mongodb_service.get_user_by_policy_number(user_id)
                            if user:
                                insured_id = user.get("insured_id")
                                policy_number = user.get("policy_number")
                        
                        if not policy_number and not insured_id:
                            logger.warning(f"Authenticated client user '{user_id}' has no account info, treating as guest")
                            is_authenticated_client = False
                            is_guest = True
                    except Exception as e:
                        logger.error(f"Error getting account info for user {user_id}: {e}")
                        is_authenticated_client = False
                        is_guest = True
                else:
                    # If no MongoDB service, can't look up account info
                    is_authenticated_client = False
                    is_guest = True
            elif policy_number and is_authenticated_client:
                # If policy_number is provided, try to get insured_id from it
                if self.mongodb_service:
                    try:
                        user = await self.mongodb_service.get_user_by_policy_number(policy_number)
                        if user:
                            insured_id = user.get("insured_id")
                    except Exception as e:
                        logger.warning(f"Could not get insured_id for policy_number {policy_number}: {e}")
            
            # Access control rules:
            # - Admin (admin-app): Can query all data sources (SQL, MongoDB, RAG, Hybrid) - no filtering
            # - Authenticated client users: Can query SQL (filtered to their policy only) and RAG
            # - Guest (client-app unauthenticated): Can only query RAG
            if is_guest and query_type in ['sql', 'mongo', 'hybrid']:
                logger.info(f"Guest user attempted {query_type} query. Access denied.")
                return {
                    "query": query,
                    "answer": "I can only provide information from our company documentation and knowledge base. To query database information (policies, claims, customer data), please register and log in to your account.",
                    "sources": [],
                    "query_type": "access_denied",
                    "metadata": {}
                }
            elif is_authenticated_client and query_type in ['mongo', 'hybrid']:
                # Authenticated client users can't query MongoDB (user profiles) or hybrid
                logger.info(f"Authenticated client user '{user_id}' attempted {query_type} query. Redirecting to RAG-only.")
                query_type = 'rag'
            elif is_authenticated_client and query_type == 'sql':
                # Authenticated client users can query SQL, but ONLY for their own policy data
                if not policy_number:
                    logger.warning(f"Authenticated client user '{user_id}' has no policy_number, restricting to RAG")
                    query_type = 'rag'
                else:
                    logger.info(f"Authenticated client user '{user_id}' (policy_number: {policy_number}) querying SQL for their policy")
            
            # Step 3: Execute based on type
            if query_type == 'sql':
                result = self._process_sql_query(cleaned_query, user_id, insured_id, policy_number)
            elif query_type == 'mongo':
                result = await self._process_mongo_query(cleaned_query, user_id)
            elif query_type == 'hybrid':
                result = self._process_hybrid_query(cleaned_query, user_id, collection_name, top_k, temperature)
            else:  # 'rag'
                result = self._process_rag_query(cleaned_query, user_id, collection_name, top_k, temperature, stream)
            
            # Cache result for non-streaming, non-user-specific queries
            if not stream and not user_id and 'error' not in result:
                # Cache for 5 minutes (300 seconds)
                self.cache_service.set(query, query_type, result, ttl=300)
            
            return result
                
        except Exception as e:
            logger.error(f"Query processing failed: {e}", exc_info=True)
            return {
                "query": query,
                "answer": f"An error occurred while processing your query: {str(e)}",
                "sources": [],
                "query_type": "error",
                "error": str(e)
            }
    
    async def _process_mongo_query(self, query: str, user_id: Optional[str]) -> Dict[str, Any]:
        """Process MongoDB-only query (user profiles)"""
        if not self.mongo_query_handler:
            return {
                "query": query,
                "answer": "MongoDB database is not available.",
                "sources": [],
                "query_type": "mongo",
                "retrieved_docs": 0,
                "context_length": 0,
                "model": "mongodb"
            }
        
        try:
            mongo_response = await self.mongo_query_handler.handle_query(query)
            return {
                "query": query,
                "answer": mongo_response,
                "sources": ["MongoDB Database"],
                "query_type": "mongo",
                "retrieved_docs": 0,
                "context_length": len(mongo_response) if mongo_response else 0,
                "model": "mongodb"
            }
        except Exception as e:
            logger.error(f"MongoDB query failed: {e}", exc_info=True)
            return {
                "query": query,
                "answer": f"Error querying MongoDB: {str(e)}",
                "sources": [],
                "query_type": "mongo",
                "retrieved_docs": 0,
                "context_length": 0,
                "model": "mongodb",
                "error": str(e)
            }
    
    def _process_sql_query(self, query: str, user_id: Optional[str], insured_id: Optional[str] = None, policy_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Process SQL-only query
        
        Args:
            query: Query text
            user_id: User ID (for logging)
            insured_id: Optional insured_id to filter queries (for authenticated users)
            policy_number: Optional policy_number for direct policy queries (for authenticated users)
        """
        if not self.sql_query_handler:
            return {
                "query": query,
                "answer": "SQL database is not available.",
                "sources": [],
                "query_type": "sql",
                "retrieved_docs": 0,
                "context_length": 0,
                "model": "postgresql"
            }
        
        try:
            # Pass both insured_id and policy_number to handler for account-specific filtering
            sql_response = self.sql_query_handler.handle_query(query, insured_id=insured_id, policy_number=policy_number)
            return {
                "query": query,
                "answer": sql_response,
                "sources": ["PostgreSQL Database"],
                "query_type": "sql",
                "retrieved_docs": 0,
                "context_length": len(sql_response) if sql_response else 0,
                "model": "postgresql"
            }
        except Exception as e:
            logger.error(f"SQL query failed: {e}", exc_info=True)
            return {
                "query": query,
                "answer": f"Error querying database: {str(e)}",
                "sources": [],
                "query_type": "sql",
                "retrieved_docs": 0,
                "context_length": 0,
                "model": "postgresql",
                "error": str(e)
            }
    
    def _process_rag_query(
        self,
        query: str,
        user_id: Optional[str],
        collection_name: Optional[str],
        top_k: Optional[int],
        temperature: Optional[float],
        stream: bool = False
    ) -> Dict[str, Any]:
        """Process RAG-only query"""
        try:
            # Build kwargs for RAG engine query
            query_kwargs = {
                "query": query,
                "collection_name": collection_name,
                "temperature": temperature or 0.7,
                "stream": stream
            }
            if top_k is not None:
                query_kwargs["top_k"] = top_k
            
            result = self.rag_engine.query(**query_kwargs)
            result["query_type"] = "rag"
            return result
        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)
            return {
                "query": query,
                "answer": f"Error searching documents: {str(e)}",
                "sources": [],
                "query_type": "rag",
                "retrieved_docs": 0,
                "context_length": 0,
                "model": "",
                "error": str(e)
            }
    
    def _process_hybrid_query(
        self,
        query: str,
        user_id: Optional[str],
        collection_name: Optional[str],
        top_k: Optional[int],
        temperature: Optional[float]
    ) -> Dict[str, Any]:
        """
        Process hybrid query (SQL + RAG).
        
        Executes both SQL and RAG queries, then synthesizes the results.
        """
        try:
            # Execute SQL query
            sql_result = None
            sql_context = ""
            if self.sql_query_handler:
                try:
                    sql_response = self.sql_query_handler.handle_query(query)
                    sql_context = f"Database Information:\n{sql_response}\n\n"
                    sql_result = sql_response
                except Exception as e:
                    logger.warning(f"SQL part of hybrid query failed: {e}")
            
            # Execute RAG query with SQL context
            query_kwargs = {
                "query": query,
                "collection_name": collection_name,
                "temperature": temperature or 0.7,
                "sql_context": sql_context if sql_context else None
            }
            if top_k is not None:
                query_kwargs["top_k"] = top_k
            
            rag_result = self.rag_engine.query(**query_kwargs)
            
            # Combine sources
            sources = rag_result.get("sources", [])
            if sql_result:
                sources.append("PostgreSQL Database")
            
            # Enhance answer with SQL context if available
            answer = rag_result.get("answer", "")
            if sql_result and sql_context:
                answer = f"{answer}\n\nAdditional Database Information:\n{sql_result}"
            
            return {
                "query": query,
                "answer": answer,
                "sources": sources,
                "query_type": "hybrid",
                "retrieved_docs": rag_result.get("retrieved_docs", 0),
                "context_length": rag_result.get("context_length", 0),
                "model": rag_result.get("model", ""),
                "sql_result": sql_result,
                "rag_result": rag_result
            }
        except Exception as e:
            logger.error(f"Hybrid query failed: {e}", exc_info=True)
            return {
                "query": query,
                "answer": f"Error processing hybrid query: {str(e)}",
                "sources": [],
                "query_type": "hybrid",
                "retrieved_docs": 0,
                "context_length": 0,
                "model": "",
                "error": str(e)
            }

