"""
SQL Query Handler Module

Handles natural language queries to the SQL database and formats responses.
Supports four main query types:
1. Count insureds
2. Count claims
3. High-risk policies
4. Insured information by ID
"""

import re
import logging
from typing import Optional
from agent.routing.constants import (
    HIGH_RISK_SCORE_THRESHOLD,
    INSURED_ID_PATTERN,
    DEFAULT_SQL_UNAVAILABLE_MSG,
    DEFAULT_SQL_HELP_MSG,
    DEFAULT_NO_INSURED_ID_MSG
)

logger = logging.getLogger(__name__)


class SQLQueryHandler:
    """Handles SQL database queries and response formatting."""
    
    def __init__(self, sql_processor):
        """
        Initialize the SQL query handler.
        
        Args:
            sql_processor: SQLProcessor instance for database queries
        """
        self.sql_processor = sql_processor
    
    def handle_query(self, question: str) -> str:
        """
        Handle a natural language question and return formatted response.
        
        Args:
            question: User's question
            
        Returns:
            Formatted response with database results
        """
        if not self.sql_processor:
            return DEFAULT_SQL_UNAVAILABLE_MSG
        
        question_lower = question.lower()
        
        # Try each query type in order
        if self._is_count_insureds_query(question_lower):
            return self._handle_count_insureds()
        
        if self._is_count_claims_query(question_lower):
            return self._handle_count_claims()
        
        if self._is_high_risk_policies_query(question_lower):
            return self._handle_high_risk_policies()
        
        if self._is_insured_info_query(question_lower, question):
            return self._handle_insured_info(question)
        
        # Default: help message
        return DEFAULT_SQL_HELP_MSG
    
    def _is_count_insureds_query(self, question_lower: str) -> bool:
        """Check if query is asking to count insureds."""
        return ('insured' in question_lower and 
                any(keyword in question_lower for keyword in ['how many', 'count', 'total']) and
                'information' not in question_lower and 
                'info' not in question_lower)
    
    def _handle_count_insureds(self) -> str:
        """Handle count insureds query."""
        try:
            count = self.sql_processor.count_insureds()
            return f"There are {count} insureds in the database."
        except Exception as e:
            logger.error(f"Error counting insureds: {e}", exc_info=True)
            return f"Error retrieving insured count: {str(e)}"
    
    def _is_count_claims_query(self, question_lower: str) -> bool:
        """Check if query is asking to count claims."""
        return ('claim' in question_lower and 
                any(keyword in question_lower for keyword in ['how many', 'count', 'total', 'filed']))
    
    def _handle_count_claims(self) -> str:
        """Handle count claims query."""
        try:
            count = self.sql_processor.count_claims()
            return f"{count} claims have been filed."
        except Exception as e:
            logger.error(f"Error counting claims: {e}", exc_info=True)
            return f"Error retrieving claims count: {str(e)}"
    
    def _is_high_risk_policies_query(self, question_lower: str) -> bool:
        """Check if query is asking for high-risk policies."""
        return 'high risk' in question_lower and 'polic' in question_lower
    
    def _handle_high_risk_policies(self) -> str:
        """Handle high-risk policies query."""
        try:
            policies = self.sql_processor.get_high_risk_policies(HIGH_RISK_SCORE_THRESHOLD)
            if not policies:
                return f"No high-risk policies found (risk score >= {HIGH_RISK_SCORE_THRESHOLD})."
            
            response = f"Found {len(policies)} high-risk policies (risk score >= {HIGH_RISK_SCORE_THRESHOLD}):\n\n"
            for i, policy in enumerate(policies, 1):
                response += f"{i}. Policy {policy['Policy_Number']}\n"
                response += f"   Insured: {policy.get('First_Name', '')} {policy.get('Last_Name', '')} ({policy.get('Company_Name', 'N/A')})\n"
                response += f"   Type: {policy.get('Policy_Type', 'N/A')}\n"
                response += f"   Status: {policy.get('Policy_Status', 'N/A')}\n"
                response += f"   Risk Score: {policy.get('Risk_Score_Internal', 'N/A')}\n"
                response += f"   AI System: {policy.get('AI_System_Type', 'N/A')}\n"
                if policy.get('Annual_Premium'):
                    response += f"   Annual Premium: ${policy.get('Annual_Premium', 0):,.2f}\n"
                response += "\n"
            
            return response
        except Exception as e:
            logger.error(f"Error getting high-risk policies: {e}", exc_info=True)
            return f"Error retrieving high-risk policies: {str(e)}"
    
    def _is_insured_info_query(self, question_lower: str, question: str) -> bool:
        """Check if query is asking for insured information."""
        matches = re.findall(INSURED_ID_PATTERN, question.upper())
        return bool(matches) or ('information' in question_lower and 'insured' in question_lower)
    
    def _handle_insured_info(self, question: str) -> str:
        """Handle insured information query."""
        # Extract insured ID
        insured_id = self._extract_insured_id(question)
        
        if not insured_id:
            return DEFAULT_NO_INSURED_ID_MSG
        
        try:
            info = self.sql_processor.get_insured_info(insured_id)
            if not info:
                return f"Insured ID '{insured_id}' not found in the database."
            
            return self._format_insured_info(insured_id, info)
        except Exception as e:
            logger.error(f"Error getting insured information: {e}", exc_info=True)
            return f"Error retrieving information for insured {insured_id}: {str(e)}"
    
    def _extract_insured_id(self, question: str) -> Optional[str]:
        """Extract insured ID from question."""
        # Try pattern matching first
        matches = re.findall(INSURED_ID_PATTERN, question.upper())
        if matches:
            return matches[0]
        
        # Try finding ID after "insured" keyword
        words = question.upper().split()
        if 'INSURED' in words:
            idx = words.index('INSURED')
            if idx + 1 < len(words):
                return words[idx + 1]
        
        return None
    
    def _format_insured_info(self, insured_id: str, info: dict) -> str:
        """Format insured information response."""
        response = f"Information for Insured {insured_id}:\n\n"
        
        # Insured basic information
        insured = info['insured']
        response += "=== Insured Information ===\n"
        response += f"Name: {insured.get('First_Name', '')} {insured.get('Last_Name', '')}\n"
        response += f"Company: {insured.get('Company_Name', 'N/A')}\n"
        response += f"Industry: {insured.get('Industry', 'N/A')}\n"
        response += f"Email: {insured.get('Email_Address', 'N/A')}\n"
        response += f"Phone: {insured.get('Phone_Number', 'N/A')}\n"
        response += f"Address: {insured.get('Address_Line1', '')}, {insured.get('City', '')}, {insured.get('State', '')} {insured.get('Postal_Code', '')}\n"
        response += "\n"
        
        # Policies
        policies = info['policies']
        if policies:
            response += f"=== Policies ({len(policies)}) ===\n"
            for i, policy in enumerate(policies, 1):
                response += f"\n{i}. Policy {policy.get('Policy_Number', 'N/A')}\n"
                response += f"   Type: {policy.get('Policy_Type', 'N/A')}\n"
                response += f"   Status: {policy.get('Policy_Status', 'N/A')}\n"
                if policy.get('Effective_Date'):
                    response += f"   Effective: {policy.get('Effective_Date', 'N/A')}\n"
                if policy.get('Expiration_Date'):
                    response += f"   Expiration: {policy.get('Expiration_Date', 'N/A')}\n"
                if policy.get('Annual_Premium'):
                    response += f"   Annual Premium: ${policy.get('Annual_Premium', 0):,.2f}\n"
                if policy.get('Risk_Score_Internal'):
                    response += f"   Risk Score: {policy.get('Risk_Score_Internal', 'N/A')}\n"
                if policy.get('AI_System_Type'):
                    response += f"   AI System: {policy.get('AI_System_Type', 'N/A')}\n"
                if policy.get('Coverage_Limit'):
                    response += f"   Coverage Limit: ${policy.get('Coverage_Limit', 0):,}\n"
        else:
            response += "=== Policies ===\nNo policies found.\n\n"
        
        # Claims
        claims = info['claims']
        if claims:
            response += f"\n=== Claims ({len(claims)}) ===\n"
            for i, claim in enumerate(claims, 1):
                response += f"\n{i}. Claim {claim.get('Claim_ID', 'N/A')}\n"
                response += f"   Date: {claim.get('Claim_Date', 'N/A')}\n"
                response += f"   Type: {claim.get('Claim_Type', 'N/A')}\n"
                response += f"   Status: {claim.get('Claim_Status', 'N/A')}\n"
                if claim.get('Claim_Amount'):
                    response += f"   Amount: ${claim.get('Claim_Amount', 0):,.2f}\n"
                if claim.get('Amount_Paid'):
                    response += f"   Paid: ${claim.get('Amount_Paid', 0):,.2f}\n"
        else:
            response += "\n=== Claims ===\nNo claims found.\n"
        
        return response

