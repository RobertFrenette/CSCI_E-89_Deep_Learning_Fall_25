#!/usr/bin/env python3
"""
Database connection test script
Verifies connectivity to Postgres database
"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Load environment variables from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'insurance_db'),
    'user': os.getenv('POSTGRES_USER', 'insure_admin'),
    'password': os.getenv('POSTGRES_PASSWORD', 'insure_secure_pass_2024')
}


def test_connection():
    """Test database connection"""
    print("\n" + "="*60)
    print("Database Connection Test")
    print("="*60)
    print(f"Host     : {DB_CONFIG['host']}")
    print(f"Port     : {DB_CONFIG['port']}")
    print(f"Database : {DB_CONFIG['database']}")
    print(f"User     : {DB_CONFIG['user']}")
    print("="*60 + "\n")
    
    try:
        # Attempt connection
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Successfully connected to database")
        
        # Get database version
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ PostgreSQL version: {version.split(',')[0]}")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("\n⚠ No tables found (schema may not be initialized)")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Connection test passed!\n")
        return True
        
    except psycopg2.Error as e:
        print(f"\n✗ Connection failed: {e}\n")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
