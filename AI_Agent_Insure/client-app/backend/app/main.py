"""
FastAPI application entry point
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.database import init_postgres_pool, close_postgres_pool, close_mongo_connection
from app.routes import auth_router, user_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Skip database initialization during testing
    if not os.getenv("TESTING"):
        # Startup
        init_postgres_pool()
    yield
    # Shutdown
    if not os.getenv("TESTING"):
        close_postgres_pool()
        await close_mongo_connection()


# Create FastAPI app with OpenAPI docs
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Client-facing API for AI Agent Insurance Platform
    
    ## Features
    * User registration with policy validation
    * JWT-based authentication
    * Dual database access (PostgreSQL + MongoDB)
    * Policy information retrieval
    * AI query history
    
    ## Authentication
    All endpoints except /register and /login require a valid JWT token.
    Use the /login endpoint to obtain a token.
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


# Health endpoints first so 'Health' tag appears first in docs
@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness check endpoint - service is running"""
    return {"status": "healthy"}


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check endpoint - service can serve requests (DB connected and has data)"""
    from app.database import get_postgres_cursor, get_mongo_db
    
    try:
        # Check PostgreSQL connection and data
        with get_postgres_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM policies")
            policy_count = cursor.fetchone()["count"]
        
        # Check MongoDB connection (with error handling)
        try:
            db = get_mongo_db()
            user_count = await db.user_profiles.count_documents({})
        except Exception as mongo_error:
            return {
                "status": "not_ready",
                "message": "MongoDB connection failed",
                "postgres": "connected",
                "mongodb": "failed",
                "error": str(mongo_error)
            }, 503
        
        if policy_count == 0:
            return {
                "status": "not_ready",
                "message": "Database has no data",
                "postgres": "connected",
                "mongodb": "connected",
                "data_loaded": False
            }, 503
        
        return {
            "status": "ready",
            "postgres": "connected",
            "mongodb": "connected",
            "data_loaded": True,
            "policy_count": policy_count,
            "user_count": user_count
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "message": "Database connection failed",
            "error": str(e)
        }, 503

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "message": "AI Agent Insurance - Client API",
        "version": settings.app_version,
        "docs": "/docs"
    }

# Include routers
app.include_router(auth_router)
app.include_router(user_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
