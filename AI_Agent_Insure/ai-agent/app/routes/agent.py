"""
Agent API routes for intelligent query processing
"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, List
import sys
import json
import asyncio
from pathlib import Path

# Add parent directory to path to import RAG engine
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.rag_engine import RAGEngine
from src.chromadb_client import ChromaDBClient
from src.ollama_client import OllamaClient
from app.models import QueryResponse, ChatRequest, QueryHistoryResponse
from app.services.mongodb_service import MongoDBService
from app.services.postgres_service import PostgreSQLService
from app.services.query_service import QueryService
from app.services.pdf_service import PDFService
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/agent", tags=["agent"])

# Initialize services
_mongodb_service = None
_query_service = None
_pdf_service = None


def get_mongodb_service() -> MongoDBService:
    """Get MongoDB service instance"""
    global _mongodb_service
    if _mongodb_service is None:
        _mongodb_service = MongoDBService()
    return _mongodb_service


def get_pdf_service() -> PDFService:
    """Get PDF service instance"""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service


def _map_query_type_to_mongo(routing_type: Optional[str]) -> str:
    """
    Map routing query type (sql, mongo, rag, hybrid) to MongoDB enum value.
    
    Args:
        routing_type: Query type from routing (sql, mongo, rag, hybrid)
        
    Returns:
        MongoDB-compatible query type (policy_info, claims, coverage, general)
    """
    if not routing_type:
        return "general"
    
    # Map routing types to MongoDB enum values
    type_mapping = {
        "sql": "policy_info",  # SQL queries are typically about policy data
        "mongo": "general",    # MongoDB queries are about user profiles
        "rag": "general",      # RAG queries are general knowledge base queries
        "hybrid": "coverage"   # Hybrid queries combine structured and document data
    }
    
    return type_mapping.get(routing_type.lower(), "general")


def get_query_service() -> QueryService:
    """Get QueryService instance with all dependencies"""
    global _query_service
    if _query_service is None:
        # Initialize PostgreSQL service
        postgres_service = None
        try:
            postgres_service = PostgreSQLService()
            # Test connection
            postgres_service.count_insureds()
            logger.info("PostgreSQL service initialized successfully")
        except Exception as e:
            logger.warning(f"PostgreSQL service not available: {e}")
            postgres_service = None
        
        # Initialize RAG engine
        chromadb_client = ChromaDBClient(
            host=settings.chromadb_host,
            port=settings.chromadb_port
        )
        ollama_client = OllamaClient(base_url=settings.ollama_base_url)
        rag_engine = RAGEngine(
            chromadb_client=chromadb_client,
            ollama_client=ollama_client,
            model=settings.ollama_model,
            collection_name=settings.chromadb_collection,
            top_k=settings.rag_top_k,
            max_context_length=settings.rag_max_context_length
        )
        
        # Initialize MongoDB service
        mongodb_service = get_mongodb_service()
        
        # Create QueryService
        _query_service = QueryService(
            postgres_service=postgres_service,
            mongodb_service=mongodb_service,
            rag_engine=rag_engine
        )
        logger.info("QueryService initialized with intelligent routing")
    
    return _query_service


@router.post("/chat/stream")
async def chat_agent_stream(
    request: ChatRequest,
    mongodb_service: MongoDBService = Depends(get_mongodb_service),
    query_service: QueryService = Depends(get_query_service)
):
    """
    Streaming chat interface with conversation history and intelligent routing
    Returns Server-Sent Events (SSE) stream of response chunks
    """
    async def generate_stream():
        accumulated_answer = ""
        sources = []
        query_type_result = None
        last_user_msg = None
        
        try:
            # Get user context if user_id is provided (skip for admin-app)
            messages = request.messages.copy()
            if request.user_id and request.user_id.lower() != "admin":
                try:
                    context_messages = await mongodb_service.get_user_context(
                        user_id=request.user_id,
                        limit=3
                    )
                    existing_user_messages = {msg.get("content") for msg in messages if msg.get("role") == "user"}
                    for ctx_msg in context_messages:
                        if ctx_msg.get("content") not in existing_user_messages:
                            messages.insert(0, ctx_msg)
                except Exception as e:
                    logger.warning(f"Failed to get user context: {e}")
            
            # Extract last user message for routing
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_msg = msg.get("content")
                    break
            
            if not last_user_msg:
                yield f"data: {json.dumps({'error': 'No user message found'})}\n\n"
                return
            
            # Route query
            from app.routing.query_router import detect_query_type
            query_type, cleaned_query = detect_query_type(last_user_msg)
            
            # Access control: check if user is admin
            is_admin = request.user_id and request.user_id.lower() == "admin"
            # If not admin and query is SQL/MongoDB/hybrid, it will be forced to RAG in process_query
            # So we should use streaming for RAG queries or when access control will redirect to RAG
            should_stream = query_type == 'rag' or (not is_admin and query_type in ['sql', 'mongo', 'hybrid'])
            
            if should_stream:
                # Process with streaming (will be RAG for non-admin users)
                result = await query_service.process_query(
                    query=cleaned_query,
                    user_id=request.user_id,
                    policy_number=request.policy_number,
                    collection_name=request.collection_name or settings.chromadb_collection,
                    top_k=request.top_k or settings.rag_top_k,
                    temperature=request.temperature or settings.rag_temperature,
                    stream=True
                )
                
                # Stream the response
                if 'stream' in result and result.get('stream'):
                    # Stream chunks from Ollama
                    sources = result.get('sources', [])
                    query_type_result = result.get('query_type', 'rag')
                    
                    logger.info(f"📡 Starting to stream response (query_type: {query_type_result})")
                    stream_iterator = result.get('stream')
                    chunk_count = 0
                    if stream_iterator:
                        for line in stream_iterator:
                            chunk_count += 1
                            if line:
                                try:
                                    # Ollama returns JSON lines (bytes or string)
                                    line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                                    if not line_str.strip():
                                        continue
                                    chunk_data = json.loads(line_str)
                                    if 'response' in chunk_data:
                                        text_chunk = chunk_data['response']
                                        accumulated_answer += text_chunk
                                        yield f"data: {json.dumps({'chunk': text_chunk, 'done': False})}\n\n"
                                    elif chunk_data.get('done', False):
                                        # Stream is complete
                                        break
                                except json.JSONDecodeError:
                                    # Skip invalid JSON lines
                                    continue
                                except Exception as e:
                                    logger.warning(f"Error processing stream chunk: {e}")
                                    continue
                    
                    logger.info(f"📡 Finished streaming response ({chunk_count} chunks processed)")
                    # Send final metadata
                    yield f"data: {json.dumps({'done': True, 'sources': sources, 'query_type': query_type_result})}\n\n"
                else:
                    # Fallback: send complete answer
                    accumulated_answer = result.get('answer', '')
                    sources = result.get('sources', [])
                    query_type_result = result.get('query_type')
                    yield f"data: {json.dumps({'chunk': accumulated_answer, 'done': True, 'sources': sources, 'query_type': query_type_result})}\n\n"
            else:
                # For SQL/MongoDB/hybrid queries (admin only), send complete response immediately
                result = await query_service.process_query(
                    query=cleaned_query,
                    user_id=request.user_id,
                    policy_number=request.policy_number,
                    collection_name=request.collection_name or settings.chromadb_collection,
                    top_k=request.top_k or settings.rag_top_k,
                    temperature=request.temperature or settings.rag_temperature,
                    stream=False
                )
                accumulated_answer = result.get('answer', '')
                sources = result.get('sources', [])
                query_type_result = result.get('query_type')
                yield f"data: {json.dumps({'chunk': accumulated_answer, 'done': True, 'sources': sources, 'query_type': query_type_result})}\n\n"
            
            # Log query after streaming is complete (skip logging for admin-app)
            if request.user_id and request.user_id.lower() != "admin" and last_user_msg:
                try:
                    query_id = await mongodb_service.log_query(
                        user_id=request.user_id,
                        query_text=last_user_msg,
                        query_type=_map_query_type_to_mongo(query_type_result),
                        answer=accumulated_answer,
                        sources=sources,
                        model=result.get('model', 'unknown') if 'result' in locals() else 'unknown',
                        retrieved_docs=result.get('retrieved_docs', 0) if 'result' in locals() else 0
                    )
                    logger.info(f"Logged streaming query {query_id} for user {request.user_id}")
                except Exception as e:
                    logger.warning(f"Failed to log streaming query: {e}")
                
        except Exception as e:
            logger.error(f"Streaming chat failed: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.get("/history/{user_id}", response_model=List[QueryHistoryResponse])
async def get_query_history(
    user_id: str,
    limit: int = 20,
    mongodb_service: MongoDBService = Depends(get_mongodb_service)
):
    """
    Get query history for a user
    
    Returns the user's recent query history from MongoDB.
    """
    try:
        history = await mongodb_service.get_user_query_history(
            user_id=user_id,
            limit=limit
        )
        
        return [QueryHistoryResponse(**q) for q in history]
        
    except Exception as e:
        logger.error(f"Failed to get query history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve query history: {str(e)}"
        )


@router.post("/upload/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    collection_name: Optional[str] = None,
    pdf_service: PDFService = Depends(get_pdf_service)
):
    """
    Upload and ingest a PDF file into ChromaDB
    
    Accepts a PDF file upload, extracts text, chunks it, and adds it to the ChromaDB collection.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF (.pdf)"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        
        # Use provided collection or default
        collection = collection_name or settings.chromadb_collection
        
        # Ingest PDF
        chunks_count = pdf_service.ingest_pdf_file(
            file_content=file_content,
            filename=file.filename,
            collection_name=collection
        )
        
        logger.info(f"Successfully ingested PDF {file.filename}: {chunks_count} chunks")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "filename": file.filename,
                "chunks_ingested": chunks_count,
                "collection": collection,
                "message": f"Successfully ingested {chunks_count} chunks from {file.filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload PDF {file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest PDF: {str(e)}"
        )

