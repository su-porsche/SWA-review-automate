# Quick Start - Hierarchisches Import-System

## ✅ Das Script ist fertig und macht automatisch:

1. ✅ Prüft ob `chunk_categories` Tabelle existiert
2. ✅ Erstellt die Tabelle automatisch (falls Rechte vorhanden)
3. ✅ Schneidet Chunks bei Kapitelgrenzen
4. ✅ Ordnet jeden Chunk allen Parent-Kategorien zu
5. ✅ Maximale Chunk-Größe: 500 Zeichen

## 🚀 So starten Sie:

### Schritt 1: Tabelle erstellen (einmalig)

**Option A: Wenn Sie sudo haben**

Öffnen Sie ein **neues Terminal** und führen Sie aus:

```bash
sudo -u postgres psql swadocs
```

Dann kopieren Sie diesen SQL-Code hinein:

```sql
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

\q
```

**Option B: Alternative mit psql**

```bash
psql -h localhost -U postgres -d swadocs
# Dann SQL von oben einfügen
```

### Schritt 2: Daten importieren

```bash
cd /mnt/c/Users/p355208/OneDrive\ -\ Dr.\ Ing.\ h.c.\ F.\ Porsche\ AG/Notebooks/Projects/AI/Arch_review/POC/MPC

# Alte Daten löschen und neu importieren
.venv/bin/python import_to_db_hierarchical.py txts --clear
```

Das Script:
- ✓ Prüft automatisch die Tabelle
- ✓ Liest alle *_sections.jsonl Dateien
- ✓ Erstellt Chunks mit Kapitelhierarchie
- ✓ Befüllt chunk_categories automatisch

### Schritt 3: Testen

```bash
# Statistik
PGPASSWORD='swaagent911' psql -h localhost -U swaagent -d swadocs -c "
SELECT
    'Documents' as type, COUNT(*) as count FROM documents
UNION ALL
SELECT 'Chunks', COUNT(*) FROM chunks
UNION ALL
SELECT 'Category Links', COUNT(*) FROM chunk_categories;
"

# Beispiel: Chunks aus Kapitel 5 im Leitfaden-Dokument
PGPASSWORD='swaagent911' psql -h localhost -U swaagent -d swadocs -c "
SELECT DISTINCT
    c.id,
    d.metadata->>'pdf' as pdf,
    LEFT(c.chunk_text, 60) as chunk_preview,
    STRING_AGG(DISTINCT cc.category, ', ') as categories
FROM chunks c
JOIN documents d ON c.document_id = d.id
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category LIKE '5%'
  AND d.metadata->>'pdf' LIKE '%Leitfaden%'
GROUP BY c.id, d.metadata, c.chunk_text
ORDER BY c.id
LIMIT 10;
"
```

## 📝 Nützliche Abfragen

### Alle Chunks aus Kapitel 5 (inkl. Unterkapitel)

```sql
SELECT DISTINCT
    c.id,
    LEFT(c.chunk_text, 80) as chunk_preview,
    STRING_AGG(DISTINCT cc.category, ', ') as all_categories
FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category LIKE '5%'
GROUP BY c.id, c.chunk_text
ORDER BY c.id
LIMIT 20;
```

### Chunks aus Kapitel 5 in bestimmtem Dokument

```sql
SELECT DISTINCT
    c.id,
    d.title as document,
    LEFT(c.chunk_text, 80) as chunk_preview
FROM chunks c
JOIN documents d ON c.document_id = d.id
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category LIKE '5%'
  AND d.metadata->>'pdf' = 'Leitfaden Software Architektur Dokumentation (English) _ VR6.0.2.pdf'
ORDER BY c.id;
```

### Verfügbare Dokumente anzeigen

```sql
SELECT DISTINCT
    d.metadata->>'pdf' as pdf_name,
    COUNT(DISTINCT d.id) as sections,
    COUNT(c.id) as chunks
FROM documents d
LEFT JOIN chunks c ON d.id = c.document_id
GROUP BY d.metadata->>'pdf'
ORDER BY pdf_name;
```

### Kategorie-Hierarchie eines Chunks

```sql
SELECT
    c.id,
    LEFT(c.chunk_text, 60) as chunk_preview,
    ARRAY_AGG(cc.category ORDER BY cc.category_level) as category_hierarchy
FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE c.id = 100  -- Chunk-ID hier anpassen
GROUP BY c.id, c.chunk_text;
```

## 🔧 Troubleshooting

### "Table chunk_categories does not exist"

→ Sie müssen zuerst Schritt 1 ausführen (Tabelle erstellen)

### "Permission denied for schema public"

→ Der swaagent User kann die Tabelle nicht erstellen. Nutzen Sie `sudo -u postgres psql` (siehe Schritt 1)

### "No *_sections.jsonl files found"

→ Prüfen Sie den Pfad. Die JSONL-Dateien müssen im `txts/` Verzeichnis liegen

### Chunks werden nicht nach Kapiteln geschnitten

→ Prüfen Sie ob die TXT-Dateien die Markierungen `###{number}[title]` enthalten.
Falls nicht, führen Sie zuerst `pdf2text.py` aus

## 📊 Was passiert beim Import

1. **Dokumente erstellen**: Jede Section aus JSONL wird ein `documents` Eintrag
2. **Chunks erstellen**: Text wird in max. 500-Zeichen Chunks aufgeteilt
3. **Kategorien zuordnen**: Jeder Chunk bekommt Einträge in `chunk_categories`

**Beispiel:**

Chunk aus Sektion "5.2.3 Details"
→ Bekommt 3 Kategorie-Einträge:
- `5.2.3 Details` (level 1)
- `5.2 Subsection` (level 2)
- `5 Main Chapter` (level 3)

## 📚 Weitere Dokumentation

- [README_HIERARCHICAL_IMPORT.md](README_HIERARCHICAL_IMPORT.md) - Vollständige Dokumentation
- [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) - Detaillierte Setup-Anleitung
- [import_to_db_hierarchical.py](import_to_db_hierarchical.py) - Import-Script (mit Kommentaren)
