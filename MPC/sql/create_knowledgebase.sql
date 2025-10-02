-- 1. Datenbank und Extension anlegen
CREATE DATABASE swadocs;
\c swadocs

CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Rolle und User anlegen
CREATE ROLE swa_readonly;
CREATE USER swaagent WITH PASSWORD 'swaagent911';

-- 3. Rechte für User und Rolle
GRANT swa_readonly TO swaagent;

-- 4. Tabellen anlegen
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title TEXT,
    category TEXT,
    source_path TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text TEXT,
    embedding VECTOR(1536),
    chunk_index INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Hierarchical category support: chunks can belong to multiple categories
CREATE TABLE chunk_categories (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    category_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Indizes für schnelle Suche
CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Indexes for chunk_categories
CREATE INDEX idx_chunk_categories_chunk ON chunk_categories(chunk_id);
CREATE INDEX idx_chunk_categories_category ON chunk_categories(category);
CREATE INDEX idx_chunk_categories_level ON chunk_categories(category_level);

-- 6. Rechte für Tabellen
GRANT USAGE, SELECT ON SEQUENCE documents_id_seq TO swa_readonly;
GRANT USAGE, SELECT ON SEQUENCE chunks_id_seq TO swa_readonly;
GRANT USAGE, SELECT ON SEQUENCE chunk_categories_id_seq TO swa_readonly;

GRANT SELECT, INSERT, UPDATE, DELETE ON documents TO swa_readonly;
GRANT SELECT, INSERT, UPDATE, DELETE ON chunks TO swa_readonly;
GRANT SELECT, INSERT, UPDATE, DELETE ON chunk_categories TO swa_readonly;

-- 7. Optional: Nur SELECT für Rolle, vollen Zugriff für swaagent
REVOKE INSERT, UPDATE, DELETE ON documents FROM swa_readonly;
REVOKE INSERT, UPDATE, DELETE ON chunks FROM swa_readonly;
REVOKE INSERT, UPDATE, DELETE ON chunk_categories FROM swa_readonly;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO swaagent;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO swaagent;

-- 8. Standard-Schema für User setzen
ALTER USER swaagent SET search_path TO public;

-- 9. Helper function for hierarchical category queries
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

COMMENT ON FUNCTION get_chunks_in_category_hierarchy IS 'Find all chunks in a category hierarchy, e.g. get_chunks_in_category_hierarchy(''5%'') finds all chunks in chapter 5';

-- Example usage:
-- SELECT * FROM get_chunks_in_category_hierarchy('5%') LIMIT 10;