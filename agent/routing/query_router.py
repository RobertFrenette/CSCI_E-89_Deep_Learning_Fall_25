"""
Query Router Module
Used in the QueryService to route queries to SQL or RAG.

Intelligently detects whether a query should be routed to SQL database
or RAG system using multi-factor analysis.
"""

import logging
from agent import config
from agent.routing.constants import (
    SQL_INDICATORS,
    RAG_INDICATORS,
    SQL_STRONG_WEIGHT,
    SQL_MEDIUM_WEIGHT,
    RAG_STRONG_WEIGHT,
    RAG_MEDIUM_WEIGHT,
    SQL_MIN_SCORE_THRESHOLD
)

logger = logging.getLogger(__name__)

def detect_query_type(question: str) -> tuple[str, str]:
    """
    Intelligently detect whether query is for SQL database or RAG system.
    
    Uses a multi-factor approach:
    1. Explicit prefix ("DB:" or "database:") forces SQL routing
    2. Semantic analysis of query intent (looking for data queries vs info queries)
    3. Keyword analysis (insureds, policies, claims vs company info)
    
    SQL queries about client/policyholder data are automatically detected.
    Document queries about company info default to RAG.
    
    This ensures:
    - "What is AI Agent Insure?" → RAG (company documents)
    - "Show me high risk insureds" → SQL (client database)
    - "How many policies?" → SQL (structured data)
    
    Args:
        question: User's question
        
    Returns:
        Tuple of (query_type, cleaned_question)
        query_type: 'sql' or 'rag'
        cleaned_question: Question with prefix removed if SQL query
    """
    question_stripped = question.strip()
    question_lower = question_stripped.lower()
    
    # Check for explicit SQL prefix (highest priority)
    for prefix in config.SQL_QUERY_PREFIX:
        if question_lower.startswith(prefix):
            # Remove prefix and return SQL type
            cleaned_question = question_stripped[len(prefix):].strip()
            logger.debug("SQL routing: explicit prefix detected")
            return 'sql', cleaned_question
    
    # Count indicators
    sql_score = 0
    rag_score = 0
    
    # Check for SQL indicators
    for indicator in SQL_INDICATORS['strong']:
        if indicator in question_lower:
            sql_score += SQL_STRONG_WEIGHT
            logger.debug(f"SQL indicator (strong): '{indicator}'")
    
    for indicator in SQL_INDICATORS['operations']:
        if indicator in question_lower:
            sql_score += SQL_MEDIUM_WEIGHT
            logger.debug(f"SQL indicator (operation): '{indicator}'")
    
    for indicator in SQL_INDICATORS['qualifiers']:
        if indicator in question_lower:
            sql_score += SQL_MEDIUM_WEIGHT
            logger.debug(f"SQL indicator (qualifier): '{indicator}'")
    
    # Check for RAG indicators
    for indicator in RAG_INDICATORS['company']:
        if indicator in question_lower:
            rag_score += RAG_STRONG_WEIGHT
            logger.debug(f"RAG indicator (company): '{indicator}'")
    
    for indicator in RAG_INDICATORS['products']:
        if indicator in question_lower:
            rag_score += RAG_MEDIUM_WEIGHT
            logger.debug(f"RAG indicator (product): '{indicator}'")
    
    for indicator in RAG_INDICATORS['procedures']:
        if indicator in question_lower:
            rag_score += RAG_MEDIUM_WEIGHT
            logger.debug(f"RAG indicator (procedure): '{indicator}'")
    
    # Decision logic
    logger.debug(f"Routing scores - SQL: {sql_score}, RAG: {rag_score}")
    
    if sql_score > rag_score and sql_score >= SQL_MIN_SCORE_THRESHOLD:
        logger.info(f"SQL routing: score {sql_score} vs {rag_score}")
        return 'sql', question_stripped
    else:
        # Default to RAG (documents) for ambiguous or company info queries
        logger.info(f"RAG routing: score {sql_score} vs {rag_score}")
        return 'rag', question_stripped
