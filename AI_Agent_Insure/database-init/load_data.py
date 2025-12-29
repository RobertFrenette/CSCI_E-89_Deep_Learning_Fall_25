#!/usr/bin/env python3
"""
Data loading script for AI Insurance Platform
Loads CSV files into Postgres database with proper relationship handling
"""

import os
import sys
import csv
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from pathlib import Path
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
    'password': os.getenv('POSTGRES_PASSWORD', 'insure_secure_pass_2025')
}

# Data directory
DATA_DIR = Path(__file__).parent.parent / 'data' / 'insured_data'


def get_db_connection():
    """Create and return database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"✓ Connected to database: {DB_CONFIG['database']}")
        return conn
    except psycopg2.Error as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)


def parse_boolean(value):
    """Convert string to boolean"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('yes', 'true', '1', 'y')
    return False


def parse_decimal(value):
    """Convert string to decimal, handle empty values"""
    if not value or value.strip() == '':
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_integer(value):
    """Convert string to integer, handle empty values"""
    if not value or value.strip() == '':
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_date(value):
    """Convert string to date, handle empty values"""
    if not value or value.strip() == '':
        return None
    try:
        return datetime.strptime(value.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def clean_value(value):
    """Clean CSV value - handle empty strings and N/A"""
    if not value or value.strip() == '' or value.strip().upper() == 'N/A':
        return None
    return value.strip()


def load_insureds(conn):
    """Load insureds data from CSV"""
    csv_file = DATA_DIR / 'insureds.csv'
    print(f"\nLoading insureds from {csv_file}...")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = []
        
        for row in reader:
            record = (
                clean_value(row['Insured_ID']),
                clean_value(row['First_Name']),
                clean_value(row['Last_Name']),
                parse_date(row['Date_of_Birth']),
                clean_value(row['Phone_Number']),
                clean_value(row['Email_Address']),
                clean_value(row['Address_Line1']),
                clean_value(row['Address_Line2']),
                clean_value(row['City']),
                clean_value(row['State']),
                clean_value(row['Postal_Code']),
                clean_value(row['Country']) or 'USA',
                clean_value(row['Company_Name']),
                clean_value(row['Industry']),
                clean_value(row['Contact_Person'])
            )
            records.append(record)
    
    query = """
        INSERT INTO insureds (
            insured_id, first_name, last_name, date_of_birth, phone_number,
            email_address, address_line1, address_line2, city, state,
            postal_code, country, company_name, industry, contact_person
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (insured_id) DO NOTHING
    """
    
    cursor = conn.cursor()
    execute_batch(cursor, query, records)
    conn.commit()
    print(f"✓ Loaded {len(records)} insureds")
    cursor.close()


def load_policies(conn):
    """Load policies data from CSV"""
    csv_file = DATA_DIR / 'policies.csv'
    print(f"\nLoading policies from {csv_file}...")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = []
        
        for row in reader:
            record = (
                clean_value(row['Policy_Number']),
                clean_value(row['Insured_ID']),
                clean_value(row['Policy_Type']),
                parse_date(row['Effective_Date']),
                parse_date(row['Expiration_Date']),
                clean_value(row['Policy_Status']) or 'Active',
                clean_value(row['Payment_Status']) or 'Pending',
                parse_decimal(row['Annual_Premium']),
                parse_decimal(row['Monthly_Premium']),
                clean_value(row['Payment_Method']),
                clean_value(row['Broker']),
                clean_value(row['Discounts_Applied'])
            )
            records.append(record)
    
    query = """
        INSERT INTO policies (
            policy_number, insured_id, policy_type, effective_date, expiration_date,
            policy_status, payment_status, annual_premium, monthly_premium,
            payment_method, broker, discounts_applied
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (policy_number) DO NOTHING
    """
    
    cursor = conn.cursor()
    execute_batch(cursor, query, records)
    conn.commit()
    print(f"✓ Loaded {len(records)} policies")
    cursor.close()


def load_coverage_details(conn):
    """Load coverage details data from CSV"""
    csv_file = DATA_DIR / 'coverage_details.csv'
    print(f"\nLoading coverage details from {csv_file}...")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = []
        
        for row in reader:
            record = (
                clean_value(row['Policy_Number']),
                parse_decimal(row['Coverage_Limit']),
                parse_decimal(row['Deductible']),
                clean_value(row['Coverage_Tier']),
                clean_value(row['Optional_AddOns_Selected']),
                clean_value(row['Regulatory_AddOns_Selected']),
                parse_boolean(row['Business_Interruption_Coverage']),
                parse_boolean(row['Cyber_Extension']),
                parse_boolean(row['Incident_Response_AddOn'])
            )
            records.append(record)
    
    query = """
        INSERT INTO coverage_details (
            policy_number, coverage_limit, deductible, coverage_tier,
            optional_addons_selected, regulatory_addons_selected,
            business_interruption_coverage, cyber_extension, incident_response_addon
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (policy_number) DO NOTHING
    """
    
    cursor = conn.cursor()
    execute_batch(cursor, query, records)
    conn.commit()
    print(f"✓ Loaded {len(records)} coverage details")
    cursor.close()


def load_ai_risk_profile(conn):
    """Load AI risk profile data from CSV"""
    csv_file = DATA_DIR / 'ai_risk_profile.csv'
    print(f"\nLoading AI risk profiles from {csv_file}...")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = []
        
        for row in reader:
            record = (
                clean_value(row['Policy_Number']),
                clean_value(row['AI_System_Type']),
                clean_value(row['Deployment_Stage']),
                parse_integer(row['Number_of_Active_Agents']),
                parse_boolean(row['Critical_Workflows_Protected']),
                parse_integer(row['Incident_History_Count']),
                parse_date(row['Last_AI_Incident_Date']),
                parse_boolean(row['Has_High_Risk_Use_Cases']),
                clean_value(row['Regulatory_Classification']),
                parse_integer(row['Risk_Score_Internal'])
            )
            records.append(record)
    
    query = """
        INSERT INTO ai_risk_profile (
            policy_number, ai_system_type, deployment_stage, number_of_active_agents,
            critical_workflows_protected, incident_history_count, last_ai_incident_date,
            has_high_risk_use_cases, regulatory_classification, risk_score_internal
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (policy_number) DO NOTHING
    """
    
    cursor = conn.cursor()
    execute_batch(cursor, query, records)
    conn.commit()
    print(f"✓ Loaded {len(records)} AI risk profiles")
    cursor.close()


def load_claims_history(conn):
    """Load claims history data from CSV"""
    csv_file = DATA_DIR / 'claims_history.csv'
    print(f"\nLoading claims history from {csv_file}...")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = []
        
        for row in reader:
            record = (
                clean_value(row['Claim_ID']),
                clean_value(row['Policy_Number']),
                clean_value(row['Insured_ID']),
                parse_date(row['Claim_Date']),
                clean_value(row['Claim_Type']),
                clean_value(row['Claim_Description']),
                clean_value(row['Claim_Status']) or 'Pending',
                parse_decimal(row['Claim_Amount']),
                parse_decimal(row['Amount_Paid']) or 0
            )
            records.append(record)
    
    query = """
        INSERT INTO claims_history (
            claim_id, policy_number, insured_id, claim_date, claim_type,
            claim_description, claim_status, claim_amount, amount_paid
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (claim_id) DO NOTHING
    """
    
    cursor = conn.cursor()
    execute_batch(cursor, query, records)
    conn.commit()
    print(f"✓ Loaded {len(records)} claims")
    cursor.close()


def verify_data(conn):
    """Verify data loaded correctly"""
    print("\n" + "="*60)
    print("Data Verification")
    print("="*60)
    
    cursor = conn.cursor()
    
    tables = [
        'insureds',
        'policies',
        'coverage_details',
        'ai_risk_profile',
        'claims_history'
    ]
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:20} : {count:6} records")
    
    cursor.close()
    print("="*60)


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("AI Insurance Platform - Data Loading Script")
    print("="*60)
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        # Load data in order (respecting foreign key constraints)
        load_insureds(conn)
        load_policies(conn)
        load_coverage_details(conn)
        load_ai_risk_profile(conn)
        load_claims_history(conn)
        
        # Verify data
        verify_data(conn)
        
        print("\n✓ Data loading completed successfully!\n")
        
    except Exception as e:
        print(f"\n✗ Error during data loading: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
