"""
Constants for query routing and SQL query handling.

Contains indicator dictionaries, patterns, and magic numbers used
for routing queries between SQL database and RAG system.
"""

# SQL Database Indicators (client data queries)
SQL_INDICATORS = {
    # Direct data entity references
    'strong': [
        'insured', 'insureds', 'policyholder', 'policyholders', 
        'customer', 'customers', 'client', 'clients',
        'policy number', 'policy id', 'claim number', 'claim id',
        'high risk', 'low risk', 'risk score', 'risk level',
        'premium', 'deductible', 'coverage limit',
        'claim history', 'claims history'
    ],
    # Data operation keywords
    'operations': [
        'how many', 'count', 'total', 'average', 'sum',
        'list all', 'show all', 'find all', 'get all',
        'statistics', 'stats', 'data about'
    ],
    # Specific to structured data
    'qualifiers': [
        'in the database', 'from the database',
        'with coverage', 'with policy', 'with claim'
    ]
}

# RAG Document Indicators (company/product information)
RAG_INDICATORS = {
    # Company information
    'company': [
        'ai agent insure', 'this company', 'your company',
        'company offer', 'company provide', 'company history',
        'about ai agent', 'what is ai agent insure',
        'mission', 'vision', 'values'
    ],
    # Product/service information
    'products': [
        'insurance product', 'product line', 'coverage type',
        'what products', 'what services', 'types of insurance',
        'ai liability', 'data breach', 'model failure',
        'coverage include', 'coverage cover'
    ],
    # Procedural/guide information
    'procedures': [
        'how to file', 'how to submit', 'how to apply',
        'what is the process', 'steps to', 'procedure for',
        'guide', 'documentation', 'requirements for'
    ]
}

# Routing scoring weights
SQL_STRONG_WEIGHT = 3  # Strong weight for direct entity references
SQL_MEDIUM_WEIGHT = 2  # Medium weight for operations and qualifiers
RAG_STRONG_WEIGHT = 3  # Strong weight for company info
RAG_MEDIUM_WEIGHT = 2  # Medium weight for product info and procedures
SQL_MIN_SCORE_THRESHOLD = 2  # Minimum score to route to SQL

# SQL Query constants
HIGH_RISK_SCORE_THRESHOLD = 90  # Minimum risk score for high-risk policies
INSURED_ID_PATTERN = r'\b([A-Z0-9]{8,10})\b'  # Pattern to match insured ID

# Default messages
DEFAULT_SQL_UNAVAILABLE_MSG = "SQL database is not available."
DEFAULT_SQL_HELP_MSG = """I can answer four types of database queries:

1. "How many insureds are there in the database?"
2. "How many claims have been filed?"
3. "Show me all the high risk policies."
4. "Show me information for insured [ID]"

Please try one of these queries."""
DEFAULT_NO_INSURED_ID_MSG = "Please provide an insured ID (e.g., 'BQ4DCXWL'). Example: 'Show me information for insured BQ4DCXWL'"

