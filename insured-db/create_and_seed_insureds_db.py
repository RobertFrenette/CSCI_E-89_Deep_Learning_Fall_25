"""
Create and populate SQLite database from insured CSV files.

This script reads CSV files from the knowledge-base/insured directory and creates
a properly normalized SQLite database with foreign key constraints.

Run this script to generate the insureds.db file before launching the LLM RAG Agent.
"""

import sqlite3
import csv
from pathlib import Path

def create_database(db_path):
    """
    Create the database schema with all necessary tables.

    Description:
        Establishes a connection to a SQLite database and creates a normalized schema for storing insured customer data, policies, coverage details, AI risk profiles, and claims history. Enables foreign key constraints for referential integrity.

    Params:
        db_path (Path or str): The file path where the SQLite database will be created.

    Returns:
        sqlite3.Connection: An active database connection object with the schema created.

    Raises:
        sqlite3.Error: If there is an error creating the database or tables.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Drop existing tables if they exist (for fresh start)
    cursor.execute("DROP TABLE IF EXISTS claims_history")
    cursor.execute("DROP TABLE IF EXISTS ai_risk_profile")
    cursor.execute("DROP TABLE IF EXISTS coverage_details")
    cursor.execute("DROP TABLE IF EXISTS policies")
    cursor.execute("DROP TABLE IF EXISTS insureds")
    
    # Create insureds table
    cursor.execute("""
        CREATE TABLE insureds (
            Insured_ID TEXT PRIMARY KEY,
            First_Name TEXT,
            Last_Name TEXT,
            Date_of_Birth TEXT,
            Phone_Number TEXT,
            Email_Address TEXT,
            Address_Line1 TEXT,
            Address_Line2 TEXT,
            City TEXT,
            State TEXT,
            Postal_Code TEXT,
            Country TEXT,
            Company_Name TEXT,
            Industry TEXT,
            Contact_Person TEXT
        )
    """)
    
    # Create policies table
    cursor.execute("""
        CREATE TABLE policies (
            Policy_Number TEXT PRIMARY KEY,
            Insured_ID TEXT NOT NULL,
            Policy_Type TEXT,
            Effective_Date TEXT,
            Expiration_Date TEXT,
            Policy_Status TEXT,
            Payment_Status TEXT,
            Annual_Premium REAL,
            Monthly_Premium REAL,
            Payment_Method TEXT,
            Broker TEXT,
            Discounts_Applied TEXT,
            FOREIGN KEY (Insured_ID) REFERENCES insureds(Insured_ID)
        )
    """)
    
    # Create coverage_details table
    cursor.execute("""
        CREATE TABLE coverage_details (
            Policy_Number TEXT PRIMARY KEY,
            Coverage_Limit INTEGER,
            Deductible INTEGER,
            Coverage_Tier TEXT,
            Optional_AddOns_Selected TEXT,
            Regulatory_AddOns_Selected TEXT,
            Business_Interruption_Coverage TEXT,
            Cyber_Extension TEXT,
            Incident_Response_AddOn TEXT,
            FOREIGN KEY (Policy_Number) REFERENCES policies(Policy_Number)
        )
    """)
    
    # Create ai_risk_profile table
    cursor.execute("""
        CREATE TABLE ai_risk_profile (
            Policy_Number TEXT PRIMARY KEY,
            AI_System_Type TEXT,
            Deployment_Stage TEXT,
            Number_of_Active_Agents INTEGER,
            Critical_Workflows_Protected TEXT,
            Incident_History_Count INTEGER,
            Last_AI_Incident_Date TEXT,
            Has_High_Risk_Use_Cases TEXT,
            Regulatory_Classification TEXT,
            Risk_Score_Internal INTEGER,
            FOREIGN KEY (Policy_Number) REFERENCES policies(Policy_Number)
        )
    """)
    
    # Create claims_history table
    cursor.execute("""
        CREATE TABLE claims_history (
            Claim_ID TEXT PRIMARY KEY,
            Policy_Number TEXT NOT NULL,
            Insured_ID TEXT NOT NULL,
            Claim_Date TEXT,
            Claim_Type TEXT,
            Claim_Description TEXT,
            Claim_Status TEXT,
            Claim_Amount REAL,
            Amount_Paid REAL,
            FOREIGN KEY (Policy_Number) REFERENCES policies(Policy_Number),
            FOREIGN KEY (Insured_ID) REFERENCES insureds(Insured_ID)
        )
    """)
    
    # Create indexes for better query performance
    cursor.execute("CREATE INDEX idx_policies_insured ON policies(Insured_ID)")
    cursor.execute("CREATE INDEX idx_claims_policy ON claims_history(Policy_Number)")
    cursor.execute("CREATE INDEX idx_claims_insured ON claims_history(Insured_ID)")
    
    conn.commit()
    return conn

def import_csv(conn, table_name, csv_path):
    """
    Import data from a CSV file into the specified table.

    Description:
        Reads data from a CSV file and inserts it into the given table in the database.

    Params:
        conn (sqlite3.Connection): Active database connection object.
        table_name (str): Name of the table to import data into.
        csv_path (Path): Path to the CSV file.

    Returns:
        int: The number of rows successfully imported from the CSV file.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        sqlite3.Error: If there is an error inserting data into the table.
    """
    cursor = conn.cursor()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        if not rows:
            print(f"⚠️  No data found in {csv_path}")
            return 0
        
        # Get column names from the first row
        columns = list(rows[0].keys())
        placeholders = ','.join(['?' for _ in columns])
        column_names = ','.join(columns)
        
        # Insert data
        insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
        
        for row in rows:
            values = [row[col] for col in columns]
            cursor.execute(insert_sql, values)
        
        conn.commit()
        return len(rows)

def setup_paths(db_path, csv_dir):
    """
    Ensures required directories exist and prints their locations.

    Description:
        Checks and creates the database directory if needed, and verifies the existence of the CSV directory.

    Params:
        db_path (Path): Path to the database file.
        csv_dir (Path): Path to the directory containing CSV files.

    Returns:
        bool: True if setup is successful, False otherwise.

    Raises:
        OSError: If directory creation fails.
    """
    db_path.parent.mkdir(exist_ok=True)
    if not csv_dir.exists():
        print(f"❌ CSV directory not found: {csv_dir}")
        print("Please ensure the insured_data folder exists with CSV files.")
        return False
    print(f"📁 Database location: {db_path}")
    print(f"📁 CSV source directory: {csv_dir}")
    print()
    return True

def remove_existing_db(db_path):
    """
    Removes the existing database file if it exists.

    Description:
        Deletes the database file at the specified path if it exists.

    Params:
        db_path (Path): Path to the database file.

    Returns:
        None

    Raises:
        OSError: If file removal fails.
    """
    if db_path.exists():
        print(f"🗑️  Removing existing database: {db_path}")
        db_path.unlink()
        print("✅ Existing database removed")
        print()

def create_schema(db_path):
    """
    Creates the database schema and returns the connection object.

    Description:
        Calls create_database to initialize the schema and returns the connection.

    Params:
        db_path (Path): Path to the database file.

    Returns:
        sqlite3.Connection: An active database connection object with the schema created.

    Raises:
        sqlite3.Error: If there is an error creating the database or tables.
    """
    print("🔨 Creating database schema...")
    conn = create_database(db_path)
    print("✅ Schema created successfully")
    print()
    return conn

def import_all_csvs(conn, csv_dir):
    """
    Imports all CSV files into the database in the correct order.

    Description:
        Iterates through all required CSV files and imports their data into the corresponding tables, respecting foreign key order.

    Params:
        conn (sqlite3.Connection): Active database connection object.
        csv_dir (Path): Path to the directory containing CSV files.

    Returns:
        int: Total number of rows imported from all CSV files.

    Raises:
        FileNotFoundError: If any required CSV file does not exist.
        sqlite3.Error: If there is an error inserting data into the tables.
    """
    tables_to_import = [
        ("insureds", "insureds.csv"),
        ("policies", "policies.csv"),
        ("coverage_details", "coverage_details.csv"),
        ("ai_risk_profile", "ai_risk_profile.csv"),
        ("claims_history", "claims_history.csv")
    ]
    print("📥 Importing data from CSV files...")
    print()
    total_rows = 0
    for table_name, csv_file in tables_to_import:
        csv_path = csv_dir / csv_file
        if not csv_path.exists():
            print(f"❌ File not found: {csv_path}")
            continue
        print(f"   Importing {csv_file}...", end=" ")
        row_count = import_csv(conn, table_name, csv_path)
        total_rows += row_count
        print(f"✅ {row_count:,} rows")
    print()
    print(f"✅ Total rows imported: {total_rows:,}")
    print()
    return total_rows

def verify_data(conn):
    """
    Runs verification queries to check record counts for each table.

    Description:
        Executes SELECT COUNT(*) queries for each table and prints the record counts.

    Params:
        conn (sqlite3.Connection): Active database connection object.

    Returns:
        None

    Raises:
        sqlite3.Error: If there is an error executing the queries.
    """
    print("🔍 Verifying data...")
    cursor = conn.cursor()
    verification_queries = [
        ("Insureds", "SELECT COUNT(*) FROM insureds"),
        ("Policies", "SELECT COUNT(*) FROM policies"),
        ("Coverage Details", "SELECT COUNT(*) FROM coverage_details"),
        ("AI Risk Profiles", "SELECT COUNT(*) FROM ai_risk_profile"),
        ("Claims", "SELECT COUNT(*) FROM claims_history")
    ]
    for label, query in verification_queries:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        print(f"   {label}: {count:,} records")
    print()

def show_sample_query(conn):
    """
    Executes and displays a sample query for top 5 insureds by policy count.

    Description:
        Runs a sample SQL query to display the top 5 insureds by policy count and prints the results.

    Params:
        conn (sqlite3.Connection): Active database connection object.

    Returns:
        None

    Raises:
        sqlite3.Error: If there is an error executing the query.
    """
    print("📊 Sample query - Top 5 insureds by policy count:")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.First_Name, i.Last_Name, i.Company_Name, COUNT(p.Policy_Number) as policy_count
        FROM insureds i
        LEFT JOIN policies p ON i.Insured_ID = p.Insured_ID
        GROUP BY i.Insured_ID
        ORDER BY policy_count DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]} {row[1]} ({row[2]}): {row[3]} policies")
    print()

def main():
    """
    Orchestrates the insureds database creation and population process.

    Description:
        Delegates setup, import, verification, and sample query tasks to helper functions.

    Params:
        None

    Returns:
        None

    Raises:
        Any exceptions raised by helper functions are propagated.
    """
    print("=" * 70)
    print("Creating AI Agent Insure - Insureds Database")
    print("=" * 70)
    print()

    script_dir = Path(__file__).parent
    db_path = script_dir / "insureds.db"
    csv_dir = script_dir / "insured_data"

    if not setup_paths(db_path, csv_dir):
        return

    remove_existing_db(db_path)
    conn = create_schema(db_path)
    total_rows = import_all_csvs(conn, csv_dir)
    verify_data(conn)
    show_sample_query(conn)
    conn.close()

    print("=" * 70)
    print("✅ Database created and populated successfully!")
    print("=" * 70)
    print()
    print(f"You can now use the database at: {db_path}")
    print()

if __name__ == "__main__":
    main()
