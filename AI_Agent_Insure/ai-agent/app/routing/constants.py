"""
Constants for query routing
Contains indicator dictionaries and scoring weights for routing queries
"""

# SQL Database Indicators (structured data queries)
SQL_INDICATORS = {
    # Direct data entity references
    'strong': [
        'insured', 'insureds', 'policyholder', 'policyholders', 
        'customer', 'customers', 'client', 'clients',
        'policy', 'policies', 'policy number', 'policy id',
        'claim', 'claims', 'claim number', 'claim id',
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

# MongoDB User Profile Indicators
MONGO_INDICATORS = {
    'strong': [
        'user profile', 'user profiles', 'registered user', 'registered users',
        'user account', 'user accounts', 'username', 'usernames',
        'user email', 'user emails', 'user login', 'user logins'
    ],
    'operations': [
        'how many users', 'how many registered', 'count users', 'total users',
        'list users', 'show users', 'find user', 'search user',
        'user information', 'user info', 'user details'
    ],
    'qualifiers': [
        'user profile', 'user account', 'registered user'
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
        'how do i', 'how do you', 'how can i', 'how can you',
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
DEFAULT_SQL_HELP_MSG = """I can answer several types of database queries:

1. "How many insureds are there in the database?"
2. "How many policies are there in the database?"
3. "How many claims have been filed?"
4. "Show me all the high risk policies."
5. "Show me information for insured [ID]"

Please try one of these queries."""
DEFAULT_NO_INSURED_ID_MSG = "Please provide an insured ID (e.g., 'BQ4DCXWL'). Example: 'Show me information for insured BQ4DCXWL'"

