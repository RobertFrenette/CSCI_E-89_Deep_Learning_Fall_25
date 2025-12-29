"""
PostgreSQL service for structured data queries
"""
from typing import Optional, List, Dict, Any
from functools import lru_cache
from app.database.postgres import get_postgres_cursor
import logging

logger = logging.getLogger(__name__)


class PostgreSQLService:
    """Service for PostgreSQL operations related to structured data queries"""
    
    @lru_cache(maxsize=128)
    def count_insureds(self) -> int:
        """
        Count total number of insureds in the database
        Cached for 5 minutes to improve performance
        
        Returns:
            Count of insureds
        """
        try:
            with get_postgres_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM insureds")
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Error counting insureds: {e}")
            raise
    
    @lru_cache(maxsize=128)
    def count_claims(self) -> int:
        """
        Count total number of claims in the database
        Cached for 5 minutes to improve performance
        
        Returns:
            Count of claims
        """
        try:
            with get_postgres_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM claims_history")
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Error counting claims: {e}")
            raise
    
    @lru_cache(maxsize=128)
    def count_policies(self) -> int:
        """
        Count total number of policies in the database
        Cached for 5 minutes to improve performance
        
        Returns:
            Count of policies
        """
        try:
            with get_postgres_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM policies")
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Error counting policies: {e}")
            raise
    
    def get_high_risk_policies(self, min_risk_score: int = 90) -> List[Dict[str, Any]]:
        """
        Get all high-risk policies with insured and policy information
        
        Args:
            min_risk_score: Minimum risk score threshold (default: 90)
            
        Returns:
            List of dictionaries containing policy, insured, and risk information
        """
        try:
            with get_postgres_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        i.insured_id,
                        i.first_name,
                        i.last_name,
                        i.company_name,
                        i.industry,
                        p.policy_number,
                        p.policy_type,
                        p.policy_status,
                        p.annual_premium,
                        a.risk_score_internal,
                        a.ai_system_type,
                        a.has_high_risk_use_cases
                    FROM insureds i
                    JOIN policies p ON i.insured_id = p.insured_id
                    JOIN ai_risk_profile a ON p.policy_number = a.policy_number
                    WHERE a.risk_score_internal >= %s
                    ORDER BY a.risk_score_internal DESC
                """, (min_risk_score,))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting high-risk policies: {e}")
            raise
    
    def get_insured_info(self, insured_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive information for a specific insured by ID
        
        Args:
            insured_id: The insured's unique identifier
            
        Returns:
            Dictionary containing insured information, policies, and claims, or None if not found
        """
        try:
            with get_postgres_cursor() as cursor:
                # Get insured basic information
                cursor.execute("SELECT * FROM insureds WHERE insured_id = %s", (insured_id,))
                insured_row = cursor.fetchone()
                
                if not insured_row:
                    logger.debug(f"Insured not found: {insured_id}")
                    return None
                
                insured_info = dict(insured_row)
                
                # Get policies for this insured
                cursor.execute("""
                    SELECT 
                        p.*,
                        c.coverage_limit,
                        c.coverage_tier,
                        a.risk_score_internal,
                        a.ai_system_type,
                        a.has_high_risk_use_cases,
                        a.incident_history_count
                    FROM policies p
                    LEFT JOIN coverage_details c ON p.policy_number = c.policy_number
                    LEFT JOIN ai_risk_profile a ON p.policy_number = a.policy_number
                    WHERE p.insured_id = %s
                    ORDER BY p.effective_date DESC
                """, (insured_id,))
                
                policies = [dict(row) for row in cursor.fetchall()]
                
                # Get claims for this insured
                cursor.execute("""
                    SELECT * FROM claims_history 
                    WHERE insured_id = %s
                    ORDER BY claim_date DESC
                """, (insured_id,))
                
                claims = [dict(row) for row in cursor.fetchall()]
                
                # Compile all information
                result = {
                    'insured': insured_info,
                    'policies': policies,
                    'claims': claims
                }
                
                logger.debug(f"Retrieved information for insured {insured_id}: {len(policies)} policies, {len(claims)} claims")
                return result
        except Exception as e:
            logger.error(f"Error getting insured information: {e}")
            raise
    
    def count_claims_by_policy(self, policy_number: str) -> int:
        """
        Count claims for a specific policy
        
        Args:
            policy_number: Policy number
            
        Returns:
            Count of claims for this policy
        """
        try:
            with get_postgres_cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM claims_history 
                    WHERE policy_number = %s
                """, (policy_number,))
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Error counting claims by policy: {e}")
            raise
    
    def count_claims_by_insured(self, insured_id: str) -> int:
        """
        Count claims for a specific insured
        
        Args:
            insured_id: Insured ID
            
        Returns:
            Count of claims for this insured
        """
        try:
            with get_postgres_cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM claims_history 
                    WHERE insured_id = %s
                """, (insured_id,))
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Error counting claims by insured: {e}")
            raise
    
    def count_policies_by_insured(self, insured_id: str) -> int:
        """
        Count policies for a specific insured
        
        Args:
            insured_id: Insured ID
            
        Returns:
            Count of policies for this insured
        """
        try:
            with get_postgres_cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM policies 
                    WHERE insured_id = %s
                """, (insured_id,))
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Error counting policies by insured: {e}")
            raise
    
    def get_policy_by_number(self, policy_number: str) -> Optional[Dict[str, Any]]:
        """
        Get policy information by policy number
        
        Args:
            policy_number: Policy number
            
        Returns:
            Policy dictionary or None if not found
        """
        try:
            with get_postgres_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM policies 
                    WHERE policy_number = %s
                """, (policy_number,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting policy by number: {e}")
            raise
    
    def get_policy_risk_info(self, policy_number: str) -> Optional[Dict[str, Any]]:
        """
        Get risk information for a specific policy
        
        Args:
            policy_number: Policy number
            
        Returns:
            Risk information dictionary or None if not found
        """
        try:
            with get_postgres_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        risk_score_internal,
                        ai_system_type,
                        has_high_risk_use_cases,
                        incident_history_count
                    FROM ai_risk_profile 
                    WHERE policy_number = %s
                """, (policy_number,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting policy risk info: {e}")
            raise
    
    def get_high_risk_policies_by_insured(self, insured_id: str, min_risk_score: int = 90) -> List[Dict[str, Any]]:
        """
        Get high-risk policies for a specific insured
        
        Args:
            insured_id: Insured ID
            min_risk_score: Minimum risk score threshold (default: 90)
            
        Returns:
            List of high-risk policy dictionaries
        """
        try:
            with get_postgres_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        p.policy_number,
                        p.policy_type,
                        p.policy_status,
                        a.risk_score_internal
                    FROM policies p
                    JOIN ai_risk_profile a ON p.policy_number = a.policy_number
                    WHERE p.insured_id = %s AND a.risk_score_internal >= %s
                    ORDER BY a.risk_score_internal DESC
                """, (insured_id, min_risk_score))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting high-risk policies by insured: {e}")
            raise
    
    def execute_custom_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom SQL query (for advanced use cases)
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            List of result dictionaries
        """
        try:
            with get_postgres_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error executing custom query: {e}")
            raise

