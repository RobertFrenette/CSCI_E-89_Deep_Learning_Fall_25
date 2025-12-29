"""
SQL Query Handler Module
Handles natural language queries to the PostgreSQL database and formats responses.
Supports four main query types:
- Count insureds
- Count claims
- High-risk policies
- Insured information by ID
"""
import re
import logging
from typing import Optional
from app.services.postgres_service import PostgreSQLService
from app.routing.constants import (
    HIGH_RISK_SCORE_THRESHOLD,
    INSURED_ID_PATTERN,
    DEFAULT_SQL_UNAVAILABLE_MSG,
    DEFAULT_SQL_HELP_MSG,
    DEFAULT_NO_INSURED_ID_MSG
)

logger = logging.getLogger(__name__)


class SQLQueryHandler:
    """
    Handles SQL database queries and response formatting.
    
    Attributes:
        postgres_service: PostgreSQLService instance for database queries
    """
    
    def __init__(self, postgres_service: PostgreSQLService):
        """
        Initialize the SQL query handler.
        
        Args:
            postgres_service: PostgreSQLService instance for database queries
        """
        self.postgres_service = postgres_service
    
    def handle_query(self, question: str, insured_id: Optional[str] = None, policy_number: Optional[str] = None) -> str:
        """
        Handle a natural language question and return formatted response.
        
        Args:
            question: User's question
            insured_id: Optional insured_id to filter queries (for authenticated users)
                       If provided, queries will be filtered to this user's data only
            policy_number: Optional policy_number for direct policy queries (for authenticated users)
                          Takes precedence over insured_id for policy-specific queries
            
        Returns:
            Formatted response with database results
        """
        if not self.postgres_service:
            return DEFAULT_SQL_UNAVAILABLE_MSG
        
        question_lower = question.lower()
        
        # Try each query type in order
        if self._is_count_insureds_query(question_lower):
            return self._handle_count_insureds(insured_id)
        
        if self._is_count_claims_query(question_lower):
            return self._handle_count_claims(insured_id, policy_number)
        
        if self._is_count_policies_query(question_lower):
            return self._handle_count_policies(insured_id, policy_number)
        
        if self._is_high_risk_policies_query(question_lower):
            return self._handle_high_risk_policies(insured_id, policy_number)
        
        if self._is_insured_info_query(question_lower, question):
            # For insured info queries, if insured_id is provided, use it instead of extracting from query
            if insured_id:
                return self._handle_insured_info_by_id(insured_id)
            return self._handle_insured_info(question)
        
        # Default: help message
        return DEFAULT_SQL_HELP_MSG
    
    def _is_count_insureds_query(self, question_lower: str) -> bool:
        """Check if query is asking to count insureds"""
        return ('insured' in question_lower and 
                any(keyword in question_lower for keyword in ['how many', 'count', 'total']) and
                'information' not in question_lower and 
                'info' not in question_lower)
    
    def _handle_count_insureds(self, insured_id: Optional[str] = None) -> str:
        """Handle count insureds query"""
        try:
            # For admin users (insured_id is None), return total count
            # For authenticated users, this query doesn't make sense (they can't count all insureds)
            # So we'll still return total, but could filter in the future if needed
            count = self.postgres_service.count_insureds()
            return f"There are {count} insureds in the database."
        except Exception as e:
            logger.error(f"Error counting insureds: {e}", exc_info=True)
            return f"Error retrieving insured count: {str(e)}"
    
    def _is_count_claims_query(self, question_lower: str) -> bool:
        """Check if query is asking to count claims"""
        return ('claim' in question_lower and 
                any(keyword in question_lower for keyword in ['how many', 'count', 'total', 'filed']) and
                'polic' not in question_lower)  # Exclude if asking about policies
    
    def _handle_count_claims(self, insured_id: Optional[str] = None, policy_number: Optional[str] = None) -> str:
        """Handle count claims query"""
        try:
            # If policy_number is provided (authenticated user), count only their claims
            if policy_number:
                count = self.postgres_service.count_claims_by_policy(policy_number)
                return f"You have {count} claim(s) for policy {policy_number}."
            # If insured_id is provided but no policy_number, count all claims for this insured
            elif insured_id:
                count = self.postgres_service.count_claims_by_insured(insured_id)
                return f"You have {count} claim(s)."
            # Admin user - return total count
            else:
                count = self.postgres_service.count_claims()
                return f"{count} claims have been filed."
        except Exception as e:
            logger.error(f"Error counting claims: {e}", exc_info=True)
            return f"Error retrieving claims count: {str(e)}"
    
    def _is_count_policies_query(self, question_lower: str) -> bool:
        """Check if query is asking to count policies"""
        return ('polic' in question_lower and 
                any(keyword in question_lower for keyword in ['how many', 'count', 'total']) and
                'information' not in question_lower and 
                'info' not in question_lower and
                'high risk' not in question_lower)
    
    def _handle_count_policies(self, insured_id: Optional[str] = None, policy_number: Optional[str] = None) -> str:
        """Handle count policies query"""
        try:
            # If policy_number is provided (authenticated user asking about their policy)
            if policy_number:
                # They're asking about their specific policy - just confirm it exists
                policy = self.postgres_service.get_policy_by_number(policy_number)
                if policy:
                    return f"You have 1 policy: {policy_number}."
                else:
                    return f"Policy {policy_number} not found."
            # If insured_id is provided, count policies for this insured
            elif insured_id:
                count = self.postgres_service.count_policies_by_insured(insured_id)
                return f"You have {count} policy/policies."
            # Admin user - return total count
            else:
                count = self.postgres_service.count_policies()
                return f"There are {count} policies in the database."
        except Exception as e:
            logger.error(f"Error counting policies: {e}", exc_info=True)
            return f"Error retrieving policies count: {str(e)}"
    
    def _is_high_risk_policies_query(self, question_lower: str) -> bool:
        """Check if query is asking for high-risk policies"""
        return 'high risk' in question_lower and 'polic' in question_lower
    
    def _handle_high_risk_policies(self, insured_id: Optional[str] = None, policy_number: Optional[str] = None) -> str:
        """Handle high-risk policies query"""
        try:
            # For authenticated users, only show their own high-risk policies
            if policy_number or insured_id:
                if policy_number:
                    # Get the specific policy and check if it's high-risk
                    policy = self.postgres_service.get_policy_by_number(policy_number)
                    if not policy:
                        return f"Policy {policy_number} not found."
                    # Get risk score for this policy
                    risk_info = self.postgres_service.get_policy_risk_info(policy_number)
                    if risk_info and risk_info.get('risk_score_internal', 0) >= HIGH_RISK_SCORE_THRESHOLD:
                        return f"Your policy {policy_number} has a high risk score of {risk_info.get('risk_score_internal')}."
                    else:
                        return f"Your policy {policy_number} is not classified as high-risk."
                else:
                    # Get high-risk policies for this insured
                    policies = self.postgres_service.get_high_risk_policies_by_insured(insured_id, HIGH_RISK_SCORE_THRESHOLD)
                    if not policies:
                        return f"You have no high-risk policies (risk score >= {HIGH_RISK_SCORE_THRESHOLD})."
                    response = f"You have {len(policies)} high-risk policy/policies:\n\n"
                    for i, policy in enumerate(policies, 1):
                        response += f"{i}. Policy {policy.get('policy_number', 'N/A')}\n"
                        response += f"   Risk Score: {policy.get('risk_score_internal', 'N/A')}\n"
                        response += f"   Status: {policy.get('policy_status', 'N/A')}\n\n"
                    return response
            else:
                # Admin user - return all high-risk policies
                policies = self.postgres_service.get_high_risk_policies(HIGH_RISK_SCORE_THRESHOLD)
                if not policies:
                    return f"No high-risk policies found (risk score >= {HIGH_RISK_SCORE_THRESHOLD})."
                
                response = f"Found {len(policies)} high-risk policies (risk score >= {HIGH_RISK_SCORE_THRESHOLD}):\n\n"
                for i, policy in enumerate(policies, 1):
                    response += f"{i}. Policy {policy.get('policy_number', 'N/A')}\n"
                    response += f"   Insured: {policy.get('first_name', '')} {policy.get('last_name', '')} ({policy.get('company_name', 'N/A')})\n"
                    response += f"   Type: {policy.get('policy_type', 'N/A')}\n"
                    response += f"   Status: {policy.get('policy_status', 'N/A')}\n"
                    response += f"   Risk Score: {policy.get('risk_score_internal', 'N/A')}\n"
                    response += f"   AI System: {policy.get('ai_system_type', 'N/A')}\n"
                    if policy.get('annual_premium'):
                        response += f"   Annual Premium: ${float(policy.get('annual_premium', 0)):,.2f}\n"
                    response += "\n"
                
                return response
        except Exception as e:
            logger.error(f"Error getting high-risk policies: {e}", exc_info=True)
            return f"Error retrieving high-risk policies: {str(e)}"
    
    def _is_insured_info_query(self, question_lower: str, question: str) -> bool:
        """Check if query is asking for insured information"""
        # Exclude common words that might match the pattern
        excluded_words = {'DATABASE', 'INFORMATION', 'POLICIES', 'CLAIMS', 'INSUREDS', 'POLICY', 'CLAIM'}
        
        matches = re.findall(INSURED_ID_PATTERN, question.upper())
        # Filter out excluded words
        valid_matches = [m for m in matches if m not in excluded_words]
        
        # Only treat as insured info query if we have a valid ID match
        # OR if explicitly asking for information about an insured (with context)
        return bool(valid_matches) or (
            'information' in question_lower and 
            'insured' in question_lower and
            'how many' not in question_lower and
            'count' not in question_lower and
            'total' not in question_lower
        )
    
    def _handle_insured_info_by_id(self, insured_id: str) -> str:
        """Handle insured information query using provided insured_id"""
        try:
            info = self.postgres_service.get_insured_info(insured_id)
            if not info:
                return f"Insured ID '{insured_id}' not found in the database."
            
            return self._format_insured_info(insured_id, info)
        except Exception as e:
            logger.error(f"Error getting insured information: {e}", exc_info=True)
            return f"Error retrieving information for insured {insured_id}: {str(e)}"
    
    def _handle_insured_info(self, question: str) -> str:
        """Handle insured information query"""
        # Extract insured ID
        insured_id = self._extract_insured_id(question)
        
        if not insured_id:
            return DEFAULT_NO_INSURED_ID_MSG
        
        try:
            info = self.postgres_service.get_insured_info(insured_id)
            if not info:
                return f"Insured ID '{insured_id}' not found in the database."
            
            return self._format_insured_info(insured_id, info)
        except Exception as e:
            logger.error(f"Error getting insured information: {e}", exc_info=True)
            return f"Error retrieving information for insured {insured_id}: {str(e)}"
    
    def _extract_insured_id(self, question: str) -> Optional[str]:
        """Extract insured ID from question"""
        # Exclude common words that might match the pattern
        excluded_words = {'DATABASE', 'INFORMATION', 'POLICIES', 'CLAIMS', 'INSUREDS', 'POLICY', 'CLAIM'}
        
        # Try pattern matching first
        matches = re.findall(INSURED_ID_PATTERN, question.upper())
        # Filter out excluded words
        valid_matches = [m for m in matches if m not in excluded_words]
        if valid_matches:
            return valid_matches[0]
        
        # Try finding ID after "insured" keyword (but not if it's a common word)
        words = question.upper().split()
        if 'INSURED' in words:
            idx = words.index('INSURED')
            if idx + 1 < len(words):
                potential_id = words[idx + 1]
                if potential_id not in excluded_words:
                    return potential_id
        
        return None
    
    def _format_insured_info(self, insured_id: str, info: dict) -> str:
        """Format insured information response"""
        response = f"Information for Insured {insured_id}:\n\n"
        
        # Insured basic information
        insured = info['insured']
        response += "=== Insured Information ===\n"
        response += f"Name: {insured.get('first_name', '')} {insured.get('last_name', '')}\n"
        response += f"Company: {insured.get('company_name', 'N/A')}\n"
        response += f"Industry: {insured.get('industry', 'N/A')}\n"
        response += f"Email: {insured.get('email_address', 'N/A')}\n"
        response += f"Phone: {insured.get('phone_number', 'N/A')}\n"
        if insured.get('address_line1'):
            response += f"Address: {insured.get('address_line1', '')}, {insured.get('city', '')}, {insured.get('state', '')} {insured.get('postal_code', '')}\n"
        response += "\n"
        
        # Policies
        policies = info['policies']
        if policies:
            response += f"=== Policies ({len(policies)}) ===\n"
            for i, policy in enumerate(policies, 1):
                response += f"\n{i}. Policy {policy.get('policy_number', 'N/A')}\n"
                response += f"   Type: {policy.get('policy_type', 'N/A')}\n"
                response += f"   Status: {policy.get('policy_status', 'N/A')}\n"
                if policy.get('effective_date'):
                    response += f"   Effective: {policy.get('effective_date', 'N/A')}\n"
                if policy.get('expiration_date'):
                    response += f"   Expiration: {policy.get('expiration_date', 'N/A')}\n"
                if policy.get('annual_premium'):
                    response += f"   Annual Premium: ${float(policy.get('annual_premium', 0)):,.2f}\n"
                if policy.get('risk_score_internal'):
                    response += f"   Risk Score: {policy.get('risk_score_internal', 'N/A')}\n"
                if policy.get('ai_system_type'):
                    response += f"   AI System: {policy.get('ai_system_type', 'N/A')}\n"
                if policy.get('coverage_limit'):
                    response += f"   Coverage Limit: ${float(policy.get('coverage_limit', 0)):,.0f}\n"
        else:
            response += "=== Policies ===\nNo policies found.\n\n"
        
        # Claims
        claims = info['claims']
        if claims:
            response += f"\n=== Claims ({len(claims)}) ===\n"
            for i, claim in enumerate(claims, 1):
                response += f"\n{i}. Claim {claim.get('claim_id', 'N/A')}\n"
                response += f"   Date: {claim.get('claim_date', 'N/A')}\n"
                response += f"   Type: {claim.get('claim_type', 'N/A')}\n"
                response += f"   Status: {claim.get('claim_status', 'N/A')}\n"
                if claim.get('claim_amount'):
                    response += f"   Amount: ${float(claim.get('claim_amount', 0)):,.2f}\n"
                if claim.get('amount_paid'):
                    response += f"   Paid: ${float(claim.get('amount_paid', 0)):,.2f}\n"
        else:
            response += "\n=== Claims ===\nNo claims found.\n"
        
        return response

