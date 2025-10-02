# Hierarchisches Kategorien-System - Implementierung

## Zusammenfassung der Änderungen

### ❌ Alte Probleme:
1. Chunks wurden nur nach Größe geschnitten, **nicht** nach Kapitelgrenzen
2. Chunks konnten **nicht** zu mehreren Kapiteln zugeordnet werden
3. Ein Chunk in "1.2.3" war nur diesem Kapitel zugeordnet, nicht auch "1.2" und "1"

### ✅ Neue Lösung:
1. ✅ Chunks werden bei Kapitelmarkierungen `###{number}[title]` geschnitten
2. ✅ Maximale Chunk-Größe bleibt 500 Zeichen
3. ✅ Jeder Chunk wird zu allen Parent-Kategorien zugeordnet via `chunk_categories` Tabelle

## Dateien

| Datei | Beschreibung |
|-------|--------------|
| [import_to_db_hierarchical.py](import_to_db_hierarchical.py) | Neues Import-Script mit Kapitel-Hierarchie |
| [CREATE_TABLE.sql](CREATE_TABLE.sql) | SQL für `chunk_categories` Tabelle |
| [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) | Detaillierte Setup-Anleitung |
| [setup_db.sh](setup_db.sh) | Bash-Script für automatisches Setup (benötigt sudo) |

## Quick Start

### Schritt 1: Tabelle erstellen

```bash
# Option A: Mit SQL-Datei
sudo -u postgres psql swadocs < CREATE_TABLE.sql

# Option B: Direkt
sudo -u postgres psql swadocs <<EOF
CREATE TABLE IF NOT EXISTS chunk_categories (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    category_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chunk_categories_chunk ON chunk_categories(chunk_id);
CREATE INDEX idx_chunk_categories_category ON chunk_categories(category);
GRANT SELECT, INSERT, UPDATE, DELETE ON chunk_categories TO swaagent;
GRANT USAGE, SELECT ON SEQUENCE chunk_categories_id_seq TO swaagent;
EOF
```

### Schritt 2: Daten importieren

```bash
# Alte Daten löschen und neu importieren
.venv/bin/python import_to_db_hierarchical.py txts --clear

# Oder: Nur neue Daten hinzufügen (ohne --clear)
.venv/bin/python import_to_db_hierarchical.py txts
```

### Schritt 3: Testen

```bash
# Statistik anzeigen
PGPASSWORD='swaagent911' psql -h localhost -U swaagent -d swadocs -c "
SELECT
    (SELECT COUNT(*) FROM documents) as documents,
    (SELECT COUNT(*) FROM chunks) as chunks,
    (SELECT COUNT(*) FROM chunk_categories) as category_links;
"

# Beispiel-Abfrage: Alle Chunks in Kapitel 1
PGPASSWORD='swaagent911' psql -h localhost -U swaagent -d swadocs -c "
SELECT DISTINCT
    c.id,
    LEFT(c.chunk_text, 60) as chunk_preview,
    ARRAY_AGG(cc.category) as all_categories
FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category LIKE '1%'
GROUP BY c.id, c.chunk_text
LIMIT 5;
"
```

## Wie es funktioniert

### 1. Kapitelmarkierungen im Text

Die [pdf2text.py](pdf2text.py) erstellt TXT-Dateien mit Markierungen:

```
###{1}[General Requirements]
This chapter describes...

###{1.1}[Introduction]
The introduction explains...

###{1.2}[Scope]
The scope defines...
```

### 2. Import mit Kapitel-Grenzen

[import_to_db_hierarchical.py](import_to_db_hierarchical.py) erkennt diese Markierungen:

```python
def create_chunks_with_chapters(text, metadata):
    # Findet alle ###-Markierungen
    markers = extract_chapter_markers(text)

    # Schneidet Chunks an Kapitelgrenzen
    # ODER bei 500 Zeichen (je nachdem was früher kommt)
    for chunk in split_at_boundaries(text, markers, max_size=500):
        yield chunk
```

**Beispiel:**
```
Kapitel 1.2 (800 Zeichen Text)
    ↓
Chunk 1: 0-500 Zeichen von 1.2
Chunk 2: 400-800 Zeichen von 1.2 (mit 100 Zeichen Overlap)
```

### 3. Hierarchische Kategorien

Jeder Chunk bekommt **alle** Parent-Kategorien:

```python
# Chunk in Kapitel 1.2.3
categories = get_categories(section, section_index)
# → ["1.2.3 Detailed Spec", "1.2 Requirements", "1 General"]

# Speichern in chunk_categories Tabelle
for level, category in enumerate(categories, 1):
    INSERT INTO chunk_categories (chunk_id, category, category_level)
    VALUES (chunk_id, category, level)
```

**Ergebnis in DB:**
| chunk_id | category | category_level |
|----------|----------|----------------|
| 42 | 1.2.3 Detailed Spec | 1 |
| 42 | 1.2 Requirements | 2 |
| 42 | 1 General | 3 |

## Vorteile

### Flexible Suche

```sql
-- Alle Chunks in Hauptkapitel 1 (inkl. Unterkapitel)
SELECT * FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category LIKE '1%';

-- Nur direkte Kinder von Kapitel 1 (nicht 1.1.1, etc.)
SELECT * FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category ~ '^1\.\d+ ';

-- Chunks auf bestimmter Hierarchie-Ebene
SELECT * FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category_level = 2;  -- Zweite Ebene (z.B. 1.1, 1.2, 2.1)
```

### Präzise Kontextsuche

Wenn ein Benutzer nach "Kapitel 1" fragt, findet das System:
- ✅ Chunks aus Kapitel 1 selbst
- ✅ Chunks aus allen Unterkapiteln (1.1, 1.2, 1.1.1, etc.)

## Datenbank-Schema

```
documents
    ↓ 1:N
chunks
    ↓ N:M
chunk_categories
```

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title TEXT,
    metadata JSONB,
    ...
);

CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    chunk_text TEXT,
    chunk_index INTEGER,
    ...
);

CREATE TABLE chunk_categories (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    category_level INTEGER,
    ...
);
```

## Nützliche SQL-Abfragen

### Chunks mit allen Kategorien
```sql
SELECT
    c.id,
    c.chunk_text,
    ARRAY_AGG(cc.category ORDER BY cc.category_level) as categories
FROM chunks c
LEFT JOIN chunk_categories cc ON c.id = cc.chunk_id
GROUP BY c.id, c.chunk_text;
```

### Anzahl Chunks pro Kategorie
```sql
SELECT
    category,
    COUNT(*) as chunk_count,
    AVG(category_level) as avg_level
FROM chunk_categories
GROUP BY category
ORDER BY category;
```

### Hierarchie-Statistik
```sql
SELECT
    category_level,
    COUNT(DISTINCT chunk_id) as unique_chunks,
    COUNT(DISTINCT category) as unique_categories
FROM chunk_categories
GROUP BY category_level
ORDER BY category_level;
```

## Nächste Schritte

Nach dem Setup können Sie:

1. **VS Code PostgreSQL Extension** installieren und DB browsen
2. **Embeddings erstellen** (nächster geplanter Schritt)
3. **RAG-System** mit hierarchischer Suche implementieren

## Fragen?

Siehe [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) für Details oder prüfen Sie die inline-Kommentare in [import_to_db_hierarchical.py](import_to_db_hierarchical.py).
