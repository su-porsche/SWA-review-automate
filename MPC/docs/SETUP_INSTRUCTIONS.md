# Setup Instructions for Hierarchical Category Support

## Problem
Die aktuelle Implementierung hat zwei Probleme:
1. ❌ Chunks werden nur nach Größe geschnitten, nicht nach Kapitelgrenzen
2. ❌ Chunks können nicht zu mehreren Kapiteln (Hauptkapitel + Unterkapitel) zugeordnet werden

## Lösung
Neue Implementierung mit:
1. ✅ `chunk_categories` Tabelle für Many-to-Many Beziehung
2. ✅ Chunks werden bei Kapitelgrenzen geschnitten (max 500 Zeichen)
3. ✅ Jeder Chunk gehört zu allen Parent-Kategorien (z.B. 1.2.3 → [1.2.3, 1.2, 1])

## Setup Steps

### 1. Tabelle erstellen (als postgres User)

```bash
sudo -u postgres psql swadocs <<EOF
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

-- Also grant CREATE permission for future tables
GRANT CREATE ON SCHEMA public TO swaagent;
EOF
```

### 2. Daten neu importieren

```bash
cd /mnt/c/Users/p355208/OneDrive\ -\ Dr.\ Ing.\ h.c.\ F.\ Porsche\ AG/Notebooks/Projects/AI/Arch_review/POC/MPC

# Mit --clear werden alte Daten gelöscht
.venv/bin/python import_to_db_hierarchical.py txts --clear
```

### 3. Testen

```bash
# Statistik anzeigen
PGPASSWORD='swaagent911' psql -h localhost -U swaagent -d swadocs -c "
SELECT
    (SELECT COUNT(*) FROM documents) as documents,
    (SELECT COUNT(*) FROM chunks) as chunks,
    (SELECT COUNT(*) FROM chunk_categories) as category_links;
"

# Beispiel: Alle Chunks in Kapitel 1 (inkl. Unterkapitel)
PGPASSWORD='swaagent911' psql -h localhost -U swaagent -d swadocs -c "
SELECT DISTINCT c.id, LEFT(c.chunk_text, 80) as preview, cc.category
FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category LIKE '1%'
ORDER BY cc.category, c.id
LIMIT 10;
"
```

## Neue Features

### 1. Chunks bei Kapitelgrenzen schneiden
Das Script `import_to_db_hierarchical.py` erkennt die Kapitelmarkierungen `###{number}[title]` und schneidet Chunks an diesen Grenzen.

### 2. Hierarchische Kategorien
Jeder Chunk wird zu allen Parent-Kategorien zugeordnet:
- Chunk in Kapitel "1.2.3" → zugeordnet zu ["1.2.3 Title", "1.2 Parent", "1 Main"]
- Chunk in Kapitel "1.2" → zugeordnet zu ["1.2 Title", "1 Main"]

### 3. Flexible Suche
Mit der neuen `chunk_categories` Tabelle können Sie:
- Alle Chunks in Hauptkapitel 1 finden: `WHERE category LIKE '1 %'`
- Alle Chunks in Kapitel 1.2.x finden: `WHERE category LIKE '1.2%'`
- Chunks auf bestimmter Ebene finden: `WHERE category_level = 2`

## Datenbankschema

```sql
documents (id, title, category, source_path, metadata, created_at)
    ↓ 1:N
chunks (id, document_id, chunk_text, embedding, chunk_index, created_at)
    ↓ N:M
chunk_categories (id, chunk_id, category, category_level, created_at)
```

## Beispiel SQL-Abfragen

### Alle Chunks mit ihren Kategorien
```sql
SELECT
    c.id,
    c.chunk_text,
    ARRAY_AGG(cc.category ORDER BY cc.category_level) as categories
FROM chunks c
LEFT JOIN chunk_categories cc ON c.id = cc.chunk_id
GROUP BY c.id, c.chunk_text
LIMIT 10;
```

### Chunks in bestimmter Kategorie-Hierarchie
```sql
SELECT c.id, c.chunk_text, cc.category
FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category LIKE '1.2%'
ORDER BY cc.category, c.id;
```

### Anzahl Chunks pro Kategorie
```sql
SELECT category, COUNT(*) as chunk_count
FROM chunk_categories
GROUP BY category
ORDER BY category;
```
