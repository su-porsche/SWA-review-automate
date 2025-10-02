#!/bin/bash
# Setup and Import Script
# This script guides you through the setup process

echo "========================================="
echo "  Hierarchical Import System Setup"
echo "========================================="
echo ""

# Check if table exists
echo "Checking if chunk_categories table exists..."
TABLE_EXISTS=$(PGPASSWORD='swaagent911' psql -h localhost -U swaagent -d swadocs -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'chunk_categories');")

if [ "$TABLE_EXISTS" = "t" ]; then
    echo "✓ Table chunk_categories already exists"
    echo ""
else
    echo "✗ Table chunk_categories does not exist yet"
    echo ""
    echo "Please create the table first:"
    echo ""
    echo "  1. Open a new terminal"
    echo "  2. Run: sudo -u postgres psql swadocs"
    echo "  3. Copy and paste this SQL:"
    echo ""
    echo "----------------------------------------"
    cat << 'EOF'
CREATE TABLE IF NOT EXISTS chunk_categories (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    category_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunk_categories_chunk ON chunk_categories(chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_categories_category ON chunk_categories(category);
CREATE INDEX IF NOT EXISTS idx_chunk_categories_level ON chunk_categories(category_level);

GRANT SELECT, INSERT, UPDATE, DELETE ON chunk_categories TO swaagent;
GRANT USAGE, SELECT ON SEQUENCE chunk_categories_id_seq TO swaagent;

SELECT 'Table created!' as status;
\q
EOF
    echo "----------------------------------------"
    echo ""
    echo "After creating the table, run this script again."
    exit 1
fi

# Ask user if they want to clear existing data
echo "Do you want to clear existing data before import? (y/N)"
read -r CLEAR_DATA

if [[ "$CLEAR_DATA" =~ ^[Yy]$ ]]; then
    CLEAR_FLAG="--clear"
    echo "✓ Will clear existing data"
else
    CLEAR_FLAG=""
    echo "✓ Will keep existing data"
fi

echo ""
echo "Starting import..."
echo ""

# Run import
.venv/bin/python import_to_db_hierarchical.py txts $CLEAR_FLAG

# Check results
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "  Import completed successfully!"
    echo "========================================="
    echo ""
    echo "Database statistics:"
    PGPASSWORD='swaagent911' psql -h localhost -U swaagent -d swadocs -c "
    SELECT
        'Documents' as type, COUNT(*)::text as count FROM documents
    UNION ALL
    SELECT 'Chunks', COUNT(*)::text FROM chunks
    UNION ALL
    SELECT 'Category Links', COUNT(*)::text FROM chunk_categories;
    "
    echo ""
    echo "Example query - Chunks from chapter 5:"
    echo "  See QUICK_START.md for more queries"
else
    echo ""
    echo "Import failed. Please check the error messages above."
    exit 1
fi
