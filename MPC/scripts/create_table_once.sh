#!/bin/bash
# One-time script to create chunk_categories table
# Run as: bash create_table_once.sh

echo "Creating chunk_categories table..."

sudo -u postgres psql swadocs <<'EOF'

-- Create table if not exists
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

-- Grant permissions to swaagent
GRANT SELECT, INSERT, UPDATE, DELETE ON chunk_categories TO swaagent;
GRANT USAGE, SELECT ON SEQUENCE chunk_categories_id_seq TO swaagent;

-- Show result
SELECT 'Table chunk_categories ready!' as status;
\d chunk_categories

EOF

echo ""
echo "✓ Done! Now you can run:"
echo "  .venv/bin/python import_to_db_hierarchical.py txts --clear"
