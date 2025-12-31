"""
Configuration settings for AI Agent API
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "AI Agent Insurance - RAG Agent API"
    app_version: str = "1.0.0"
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8002
    
    # ChromaDB
    chromadb_host: str = "chromadb"  # Docker service name
    chromadb_port: int = 8000
    chromadb_use_http: bool = True
    chromadb_collection: str = "knowledge_base"
    
    # Ollama
    ollama_base_url: str = "http://ollama:11434"  # Docker service name
    ollama_model: str = "phi3:mini"
    
    # MongoDB (for query logging)
    mongo_host: str = "mongodb"  # Docker service name
    mongo_port: int = 27017
    mongo_db: str = "insurance_users"
    mongo_user: str = "mongo_admin"
    mongo_password: str = "mongo_secure_pass_2025"
    
    # PostgreSQL (for structured data queries)
    postgres_host: str = "postgres"  # Docker service name
    postgres_port: int = 5432
    postgres_db: str = "insurance_db"
    postgres_user: str = "insure_admin"
    postgres_password: str = "insure_secure_pass_2025"
    
    # RAG Settings
    rag_top_k: int = 3  # Reduced for faster retrieval and processing
    rag_max_context_length: int = 3000  # Optimized for phi3:mini efficiency
    rag_temperature: float = 0.1  # Very low for highly factual, deterministic responses
    
    # CORS
    cors_origins: list = [
        "http://localhost:3000",  # Admin frontend
        "http://localhost:5001",  # Client frontend
        "http://admin-frontend:3000",
        "http://client-frontend:5000"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    """Get cached settings instance"""
    return Settings()

