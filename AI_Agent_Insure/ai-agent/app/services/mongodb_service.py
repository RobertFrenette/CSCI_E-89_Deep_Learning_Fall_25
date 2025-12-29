"""
MongoDB service for query logging and user context
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.database.mongodb import get_mongo_db
import logging

logger = logging.getLogger(__name__)


class MongoDBService:
    """Service for MongoDB operations related to query logging"""
    
    async def log_query(
        self,
        user_id: Optional[str],
        query_text: str,
        query_type: Optional[str],
        answer: str,
        sources: List[str],
        model: str,
        retrieved_docs: int
    ) -> str:
        """
        Log a query to MongoDB
        
        Args:
            user_id: User ID (can be None for anonymous queries)
            query_text: Original query text
            query_type: Type of query (policy_info, claims, coverage, general)
            answer: Generated answer
            sources: List of source documents
            model: Model used for generation
            retrieved_docs: Number of documents retrieved
            
        Returns:
            Query ID (ObjectId as string)
        """
        db = get_mongo_db()
        
        # Convert user_id to ObjectId if provided
        # Create a deterministic ObjectId for non-ObjectId strings (like "admin")
        query_doc = {
            "query_text": query_text,
            "query_type": query_type or "general",
            "rag_response": answer,
            "sources_used": sources,
            "model_used": model,
            "retrieved_docs": retrieved_docs,
            "query_timestamp": datetime.utcnow(),
            "satisfaction_rating": 0  # Set to 0 instead of None (schema requires int)
        }
        
        # Handle user_id - create ObjectId if valid, or generate deterministic one for strings
        if user_id:
            try:
                user_object_id = ObjectId(user_id)
                query_doc["user_id"] = user_object_id
            except Exception as e:
                logger.info(f"Non-ObjectId user_id format detected: {user_id}, creating deterministic ObjectId")
                # For non-ObjectId user_ids (like "admin"), create a deterministic ObjectId
                # by using the first 24 hex characters of a hash of the string
                import hashlib
                hash_obj = hashlib.md5(user_id.encode())
                hex_hash = hash_obj.hexdigest()[:24]  # Use first 24 chars for ObjectId
                try:
                    user_object_id = ObjectId(hex_hash)
                    query_doc["user_id"] = user_object_id
                    logger.info(f"Created deterministic ObjectId for user_id: {user_id} -> {user_object_id}")
                except Exception as e2:
                    logger.error(f"Failed to create ObjectId from hash: {e2}")
                    # If we can't create a valid ObjectId, skip logging to avoid validation errors
                    return None
        
        result = await db.query_history.insert_one(query_doc)
        query_id = str(result.inserted_id)
        
        logger.info(f"Logged query {query_id} for user {user_id}")
        return query_id
    
    async def get_user_query_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get query history for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of queries to return
            
        Returns:
            List of query documents
        """
        db = get_mongo_db()
        
        # Convert user_id to ObjectId - use same logic as log_query for consistency
        try:
            user_object_id = ObjectId(user_id)
        except Exception as e:
            logger.info(f"Non-ObjectId user_id format detected: {user_id}, creating deterministic ObjectId for lookup")
            # For non-ObjectId user_ids, create a deterministic ObjectId using hash
            # This matches the logic in log_query, so we can find the same user's history
            try:
                import hashlib
                hash_obj = hashlib.md5(user_id.encode())
                hex_hash = hash_obj.hexdigest()[:24]  # Use first 24 chars for ObjectId
                user_object_id = ObjectId(hex_hash)
                logger.info(f"Created deterministic ObjectId for user_id lookup: {user_id} -> {user_object_id}")
            except Exception as e2:
                logger.error(f"Failed to create ObjectId from hash: {e2}")
                return []
        
        try:
            queries = await db.query_history.find(
                {"user_id": user_object_id}
            ).sort("query_timestamp", -1).limit(limit).to_list(limit)
        except Exception as e:
            logger.error(f"Error querying MongoDB for user history: {e}")
            return []
        
        # Convert ObjectIds to strings and format
        formatted_queries = []
        for query in queries:
            formatted_query = {
                "query_id": str(query["_id"]),
                "query_text": query.get("query_text", ""),
                "query_type": query.get("query_type"),
                "answer": query.get("rag_response"),
                "sources": query.get("sources_used", []),
                "query_timestamp": query.get("query_timestamp"),
                "satisfaction_rating": query.get("satisfaction_rating")
            }
            formatted_queries.append(formatted_query)
        
        return formatted_queries
    
    async def get_user_context(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, str]]:
        """
        Get recent query history for context in prompts
        
        Args:
            user_id: User ID
            limit: Number of recent queries to return
            
        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        history = await self.get_user_query_history(user_id, limit=limit)
        
        messages = []
        for query in reversed(history):  # Reverse to get chronological order
            if query.get("query_text"):
                messages.append({
                    "role": "user",
                    "content": query["query_text"]
                })
            if query.get("answer"):
                messages.append({
                    "role": "assistant",
                    "content": query["answer"]
                })
        
        return messages
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by username
        
        Args:
            username: Username
            
        Returns:
            User document or None
        """
        db = get_mongo_db()
        user = await db.user_profiles.find_one({"username": username})
        
        if user:
            user["user_id"] = str(user["_id"])
            del user["_id"]
            del user["password"]  # Don't return password
        
        return user
    
    async def get_insured_id_from_username(self, username: str) -> Optional[str]:
        """
        Get insured_id for a user by their username
        
        Args:
            username: Username to look up
            
        Returns:
            insured_id if found, None otherwise
        """
        user = await self.get_user_by_username(username)
        if user and "insured_id" in user:
            return user["insured_id"]
        return None
    
    async def get_policy_number_from_username(self, username: str) -> Optional[str]:
        """
        Get policy_number for a user by their username
        
        Args:
            username: Username to look up
            
        Returns:
            policy_number if found, None otherwise
        """
        user = await self.get_user_by_username(username)
        if user and "policy_number" in user:
            return user["policy_number"]
        return None
    
    async def get_account_info_from_username(self, username: str) -> Optional[Dict[str, str]]:
        """
        Get both insured_id and policy_number for a user by their username
        
        Args:
            username: Username to look up
            
        Returns:
            Dictionary with 'insured_id' and 'policy_number' if found, None otherwise
        """
        user = await self.get_user_by_username(username)
        if user and "insured_id" in user:
            return {
                "insured_id": user["insured_id"],
                "policy_number": user.get("policy_number")
            }
        return None
    
    async def get_user_by_policy_number(self, policy_number: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by policy_number
        
        Args:
            policy_number: Policy number to look up
            
        Returns:
            User document or None
        """
        db = get_mongo_db()
        user = await db.user_profiles.find_one({"policy_number": policy_number})
        
        if user:
            user["user_id"] = str(user["_id"])
            del user["_id"]
            del user["password"]  # Don't return password
        
        return user
    
    async def search_user_profiles(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search user profiles by username or email
        
        Args:
            query: Search query (username or email)
            limit: Maximum number of results
            
        Returns:
            List of user profiles (without passwords)
        """
        db = get_mongo_db()
        
        # Build search filter - search both username and email
        search_filter = {
            "$or": [
                {"username": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}}
            ]
        }
        
        try:
            users = await db.user_profiles.find(search_filter).limit(limit).to_list(limit)
            
            # Format results (remove password, add user_id)
            formatted_users = []
            for user in users:
                formatted_user = {
                    "user_id": str(user["_id"]),
                    "username": user.get("username", ""),
                    "email": user.get("email", ""),
                    "created_at": user.get("created_at"),
                    "updated_at": user.get("updated_at"),
                    "last_login": user.get("last_login")
                }
                formatted_users.append(formatted_user)
            
            return formatted_users
        except Exception as e:
            logger.error(f"Error searching user profiles: {e}")
            return []
    
    async def count_user_profiles(self) -> int:
        """
        Count total number of user profiles
        
        Returns:
            Count of user profiles
        """
        db = get_mongo_db()
        try:
            count = await db.user_profiles.count_documents({})
            return count
        except Exception as e:
            logger.error(f"Error counting user profiles: {e}")
            return 0

