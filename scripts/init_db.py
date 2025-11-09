#!/usr/bin/env python3
"""
Initialize PostgreSQL database with schema
Run this script to set up the database for the first time
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_db_params():
    """Get database connection parameters from environment"""
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'voyce_db'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', '')
    }


def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    params = get_db_params()
    db_name = params['database']

    # Connect to default postgres database
    conn_params = params.copy()
    conn_params['database'] = 'postgres'

    try:
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )

        if not cursor.fetchone():
            print(f"Creating database: {db_name}")
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
            )
            print(f"Database {db_name} created successfully")
        else:
            print(f"Database {db_name} already exists")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)


def run_schema_script():
    """Run the schema SQL script"""
    params = get_db_params()
    schema_file = Path(__file__).parent.parent / 'database' / '001_initial_schema.sql'

    if not schema_file.exists():
        print(f"Schema file not found: {schema_file}")
        sys.exit(1)

    try:
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()

        print(f"Running schema script: {schema_file}")

        with open(schema_file, 'r') as f:
            sql_script = f.read()

        cursor.execute(sql_script)
        conn.commit()

        print("Schema created successfully")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error running schema script: {e}")
        sys.exit(1)


def verify_tables():
    """Verify that tables were created"""
    params = get_db_params()

    expected_tables = [
        'users',
        'voice_submissions',
        'transcriptions',
        'ai_analysis',
        'sync_metadata',
        'processing_costs',
        'audit_log'
    ]

    try:
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        tables = [row[0] for row in cursor.fetchall()]

        print("\nCreated tables:")
        for table in tables:
            print(f"  ✓ {table}")

        missing = set(expected_tables) - set(tables)
        if missing:
            print(f"\n⚠ Missing tables: {', '.join(missing)}")
        else:
            print(f"\n✓ All {len(expected_tables)} expected tables created successfully")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error verifying tables: {e}")
        sys.exit(1)


def main():
    """Main initialization function"""
    print("=" * 60)
    print("Voyce Database Initialization")
    print("=" * 60)
    print()

    # Step 1: Create database
    create_database_if_not_exists()
    print()

    # Step 2: Run schema script
    run_schema_script()
    print()

    # Step 3: Verify tables
    verify_tables()
    print()

    print("=" * 60)
    print("Database initialization complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Start the backend: python main.py")
    print("  2. Visit: http://localhost:8000/api/docs")
    print()


if __name__ == '__main__':
    main()
