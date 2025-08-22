#!/usr/bin/env python3
"""
Fix enum values in the database to match the model definitions.
"""

import os
import sys
from sqlalchemy import create_engine, text

def get_database_url():
    """Get the database URL, defaulting to production unless DEV specified"""
    if os.getenv("USE_DEV_DB"):
        return "postgresql+psycopg://progress_user_dev:progress_password_dev@localhost:5433/progress_tracker_dev"
    else:
        return "postgresql+psycopg://progress_user:progress_password@localhost:5432/progress_tracker"

def fix_enums():
    """Drop and recreate enums with correct values"""
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    print(f"Connecting to database: {database_url}")
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Drop all tables first
            print("Dropping all tables...")
            conn.execute(text("DROP TABLE IF EXISTS drawing_entries CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS reading_entries CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS fitness_entries CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
            
            # Drop enum types
            print("Dropping enum types...")
            conn.execute(text("DROP TYPE IF EXISTS drawingmedium CASCADE;"))
            conn.execute(text("DROP TYPE IF EXISTS drawingstatus CASCADE;"))
            conn.execute(text("DROP TYPE IF EXISTS readingstatus CASCADE;"))
            conn.execute(text("DROP TYPE IF EXISTS readingtype CASCADE;"))
            conn.execute(text("DROP TYPE IF EXISTS fitnessstatus CASCADE;"))
            conn.execute(text("DROP TYPE IF EXISTS fitnesstype CASCADE;"))
            
            # Create enum types with correct values
            print("Creating enum types...")
            conn.execute(text("CREATE TYPE drawingmedium AS ENUM ('colored_pencils', 'crayons', 'markers', 'watercolor', 'digital', 'beads', 'mixed_media');"))
            conn.execute(text("CREATE TYPE drawingstatus AS ENUM ('planned', 'in_progress', 'completed', 'abandoned', 'continued_next_day');"))
            conn.execute(text("CREATE TYPE readingstatus AS ENUM ('pending', 'in_progress', 'completed', 'paused', 'abandoned');"))
            conn.execute(text("CREATE TYPE readingtype AS ENUM ('physical_book', 'audiobook', 'ebook', 'magazine', 'comic');"))
            conn.execute(text("CREATE TYPE fitnessstatus AS ENUM ('planned', 'in_progress', 'completed', 'skipped');"))
            conn.execute(text("CREATE TYPE fitnesstype AS ENUM ('cardio', 'strength', 'flexibility', 'sports', 'walking', 'running', 'cycling', 'swimming', 'yoga', 'other');"))
            
            trans.commit()
            print("Enums recreated successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"Error: {e}")
            raise

if __name__ == "__main__":
    print("Enum Fix Script")
    print("===============")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--dev":
        os.environ["USE_DEV_DB"] = "true"
        print("Using development database")
    else:
        print("Using production database")
    
    try:
        fix_enums()
        print("\nNow run the main application to recreate tables with correct enums.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)