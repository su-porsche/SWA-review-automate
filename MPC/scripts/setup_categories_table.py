#!/usr/bin/env python3
"""
Setup script to create chunk_categories table.
"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'database': 'swadocs',
    'user': 'swaagent',
    'password': 'swaagent911',
    'port': 5432
}

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("Creating chunk_categories table...")

        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunk_categories (
                id SERIAL PRIMARY KEY,
                chunk_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                category_level INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunk_categories_chunk
            ON chunk_categories(chunk_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunk_categories_category
            ON chunk_categories(category)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunk_categories_level
            ON chunk_categories(category_level)
        """)

        conn.commit()

        # Verify
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'chunk_categories'
        """)

        if cursor.fetchone():
            print("✓ Table chunk_categories created successfully")

            # Show table structure
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'chunk_categories'
                ORDER BY ordinal_position
            """)

            print("\nTable structure:")
            for row in cursor.fetchall():
                print(f"  - {row[0]}: {row[1]}")
        else:
            print("❌ Table creation failed")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
