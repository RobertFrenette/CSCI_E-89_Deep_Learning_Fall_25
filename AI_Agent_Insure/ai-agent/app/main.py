"""
FastAPI application entry point for AI Agent API
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.database.mongodb import close_mongo_connection
from app.routes.agent import router as agent_router
from app.models import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting AI Agent API...")
    yield
    # Shutdown
    logger.info("Shutting down AI Agent API...")
    await close_mongo_connection()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    AI Agent Intelligent Query API for Insurance Platform
    
    ## Features
    * Intelligent query routing (SQL, RAG, or Hybrid)
    * PostgreSQL integration for structured data queries
    * RAG-based question answering using ChromaDB and Ollama
    * Query logging to MongoDB
    * User context awareness
    * Conversation history support
    
    ## Query Routing
    The system automatically routes queries:
    - **SQL**: Structured data queries (insureds, policies, claims, statistics)
    - **RAG**: Document-based queries (company info, products, procedures)
    - **Hybrid**: Queries requiring both structured data and documents
    
    ## Endpoints
    * POST /api/agent/chat/stream - Streaming chat interface with conversation history and intelligent routing
    * GET /api/agent/history/{user_id} - Get user query history
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from src.chromadb_client import ChromaDBClient
    from src.ollama_client import OllamaClient
    from app.database.mongodb import get_mongo_client
    from app.database.postgres import check_postgres_health
    
    chromadb_healthy = False
    ollama_healthy = False
    mongodb_healthy = False
    postgres_healthy = False
    
    # Check ChromaDB
    try:
        chromadb_client = ChromaDBClient(
            host=settings.chromadb_host,
            port=settings.chromadb_port
        )
        chromadb_healthy = chromadb_client.check_health()
    except Exception as e:
        logger.warning(f"ChromaDB health check failed: {e}")
    
    # Check Ollama
    try:
        ollama_client = OllamaClient(base_url=settings.ollama_base_url)
        ollama_healthy = ollama_client.check_health()
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
    
    # Check MongoDB
    try:
        mongo_client = get_mongo_client()
        # Motor client is async, ping the admin database
        await mongo_client.admin.command('ping')
        mongodb_healthy = True
    except Exception as e:
        logger.warning(f"MongoDB health check failed: {e}")
        mongodb_healthy = False
    
    # Check PostgreSQL
    try:
        postgres_healthy = check_postgres_health()
    except Exception as e:
        logger.warning(f"PostgreSQL health check failed: {e}")
        postgres_healthy = False
    
    # Overall status is healthy if all critical services are up
    # PostgreSQL is optional (for SQL queries), so we don't require it for "healthy" status
    overall_status = "healthy" if (chromadb_healthy and ollama_healthy and mongodb_healthy) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        chromadb=chromadb_healthy,
        ollama=ollama_healthy,
        mongodb=mongodb_healthy,
        postgres=postgres_healthy
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Agent RAG API",
        "version": settings.app_version,
        "docs": "/docs"
    }

