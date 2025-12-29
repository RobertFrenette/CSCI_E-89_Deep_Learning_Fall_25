"""
Pydantic models for AI Agent API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class QueryResponse(BaseModel):
    """Response model for agent query"""
    answer: str = Field(..., description="Generated answer")
    sources: List[str] = Field(default_factory=list, description="Source documents used")
    model: str = Field(..., description="LLM model used")
    retrieved_docs: int = Field(..., description="Number of documents retrieved")
    context_length: int = Field(..., description="Length of context used")
    query_id: Optional[str] = Field(None, description="Query ID for history lookup")
    query_type: Optional[str] = Field(None, description="Query routing type (sql, rag, hybrid)")
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class QueryHistoryResponse(BaseModel):
    """Response model for query history"""
    query_id: str
    query_text: str
    query_type: Optional[str]
    answer: Optional[str]
    sources: List[str]
    query_timestamp: datetime
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ChatRequest(BaseModel):
    """Request model for chat interface"""
    messages: List[Dict[str, str]] = Field(..., description="Conversation history")
    user_id: Optional[str] = Field(None, description="User ID for logging and context")
    policy_number: Optional[str] = Field(None, description="Policy number for authenticated users to filter database queries")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Number of documents to retrieve")
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0, description="LLM temperature")
    collection_name: Optional[str] = Field(None, description="ChromaDB collection name")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    chromadb: bool
    ollama: bool
    mongodb: bool
    postgres: Optional[bool] = False

