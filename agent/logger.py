"""
Centralized logging configuration for the RAG Chatbot Application
"""

import logging
from pathlib import Path
from agent import config

def setup_logging():
    """
    Configure application-wide logging.
    
    Sets up handlers for console and/or file logging based on config settings.
    Should be called once at application startup.
    
    Returns:
        None
    """
    handlers = []
    
    # Console handler
    if config.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
        handlers.append(console_handler)
    
    # File handler
    if config.LOG_TO_FILE:
        # Create logs directory if it doesn't exist
        log_dir = Path(config.LOG_DIR)
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(config.LOG_FILE)
        file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        handlers=handlers,
        force=True
    )
    
    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized")
    logger.info(f"Log level: {config.LOG_LEVEL}")
    if config.LOG_TO_FILE:
        logger.info(f"Log file: {config.LOG_FILE}")
