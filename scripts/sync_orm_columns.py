#!/usr/bin/env python3
"""
Script to automatically add all missing columns to database tables based on ORM models.

This script compares the ORM model definitions with the actual database schema
and generates ALTER TABLE statements for any missing columns.
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.models.orm_models import (
    BudgetRecord,
    FundingRecord,
    ILabsRecord,
    MembershipRecord,
    ProposalRecord,
    PublicationRecord,
)
from backend.services.db import engine


# Map SQLAlchemy column types to SQL types
TYPE_MAPPING = {
    'INTEGER': 'INT',
    'VARCHAR': 'VARCHAR',
    'STRING': 'VARCHAR(255)',
    'TEXT': 'TEXT',
    'FLOAT': 'FLOAT',
    'DATE': 'DATE',
    'DATETIME': 'DATETIME',
    'BOOLEAN': 'TINYINT(1)',
}


def get_column_type_str(column):
    """Convert SQLAlchemy column type to SQL string."""
    type_str = str(column.type)
    
    # Handle VARCHAR with length
    if 'VARCHAR' in type_str.upper():
        if '(' in type_str:
            return type_str.upper()
        else:
            # Default VARCHAR length
            if hasattr(column.type, 'length') and column.type.length:
                return f"VARCHAR({column.type.length})"
            return 'VARCHAR(255)'
    
    # Handle other types
    if 'INTEGER' in type_str.upper() or 'INT' in type_str.upper():
        return 'INT'
    elif 'FLOAT' in type_str.upper() or 'DOUBLE' in type_str.upper():
        return 'FLOAT'
    elif 'TEXT' in type_str.upper():
        return 'TEXT'
    elif 'DATE' in type_str.upper():
        return 'DATE'
    elif 'DATETIME' in type_str.upper() or 'TIMESTAMP' in type_str.upper():
        return 'DATETIME'
    
    # Default
    return type_str.upper()


async def get_existing_columns(table_name):
    """Get list of existing columns in a database table."""
    async with engine.connect() as conn:
        result = await conn.execute(text(f"SHOW COLUMNS FROM {table_name}"))
        rows = result.fetchall()
        # Return set of column names (first column of each row)
        return {row[0] for row in rows}


async def add_missing_columns():
    """Compare ORM models with database and add missing columns."""
    
    # Map of table names to ORM models
    models = {
        'budgets': BudgetRecord,
        'funding': FundingRecord,
        'ilabs': ILabsRecord,
        'membership': MembershipRecord,
        'proposals': ProposalRecord,
        'publications': PublicationRecord,
    }
    
    print("=" * 80)
    print("SYNCING ORM MODELS WITH DATABASE SCHEMA")
    print("=" * 80)
    print()
    
    total_added = 0
    total_skipped = 0
    
    for table_name, model in models.items():
        print(f"Processing table: {table_name}")
        print("-" * 80)
        
        # Get existing columns from database
        try:
            existing_columns = await get_existing_columns(table_name)
        except Exception as e:
            print(f"  ⚠️  Could not read table {table_name}: {e}")
            print()
            continue
        
        # Get columns from ORM model
        orm_columns = {}
        for column_name, column in model.__table__.columns.items():
            # Skip the primary key 'id' column
            if column_name == 'id':
                continue
            orm_columns[column_name] = column
        
        # Find missing columns
        missing_columns = set(orm_columns.keys()) - existing_columns
        
        if not missing_columns:
            print(f"  ✅ All columns present ({len(orm_columns)} columns)")
            print()
            continue
        
        print(f"  Found {len(missing_columns)} missing column(s): {', '.join(sorted(missing_columns))}")
        print()
        
        # Add missing columns
        async with engine.begin() as conn:
            for col_name in sorted(missing_columns):
                column = orm_columns[col_name]
                col_type = get_column_type_str(column)
                nullable = "NULL" if column.nullable else "NOT NULL"
                
                sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} {nullable}"
                
                try:
                    print(f"  Adding: {col_name} ({col_type})")
                    await conn.execute(text(sql))
                    print(f"    ✅ Success")
                    total_added += 1
                except Exception as e:
                    error_str = str(e).lower()
                    if "duplicate column name" in error_str or "already exists" in error_str:
                        print(f"    ⚠️  Already exists (skipping)")
                        total_skipped += 1
                    else:
                        print(f"    ❌ Error: {e}")
        
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Columns added: {total_added}")
    print(f"  Columns skipped (already exist): {total_skipped}")
    print()
    print("=" * 80)
    print("DONE!")
    print("=" * 80)
    print()
    print("You can now run your database write tests again.")


if __name__ == "__main__":
    asyncio.run(add_missing_columns())

