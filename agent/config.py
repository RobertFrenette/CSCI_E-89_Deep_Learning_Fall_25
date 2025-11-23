"""
Configuration settings for the RAG Chatbot Application

Loads settings from environment variables via a `.env` file in the project root
with fallback to defaults defined in this file. Before running the application,
rename `sample.env.txt` in the project root to `.env` to customize settings.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Base directories
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

# Load environment variables from .env file in project root
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# Document and database paths
PDF_DIR = os.getenv("PDF_DIR", str(PROJECT_ROOT / "knowledge-base"))
CHROMA_DIR = os.getenv("CHROMA_DIR", str(PROJECT_ROOT / "vector-store" / "chroma_db"))
SQL_DB_PATH = os.getenv("SQL_DB_PATH", str(PROJECT_ROOT / "insured-db" / "insureds.db"))

# RAG settings (optimized for better retrieval quality)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1800"))  # Optimized chunk size (matches vectorstore creation)
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "350"))  # Optimized overlap (matches vectorstore creation)

RETRIEVAL_SCORE_THRESHOLD = os.getenv("RETRIEVAL_SCORE_THRESHOLD")  # Score threshold filtering (disabled - ChromaDB doesn't support this natively)
                                                                     # Can be implemented via custom retriever if needed
RETRIEVAL_SEARCH_TYPE = os.getenv("RETRIEVAL_SEARCH_TYPE", "similarity")  # Use similarity search for better relevance

TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))  # Higher temperature = more randomness
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "4"))  # Higher K = more context = (typically) better accuracy

# Audio settings
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # Options: tiny, base, small, medium, large

# Gradio settings
SERVER_NAME = os.getenv("SERVER_NAME", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "7861"))
SHARE = os.getenv("SHARE", "False").lower() in ("true", "1", "yes")  # Set to True to create a public link
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Application metadata
APP_TITLE = os.getenv("APP_TITLE", "AI Agent Insure - Agent Assist")
APP_DESCRIPTION = os.getenv(
    "APP_DESCRIPTION",
    "Ask questions about company documents and insured data using text or voice."
)

# SQL query prefix (optional - intelligent routing now detects SQL queries automatically)
# Comma-separated string in env, converted to list
SQL_QUERY_PREFIX = os.getenv("SQL_QUERY_PREFIX", "db:,database:").split(",")

# Example questions (demonstrates both intelligent routing and explicit prefix)
# Note: Complex lists are kept in code, but can be overridden if needed
EXAMPLE_QUESTIONS = [
    "What is AI Agent Insure?",  # Automatic RAG routing (company info)
    "What products does this company offer?",  # Automatic RAG routing (product info)
    "What is <PRODUCT_NAME>?",  # Automatic RAG routing (product info)
    "How many insureds are in the database?",  # Automatic SQL routing (count operation)
    "How many claims have been filed?",  # Automatic SQL routing (client data)
    "Show me information for insured <INSURED_NUMBER>.",  # Automatic SQL routing (client data)
]

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_DIR = os.getenv("LOG_DIR", str(BASE_DIR / "logs"))
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "app.log"))
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "True").lower() in ("true", "1", "yes")  # Set to False to disable file logging
LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "True").lower() in ("true", "1", "yes")  # Set to False to disable console logging

# Memory settings
MEMORY_TYPE = os.getenv("MEMORY_TYPE", "summary")  # Options: buffer, summary
MAX_TOKEN_LIMIT = int(os.getenv("MAX_TOKEN_LIMIT", "2000"))  # Max tokens for conversation summary (prevents unbounded growth)