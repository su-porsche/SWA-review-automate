#!/bin/bash
# Setup script for hierarchical category support
# Run as: sudo bash setup_db.sh

echo "Setting up hierarchical category support..."

# Run as postgres user
sudo -u postgres psql swadocs <<'EOF'

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

-- Grant CREATE permission for future operations
GRANT CREATE ON SCHEMA public TO swaagent;

-- Verify
SELECT 'Table chunk_categories created successfully' as status;
\dt chunk_categories

EOF

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Re-import data: .venv/bin/python import_to_db_hierarchical.py txts --clear"
echo "  2. Verify: PGPASSWORD='swaagent911' psql -h localhost -U swaagent -d swadocs -c 'SELECT COUNT(*) FROM chunk_categories;'"
