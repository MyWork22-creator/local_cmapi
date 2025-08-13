#!/usr/bin/env python3
"""
Script to check what tables exist in the database.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_tables():
    """Check what tables exist in the database."""
    try:
        from app.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            
        print("📊 Existing tables in database:")
        for table in tables:
            print(f"  - {table}")
        
        if not tables:
            print("  No tables found!")
        
        return tables
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return []

def check_table_schema(table_name):
    """Check the schema of a specific table."""
    try:
        from app.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            columns = list(result)
            
        print(f"\n📋 Schema for table '{table_name}':")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
        
    except Exception as e:
        print(f"❌ Error checking schema for {table_name}: {e}")

def main():
    """Main function."""
    print("🔍 Database Table Inspector")
    print("=" * 30)
    
    tables = check_tables()
    
    # Check schema for each table
    for table in tables:
        check_table_schema(table)

if __name__ == "__main__":
    main()
