"""
SQL Processor Module
Instantiates a SQLite database connection and uses it to handle queries.
Used in the QueryService to handle SQL queries.

Handles SQLite database queries for structured insured data.
Domain processor for database operations.

Attributes:
    db_path: Path to the SQLite database file
    _local: Thread-local storage for connections

Methods:
    _get_connection: Get or create a connection for the current thread
    connect: Establish connection to the database for the current thread
    disconnect: Close database connection for the current thread
"""

import sqlite3
import threading
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SQLProcessor:
    """
    Class for querying the insureds SQLite database (thread-safe).

    Attributes:
        db_path: Path to the SQLite database file
        _local: Thread-local storage for connections

    Methods:
        _get_connection: Get or create a connection for the current thread
        connect: Establish connection to the database for the current thread
        disconnect: Close database connection for the current thread
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the SQL processor.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._local = threading.local()  # Thread-local storage for connections
        
    def _get_connection(self):
        """
        Get or create a connection for the current thread.
        
        Uses thread-local storage to ensure each thread has its own database connection.
        
        Returns:
            sqlite3.Connection: Database connection for current thread
            
        Raises:
            FileNotFoundError: If database file doesn't exist
            sqlite3.Error: If connection fails
        """
        try:
            if not hasattr(self._local, 'connection') or self._local.connection is None:
                if not Path(self.db_path).exists():
                    logger.error(f"Database file not found: {self.db_path}")
                    raise FileNotFoundError(f"Database not found at: {self.db_path}")
                
                self._local.connection = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False
                )
                self._local.connection.row_factory = sqlite3.Row
                logger.debug(f"Database connection established for thread {threading.current_thread().name}")
            
            return self._local.connection
        except sqlite3.Error as e:
            logger.error(f"SQLite connection error: {e}")
            raise
    
    def connect(self):
        """
        Establish connection to the database for the current thread.
        
        Creates a new database connection if one doesn't exist for the current thread.
        
        Returns:
            None
            
        Raises:
            Exception: If connection fails
        """
        try:
            self._get_connection()
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
        
    def disconnect(self):
        """
        Close database connection for the current thread.
        
        Closes the thread-local database connection if it exists.
        
        Returns:
            None
        """
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None

    def count_insureds(self) -> int:
        """
        Return the number of insureds in the database.
        
        Executes SQL COUNT query on insureds table.
        
        Returns:
            int: Count of insureds in the database
            
        Raises:
            sqlite3.Error: If query execution fails
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM insureds")
            count = cursor.fetchone()[0]
            logger.debug(f"Counted {count} insureds")
            return count
        except sqlite3.Error as e:
            logger.error(f"Error counting insureds: {e}")
            raise

    def count_claims(self) -> int:
        """
        Return the number of claims filed in the database.
        
        Executes SQL COUNT query on claims_history table.
        
        Returns:
            int: Count of claims in the database
            
        Raises:
            sqlite3.Error: If query execution fails
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM claims_history")
            count = cursor.fetchone()[0]
            logger.debug(f"Counted {count} claims")
            return count
        except sqlite3.Error as e:
            logger.error(f"Error counting claims: {e}")
            raise

    def get_high_risk_policies(self, min_risk_score: int = 90) -> List[Dict[str, Any]]:
        """
        Get all high-risk policies with insured and policy information.
        
        Args:
            min_risk_score: Minimum risk score threshold (default: 90)
            
        Returns:
            List of dictionaries containing policy, insured, and risk information
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                SELECT 
                    i.Insured_ID,
                    i.First_Name,
                    i.Last_Name,
                    i.Company_Name,
                    i.Industry,
                    p.Policy_Number,
                    p.Policy_Type,
                    p.Policy_Status,
                    p.Annual_Premium,
                    a.Risk_Score_Internal,
                    a.AI_System_Type,
                    a.Has_High_Risk_Use_Cases
                FROM insureds i
                JOIN policies p ON i.Insured_ID = p.Insured_ID
                JOIN ai_risk_profile a ON p.Policy_Number = a.Policy_Number
                WHERE a.Risk_Score_Internal >= ?
                ORDER BY a.Risk_Score_Internal DESC
            """, (min_risk_score,))
            
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            logger.debug(f"Found {len(results)} high-risk policies (risk score >= {min_risk_score})")
            return results
        except sqlite3.Error as e:
            logger.error(f"Error getting high-risk policies: {e}")
            raise

    def get_insured_info(self, insured_id: str) -> Dict[str, Any]:
        """
        Get comprehensive information for a specific insured by ID.
        
        Args:
            insured_id: The insured's unique identifier
            
        Returns:
            Dictionary containing insured information, policies, and claims
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            # Get insured basic information
            cursor.execute("SELECT * FROM insureds WHERE Insured_ID = ?", (insured_id,))
            insured_row = cursor.fetchone()
            
            if not insured_row:
                logger.debug(f"Insured not found: {insured_id}")
                return None
            
            # Convert insured row to dictionary
            insured_columns = [description[0] for description in cursor.description]
            insured_info = dict(zip(insured_columns, insured_row))
            
            # Get policies for this insured
            cursor.execute("""
                SELECT 
                    p.*,
                    c.Coverage_Limit,
                    c.Coverage_Tier,
                    a.Risk_Score_Internal,
                    a.AI_System_Type,
                    a.Has_High_Risk_Use_Cases,
                    a.Incident_History_Count
                FROM policies p
                LEFT JOIN coverage_details c ON p.Policy_Number = c.Policy_Number
                LEFT JOIN ai_risk_profile a ON p.Policy_Number = a.Policy_Number
                WHERE p.Insured_ID = ?
                ORDER BY p.Effective_Date DESC
            """, (insured_id,))
            
            policy_columns = [description[0] for description in cursor.description]
            policies = []
            for row in cursor.fetchall():
                policies.append(dict(zip(policy_columns, row)))
            
            # Get claims for this insured
            cursor.execute("""
                SELECT * FROM claims_history 
                WHERE Insured_ID = ?
                ORDER BY Claim_Date DESC
            """, (insured_id,))
            
            claim_columns = [description[0] for description in cursor.description]
            claims = []
            for row in cursor.fetchall():
                claims.append(dict(zip(claim_columns, row)))
            
            # Compile all information
            result = {
                'insured': insured_info,
                'policies': policies,
                'claims': claims
            }
            
            logger.debug(f"Retrieved information for insured {insured_id}: {len(policies)} policies, {len(claims)} claims")
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting insured information: {e}")
            raise
    
    def __enter__(self):
        """
        Context manager entry.
        
        Establishes database connection when entering 'with' block.
        
        Returns:
            SQLProcessor: Self instance
        """
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.
        
        Closes database connection when exiting 'with' block.
        
        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
            
        Returns:
            None
        """
        self.disconnect()
