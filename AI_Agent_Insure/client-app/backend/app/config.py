from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "AI Agent Insurance - Client API"
    app_version: str = "1.0.0"
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    
    # PostgreSQL
    postgres_host: str = "postgres"  # Docker service name
    postgres_port: int = 5432
    postgres_db: str = "insurance_db"
    postgres_user: str = "insure_admin"
    postgres_password: str = ""
    
    # MongoDB
    mongo_host: str = "mongodb"  # Docker service name
    mongo_port: int = 27017
    mongo_db: str = "insurance_users"
    # Use root credentials (can be overridden by MONGO_ROOT_USER/MONGO_ROOT_PASSWORD env vars)
    mongo_user: str = "mongo_admin"
    mongo_password: str = "mongo_secure_pass_2025"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    """Get cached settings instance"""
    return Settings()
