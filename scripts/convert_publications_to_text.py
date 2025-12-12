#!/usr/bin/env python3
"""
Convert VARCHAR(255) columns to TEXT in publications table to avoid row size limit.

MySQL has a 65,535 byte limit for row size (excluding BLOBs/TEXT).
This script converts appropriate VARCHAR columns to TEXT to free up space.
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.services.db import engine


async def convert_columns():
    """Convert VARCHAR columns to TEXT in publications table."""
    
    # Columns to convert to TEXT (ones that likely contain longer content)
    columns_to_convert = [
        'abstract',
        'affiliations',
        'authors',
        'title',
        'grants',
        'cancer_relevance_justification',
        'all_ccm_authors_possible_names',
        'all_ccm_authors',
        'intra_authors',
        'inter_authors',
        'inter_programs',
        'citation',
        'cores_used',
        'research_programs',
        'research_program',
        'identified_cancer_centers',
        'identify_intra_authors',
        'identify_inter_authors',
        'both_in_trainter',
        'author_verification',
    ]
    
    print("=" * 80)
    print("CONVERTING VARCHAR COLUMNS TO TEXT IN PUBLICATIONS TABLE")
    print("=" * 80)
    print()
    print("This helps avoid MySQL's 65,535 byte row size limit.")
    print("TEXT columns don't count toward the row size limit.")
    print()
    
    converted = 0
    skipped = 0
    errors = 0
    
    async with engine.begin() as conn:
        for col_name in columns_to_convert:
            sql = f"ALTER TABLE publications MODIFY COLUMN {col_name} TEXT NULL"
            try:
                print(f"Converting: {col_name}")
                await conn.execute(text(sql))
                print(f"  ✅ Success")
                converted += 1
            except Exception as e:
                error_str = str(e).lower()
                if "doesn't exist" in error_str or "unknown column" in error_str:
                    print(f"  ⚠️  Column doesn't exist (skipping)")
                    skipped += 1
                elif "duplicate" in error_str:
                    print(f"  ℹ️  Already TEXT (skipping)")
                    skipped += 1
                else:
                    print(f"  ❌ Error: {e}")
                    errors += 1
        
        # Now add any missing columns that might not exist yet
        print()
        print("Adding missing columns if needed...")
        missing_columns = [
            ("pub_type", "VARCHAR(255)"),
            ("research_programs", "TEXT"),  # Add as TEXT since we're converting these
        ]
        
        for col_name, col_type in missing_columns:
            try:
                await conn.execute(text(f"ALTER TABLE publications ADD COLUMN {col_name} {col_type} NULL"))
                print(f"  ✅ Added {col_name}")
            except Exception as e:
                error_str = str(e).lower()
                if "duplicate column" in error_str or "already exists" in error_str:
                    print(f"  ℹ️  {col_name} already exists")
                else:
                    print(f"  ❌ Error adding {col_name}: {e}")
                    errors += 1
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Columns converted: {converted}")
    print(f"  Columns skipped: {skipped}")
    print(f"  Errors: {errors}")
    print()
    print("=" * 80)
    print("DONE!")
    print("=" * 80)
    print()
    print("You can now run your database write tests again.")


if __name__ == "__main__":
    asyncio.run(convert_columns())

