"""
MongoDB Query Handler Module
Handles natural language queries to the MongoDB database for user profiles.
"""
import logging
from typing import Optional, List, Dict, Any
from app.services.mongodb_service import MongoDBService
from app.routing.constants import DEFAULT_SQL_UNAVAILABLE_MSG

logger = logging.getLogger(__name__)


class MongoQueryHandler:
    """
    Handles MongoDB user profile queries and response formatting.
    
    Attributes:
        mongodb_service: MongoDBService instance for database queries
    """
    
    def __init__(self, mongodb_service: MongoDBService):
        """
        Initialize the MongoDB query handler.
        
        Args:
            mongodb_service: MongoDBService instance for database queries
        """
        self.mongodb_service = mongodb_service
    
    async def handle_query(self, question: str) -> str:
        """
        Handle a natural language question about user profiles and return formatted response.
        
        Args:
            question: User's question
            
        Returns:
            Formatted response with database results
        """
        if not self.mongodb_service:
            return "MongoDB database is not available."
        
        question_lower = question.lower()
        
        # Try each query type in order
        if self._is_count_users_query(question_lower):
            return await self._handle_count_users()
        
        if self._is_search_users_query(question_lower, question):
            return await self._handle_search_users(question)
        
        # Default: help message
        return """I can answer queries about user profiles:

1. "How many registered users are there?" or "How many user profiles are there?"
2. "Find user [username]" or "Search for user [username/email]"
3. "Show me user profile for [username]"

Please try one of these queries."""
    
    def _is_count_users_query(self, question_lower: str) -> bool:
        """Check if query is asking to count users"""
        return (
            ('user' in question_lower or 'profile' in question_lower) and
            any(keyword in question_lower for keyword in ['how many', 'count', 'total', 'registered']) and
            'information' not in question_lower and
            'info' not in question_lower and
            'search' not in question_lower and
            'find' not in question_lower
        )
    
    async def _handle_count_users(self) -> str:
        """Handle count users query"""
        try:
            count = await self.mongodb_service.count_user_profiles()
            return f"There are {count} registered user profiles in the database."
        except Exception as e:
            logger.error(f"Error counting users: {e}", exc_info=True)
            return f"Error retrieving user count: {str(e)}"
    
    def _is_search_users_query(self, question_lower: str, question: str) -> bool:
        """Check if query is asking to search for users"""
        return (
            ('user' in question_lower or 'profile' in question_lower) and
            any(keyword in question_lower for keyword in ['find', 'search', 'show', 'get', 'lookup', 'who is']) and
            'how many' not in question_lower and
            'count' not in question_lower
        )
    
    async def _handle_search_users(self, question: str) -> str:
        """Handle search users query"""
        try:
            # Extract search term from question
            search_term = self._extract_search_term(question)
            
            if not search_term:
                return "Please provide a username or email to search for. Example: 'Find user jsmith' or 'Search for user jsmith@example.com'"
            
            # Search user profiles
            users = await self.mongodb_service.search_user_profiles(search_term, limit=10)
            
            if not users:
                return f"No user profiles found matching '{search_term}'."
            
            if len(users) == 1:
                # Single user found - return detailed info
                user = users[0]
                response = f"User Profile Found:\n\n"
                response += f"Username: {user.get('username', 'N/A')}\n"
                response += f"Email: {user.get('email', 'N/A')}\n"
                response += f"User ID: {user.get('user_id', 'N/A')}\n"
                if user.get('created_at'):
                    response += f"Created: {user.get('created_at')}\n"
                if user.get('last_login'):
                    response += f"Last Login: {user.get('last_login')}\n"
                return response
            else:
                # Multiple users found - return list
                response = f"Found {len(users)} user profiles matching '{search_term}':\n\n"
                for i, user in enumerate(users, 1):
                    response += f"{i}. {user.get('username', 'N/A')} ({user.get('email', 'N/A')})\n"
                return response
                
        except Exception as e:
            logger.error(f"Error searching users: {e}", exc_info=True)
            return f"Error searching user profiles: {str(e)}"
    
    def _extract_search_term(self, question: str) -> Optional[str]:
        """Extract search term (username or email) from question"""
        question_lower = question.lower()
        
        # Look for patterns like "user jsmith", "username jsmith", "find jsmith", etc.
        words = question.split()
        
        # Find keywords that might precede the search term
        keywords = ['user', 'username', 'email', 'profile', 'find', 'search', 'show', 'get', 'lookup']
        
        for i, word in enumerate(words):
            if word.lower() in keywords and i + 1 < len(words):
                # Get the next word as potential search term
                search_term = words[i + 1].strip('.,!?;:')
                # Remove common words
                if search_term.lower() not in ['for', 'with', 'by', 'the', 'a', 'an']:
                    return search_term
        
        # If no keyword found, try to extract email or username pattern
        import re
        # Try to find email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, question)
        if email_match:
            return email_match.group(0)
        
        # Try to find username-like pattern (alphanumeric, 3+ chars)
        username_pattern = r'\b[a-zA-Z0-9_]{3,}\b'
        matches = re.findall(username_pattern, question)
        # Filter out common words
        common_words = {'user', 'users', 'profile', 'profiles', 'find', 'search', 'show', 'get', 'how', 'many', 'count', 'total', 'the', 'a', 'an', 'for', 'with', 'by', 'is', 'are', 'there', 'in', 'database'}
        for match in matches:
            if match.lower() not in common_words:
                return match
        
        return None

