#!/usr/bin/env python3
"""
Helper script to create chunk_categories table.
Tries to connect as postgres user (no password needed on local WSL).
"""

import psycopg2
import sys

SQL = """
-- Create junction table
CREATE TABLE IF NOT EXISTS chunk_categories (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    category_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_chunk_categories_chunk ON chunk_categories(chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_categories_category ON chunk_categories(category);
CREATE INDEX IF NOT EXISTS idx_chunk_categories_level ON chunk_categories(category_level);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON chunk_categories TO swaagent;
GRANT USAGE, SELECT ON SEQUENCE chunk_categories_id_seq TO swaagent;

-- Grant CREATE permission
GRANT CREATE ON SCHEMA public TO swaagent;
"""

def main():
    # Try different connection methods
    configs = [
        {'host': 'localhost', 'database': 'swadocs', 'user': 'postgres'},
        {'host': '/var/run/postgresql', 'database': 'swadocs', 'user': 'postgres'},
    ]

    for config in configs:
        try:
            print(f"Trying to connect as postgres user...")
            conn = psycopg2.connect(**config)
            cursor = conn.cursor()

            print("✓ Connected successfully")
            print("Creating table...")

            cursor.execute(SQL)
            conn.commit()

            print("✓ Table chunk_categories created")

            # Verify
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'chunk_categories'
                ORDER BY ordinal_position
            """)

            print("\nTable structure:")
            for row in cursor.fetchall():
                print(f"  - {row[0]}: {row[1]}")

            cursor.close()
            conn.close()

            print("\n✓ Setup complete!")
            return 0

        except Exception as e:
            print(f"  Failed: {e}")
            continue

    print("\n❌ Could not connect as postgres user")
    print("\nPlease run manually:")
    print("  sudo -u postgres psql swadocs")
    print("\nThen paste this SQL:")
    print("-" * 60)
    print(SQL)
    print("-" * 60)
    return 1

if __name__ == '__main__':
    sys.exit(main())
