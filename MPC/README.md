# PDF to Knowledge Base - Hierarchical Import System

Automatisiertes System zum Extrahieren von PDF-Inhalten und Importieren in eine PostgreSQL-Vektordatenbank mit hierarchischer Kategorisierung.

## 🎯 Features

- **PDF-zu-Text Konvertierung** mit Kapitel-Erkennung
- **Hierarchische Kategorien**: Chunks gehören zu allen Parent-Kapiteln
- **Chunks bei Kapitelgrenzen**: Intelligentes Schneiden an Kapitelmarkierungen
- **PostgreSQL + pgvector**: Vector-Datenbank für spätere Embeddings
- **Flexible Suche**: SQL-Abfragen über Kategorie-Hierarchien

## 📁 Projekt-Struktur

```
MPC/
├── src/                          # Haupt-Sourcecode
│   ├── pdf2text.py              # PDF → TXT + JSONL Konvertierung
│   ├── import_to_db_hierarchical.py  # Hierarchischer Import (EMPFOHLEN)
│   ├── import_to_db_simple.py   # Einfacher Import (alt)
│   ├── main.py                  # Haupt-Einstiegspunkt
│   └── view_db.py               # Datenbank-Viewer CLI
│
├── sql/                         # SQL-Skripte
│   ├── create_knowledgebase.sql # Datenbank-Schema (komplett)
│   ├── CREATE_TABLE.sql         # Nur chunk_categories Tabelle
│   └── example_queries.sql      # 12 Beispiel-Abfragen
│
├── scripts/                     # Setup & Helper Scripts
│   ├── setup_db.sh              # Datenbank Setup
│   └── setup_and_import.sh      # Interaktiver Import
│
├── docs/                        # Dokumentation
│   ├── QUICK_START.md           # Schnellstart-Anleitung
│   ├── ABSCHLUSS.md             # Zusammenfassung & Features
│   ├── README_HIERARCHICAL_IMPORT.md  # Detaillierte Doku
│   └── SETUP_INSTRUCTIONS.md    # Setup-Anleitung
│
├── tests/                       # Test & Debug Files
│   ├── debug_*.py               # Debug-Skripte
│   └── test_*.py                # Test-Skripte
│
├── data/                        # Daten-Verzeichnis
│   ├── pdfs/                    # Input: PDF-Dateien
│   └── txts/                    # Output: TXT + JSONL Dateien
└── .venv/                       # Python Virtual Environment
```

## 🚀 Quick Start

### 1. PDF zu Text konvertieren

```bash
.venv/bin/python src/pdf2text.py data/pdfs/
```

**Output:**
- `data/txts/*.txt` - Volltext mit Kapitelmarkierungen `###{number}[title]`
- `data/txts/*_sections.jsonl` - Metadata pro Kapitel

### 2. Datenbank erstellen (einmalig)

```bash
# Als postgres User
sudo -u postgres psql swadocs < sql/CREATE_TABLE.sql
```

### 3. Daten importieren

```bash
# Mit hierarchischen Kategorien (empfohlen)
.venv/bin/python src/import_to_db_hierarchical.py data/txts --clear
```

### 4. Daten abfragen

```bash
# Alle Chunks aus Kapitel 5
PGPASSWORD='swaagent911' psql -h localhost -U swaagent -d swadocs -c "
SELECT DISTINCT c.id, LEFT(c.chunk_text, 80) as preview
FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category LIKE '5%'
LIMIT 10;
"

# Oder mit Python CLI
.venv/bin/python src/view_db.py stats
.venv/bin/python src/view_db.py search "security"
```

## 📊 Datenbank-Schema

```
documents (1) ----< (N) chunks (N) >----< (M) chunk_categories
```

**Beispiel:**
```
Chunk in Sektion 5.2.3
→ Kategorien: ["5.2.3 Details", "5.2 Subsection", "5 Infrastructure View"]
```

## 🔍 Wichtige Dateien

| Datei | Beschreibung |
|-------|-------------|
| `src/pdf2text.py` | PDF-Konvertierung mit Kapitel-Erkennung |
| `src/import_to_db_hierarchical.py` | Import mit Hierarchie-Support |
| `sql/example_queries.sql` | 12 fertige SQL-Beispiele |
| `docs/QUICK_START.md` | Schritt-für-Schritt Anleitung |

## 💡 Beispiel-Abfragen

### Chunks aus Kapitel 5 (inkl. Unterkapitel)

```sql
SELECT DISTINCT c.id, cc.category, LEFT(c.chunk_text, 80)
FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category LIKE '5%';
```

### Chunks aus bestimmtem Dokument + Kapitel

```sql
SELECT DISTINCT c.id, LEFT(c.chunk_text, 80)
FROM chunks c
JOIN documents d ON c.document_id = d.id
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category LIKE '5%'
  AND d.metadata->>'pdf' LIKE '%Leitfaden%';
```

### Hierarchie eines Chunks

```sql
SELECT ARRAY_AGG(cc.category ORDER BY cc.category_level) as hierarchy
FROM chunk_categories cc
WHERE chunk_id = 1443;
```

**Mehr Beispiele:** Siehe [`sql/example_queries.sql`](sql/example_queries.sql)

## 🛠️ Technologie-Stack

- **Python 3.12+** mit PyMuPDF (fitz)
- **PostgreSQL 14+** mit pgvector Extension
- **psycopg2** für DB-Zugriff
- **regex** für Kapitel-Erkennung

## 📖 Dokumentation

- **[Quick Start](docs/QUICK_START.md)** - Schnelleinstieg in 3 Schritten
- **[Hierarchical Import](docs/README_HIERARCHICAL_IMPORT.md)** - Wie das System funktioniert
- **[Setup Instructions](docs/SETUP_INSTRUCTIONS.md)** - Detaillierte Setup-Anleitung
- **[Abschluss](docs/ABSCHLUSS.md)** - Feature-Übersicht & Zusammenfassung

## 🎓 Verwendung

### PDF konvertieren

```bash
# Alle PDFs im Verzeichnis
.venv/bin/python src/pdf2text.py data/pdfs/

# Einzelne PDF
.venv/bin/python src/pdf2text.py data/pdfs/my_document.pdf
```

### Import mit verschiedenen Optionen

```bash
# Neu importieren (löscht alte Daten)
.venv/bin/python src/import_to_db_hierarchical.py data/txts --clear

# Hinzufügen (behält alte Daten)
.venv/bin/python src/import_to_db_hierarchical.py data/txts
```

### Datenbank durchsuchen

```bash
# Statistik
.venv/bin/python src/view_db.py stats

# Dokumente auflisten
.venv/bin/python src/view_db.py list 10

# Bestimmtes Dokument anzeigen
.venv/bin/python src/view_db.py show 123

# Suche
.venv/bin/python src/view_db.py search "architecture"
```

## 🔧 Konfiguration

### Datenbank-Verbindung

In den Python-Skripten (`src/*.py`):

```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'swadocs',
    'user': 'swaagent',
    'password': 'swaagent911',
    'port': 5432
}
```

### Chunk-Größe anpassen

In `src/import_to_db_hierarchical.py`:

```python
CHUNK_SIZE = 500      # Maximale Chunk-Größe
CHUNK_OVERLAP = 100   # Überlappung zwischen Chunks
```

## 📈 Nächste Schritte

1. **Embeddings erstellen**: Vector-Embeddings für Chunks generieren
2. **RAG-System**: Retrieval-Augmented Generation implementieren
3. **API**: REST API für Chunk-Suche
4. **Frontend**: Web-Interface für Suche und Exploration

## 🤝 Contributing

Siehe Test-Dateien in [`tests/`](tests/) für Beispiele zum Testen neuer Features.

## 📝 License

Internes Projekt - Porsche AG

## 🐛 Troubleshooting

### "Permission denied for table chunk_categories"

→ Führen Sie [`sql/CREATE_TABLE.sql`](sql/CREATE_TABLE.sql) als postgres User aus

### "No *_sections.jsonl files found"

→ Führen Sie zuerst `src/pdf2text.py` aus

### Import hängt

→ Nutzen Sie `--clear` Option oder prüfen Sie DB-Verbindung

**Mehr Details:** Siehe [`docs/QUICK_START.md`](docs/QUICK_START.md)
