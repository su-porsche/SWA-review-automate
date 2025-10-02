-- Migration: Add category relationships for chunks
-- This allows chunks to belong to multiple chapters (main + subchapters)
-- Run as: sudo -u postgres psql -d swadocs -f migrate_add_categories.sql

-- 1. Create junction table for chunk-category relationships
CREATE TABLE IF NOT EXISTS chunk_categories (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    category_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Create index for fast category lookups
CREATE INDEX IF NOT EXISTS idx_chunk_categories_chunk ON chunk_categories(chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_categories_category ON chunk_categories(category);
CREATE INDEX IF NOT EXISTS idx_chunk_categories_level ON chunk_categories(category_level);

-- 3. Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON chunk_categories TO swaagent;
GRANT USAGE, SELECT ON SEQUENCE chunk_categories_id_seq TO swaagent;

-- 4. Add helper function to get all chunks in a category hierarchy
CREATE OR REPLACE FUNCTION get_chunks_in_category_hierarchy(category_pattern TEXT)
RETURNS TABLE (
    chunk_id INTEGER,
    chunk_text TEXT,
    document_title TEXT,
    categories TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        c.id as chunk_id,
        c.chunk_text,
        d.title as document_title,
        ARRAY_AGG(DISTINCT cc.category ORDER BY cc.category) as categories
    FROM chunks c
    JOIN chunk_categories cc ON c.id = cc.chunk_id
    JOIN documents d ON c.document_id = d.id
    WHERE cc.category LIKE category_pattern
    GROUP BY c.id, c.chunk_text, d.title
    ORDER BY c.id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE chunk_categories IS 'Junction table: chunks can belong to multiple chapter categories';
COMMENT ON FUNCTION get_chunks_in_category_hierarchy IS 'Find all chunks in a category hierarchy, e.g. "1%" finds all in chapter 1';
