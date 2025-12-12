#!/usr/bin/env python3
"""
Script to add missing columns to database tables.

This script executes the SQL statements from add_missing_columns_all.sql
using the application's database connection.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.services.db import engine


async def add_missing_columns():
    """Add missing columns to database tables."""
    
    # SQL statements to execute
    sql_statements = [
        # Funding table
        "ALTER TABLE funding ADD COLUMN project_status VARCHAR(255) NULL",
        "ALTER TABLE funding ADD COLUMN project_id INT NULL",
        "ALTER TABLE funding ADD COLUMN project_uid VARCHAR(255) NULL",
        
        # Membership table
        "ALTER TABLE membership ADD COLUMN rlogx_id INT NULL",
        "ALTER TABLE membership ADD COLUMN member_id INT NULL",
        "ALTER TABLE membership ADD COLUMN ccm_type_code TEXT NULL",
        
        # Publications table
        "ALTER TABLE publications ADD COLUMN publication_id INT NULL",
        "ALTER TABLE publications ADD COLUMN publication_uid VARCHAR(255) NULL",
        "ALTER TABLE publications ADD COLUMN pub_type VARCHAR(255) NULL",
    ]
    
    print("=" * 80)
    print("ADDING MISSING COLUMNS TO DATABASE TABLES")
    print("=" * 80)
    print()
    
    async with engine.begin() as conn:
        for sql in sql_statements:
            try:
                print(f"Executing: {sql}")
                await conn.execute(text(sql))
                print(f"  ✅ Success")
            except Exception as e:
                # Check if error is because column already exists
                error_str = str(e).lower()
                if "duplicate column name" in error_str or "already exists" in error_str:
                    print(f"  ⚠️  Column already exists (skipping)")
                else:
                    print(f"  ❌ Error: {e}")
                    # Continue with other statements even if one fails
            print()
    
    # Verify columns were added
    print("=" * 80)
    print("VERIFYING COLUMNS")
    print("=" * 80)
    print()
    
    async with engine.connect() as conn:
        verify_queries = [
            ("Funding", "SHOW COLUMNS FROM funding WHERE Field IN ('project_status', 'project_id', 'project_uid')"),
            ("Membership", "SHOW COLUMNS FROM membership WHERE Field IN ('rlogx_id', 'member_id', 'ccm_type_code')"),
            ("Publications", "SHOW COLUMNS FROM publications WHERE Field IN ('publication_id', 'publication_uid', 'pub_type')"),
        ]
        
        for table_name, query in verify_queries:
            print(f"{table_name} table:")
            try:
                result = await conn.execute(text(query))
                rows = result.fetchall()
                if rows:
                    for row in rows:
                        print(f"  ✅ {row[0]} ({row[1]})")
                else:
                    print(f"  ⚠️  No columns found (may not exist)")
            except Exception as e:
                print(f"  ❌ Error: {e}")
            print()
    
    print("=" * 80)
    print("DONE!")
    print("=" * 80)
    print()
    print("You can now run your database write tests again.")


if __name__ == "__main__":
    asyncio.run(add_missing_columns())

