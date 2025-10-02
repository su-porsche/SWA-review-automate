# Projekt-Struktur

## 📁 Verzeichnis-Übersicht

```
MPC/
│
├── 📂 src/                           # Haupt-Sourcecode
│   ├── pdf2text.py                   # PDF → TXT + JSONL Konvertierung
│   ├── import_to_db_hierarchical.py  # ⭐ Empfohlener hierarchischer Import
│   ├── import_to_db_simple.py        # Einfacher Import (alt, ohne Hierarchie)
│   ├── import_to_db.py               # Import (alt)
│   ├── main.py                       # Haupt-Einstiegspunkt
│   └── view_db.py                    # CLI für Datenbank-Ansicht
│
├── 📂 sql/                           # SQL-Skripte & Schema
│   ├── create_knowledgebase.sql      # ⭐ Komplettes DB-Schema
│   ├── CREATE_TABLE.sql              # Nur chunk_categories Tabelle
│   ├── example_queries.sql           # ⭐ 12 Beispiel-Abfragen
│   ├── grant_create_permissions.sql  # Rechte vergeben
│   └── migrate_add_categories.sql    # Migration (alt)
│
├── 📂 scripts/                       # Setup & Helper Scripts
│   ├── setup_db.sh                   # Datenbank-Setup automatisiert
│   ├── setup_and_import.sh           # Interaktiver Import-Assistent
│   ├── create_table_once.sh          # Einmalige Tabellen-Erstellung
│   ├── setup_categories_table.py     # Python Setup-Helper
│   └── run_sql_as_postgres.py        # SQL als postgres User ausführen
│
├── 📂 docs/                          # Dokumentation
│   ├── QUICK_START.md                # ⭐ Schnellstart in 3 Schritten
│   ├── ABSCHLUSS.md                  # Feature-Übersicht & Zusammenfassung
│   ├── README_HIERARCHICAL_IMPORT.md # ⭐ Detaillierte Doku zum System
│   └── SETUP_INSTRUCTIONS.md         # Ausführliche Setup-Anleitung
│
├── 📂 examples/                      # Beispiele & Workflows
│   ├── example_workflow.sh           # Kompletter Workflow als Script
│   └── example_queries.py            # Python-Beispiele für DB-Abfragen
│
├── 📂 tests/                         # Test & Debug Files
│   ├── debug_*.py                    # Debug-Skripte für Entwicklung
│   ├── test_*.py                     # Test-Skripte
│   └── quick_test.py                 # Schnelltest
│
├── 📂 pdfs/                          # 📥 INPUT: PDF-Dateien
│   └── *.pdf                         # Ihre PDF-Dokumente
│
├── 📂 txts/                          # 📤 OUTPUT: Konvertierte Dateien
│   ├── *.txt                         # Volltext mit Kapitelmarkierungen
│   └── *_sections.jsonl              # Metadata pro Kapitel
│
├── 📂 .venv/                         # Python Virtual Environment
│
├── README.md                         # ⭐ Haupt-README
├── STRUCTURE.md                      # Diese Datei
├── .gitignore                        # Git Ignore Rules
├── requirements.txt                  # Python Dependencies
└── ignore_sections.json              # Konfiguration: Ignorierte Sektionen
```

## 🎯 Wichtigste Dateien

### Für den Start:

1. **[README.md](README.md)** - Projekt-Übersicht & Quick Start
2. **[docs/QUICK_START.md](docs/QUICK_START.md)** - Schritt-für-Schritt Anleitung
3. **[sql/example_queries.sql](sql/example_queries.sql)** - Fertige SQL-Abfragen

### Für die Nutzung:

- **[src/pdf2text.py](src/pdf2text.py)** - PDF-Konvertierung
- **[src/import_to_db_hierarchical.py](src/import_to_db_hierarchical.py)** - Datenbank-Import
- **[src/view_db.py](src/view_db.py)** - Datenbank durchsuchen

### Für Setup:

- **[sql/create_knowledgebase.sql](sql/create_knowledgebase.sql)** - Datenbank-Schema
- **[scripts/setup_and_import.sh](scripts/setup_and_import.sh)** - Automatisierter Setup

## 📋 Workflow

```
1. PDF-Dateien
   ↓
   [pdf2text.py]
   ↓
2. TXT + JSONL
   ↓
   [import_to_db_hierarchical.py]
   ↓
3. PostgreSQL DB
   ↓
   [view_db.py oder SQL]
   ↓
4. Chunks mit Kategorien
```

## 🔍 Dateiarten

### Python-Scripts (`.py`)

| Typ | Beschreibung | Beispiele |
|-----|--------------|-----------|
| **src/** | Produktions-Code | pdf2text.py, import_to_db_hierarchical.py |
| **scripts/** | Setup & Helper | setup_categories_table.py |
| **examples/** | Beispiel-Code | example_queries.py |
| **tests/** | Debug & Tests | debug_*.py, test_*.py |

### SQL-Dateien (`.sql`)

| Datei | Zweck |
|-------|-------|
| **create_knowledgebase.sql** | Komplettes Schema inkl. chunk_categories |
| **CREATE_TABLE.sql** | Nur chunk_categories Tabelle erstellen |
| **example_queries.sql** | 12 fertige Beispiel-Abfragen |
| **migrate_add_categories.sql** | Migration für bestehende DBs |

### Shell-Scripts (`.sh`)

| Datei | Zweck |
|-------|-------|
| **setup_db.sh** | Automatisches DB-Setup |
| **setup_and_import.sh** | Interaktiver Import-Wizard |
| **example_workflow.sh** | Kompletter Workflow-Durchlauf |

### Dokumentation (`.md`)

| Datei | Zielgruppe |
|-------|-----------|
| **README.md** | Alle - Projekt-Übersicht |
| **QUICK_START.md** | Neue Nutzer - Schnelleinstieg |
| **README_HIERARCHICAL_IMPORT.md** | Entwickler - Technische Details |
| **SETUP_INSTRUCTIONS.md** | Admins - Detailliertes Setup |
| **STRUCTURE.md** | Alle - Diese Datei |

## 🔄 Datenfluss

### 1. PDF → Text

```
pdfs/document.pdf
    → [pdf2text.py]
    → txts/document.txt              (Volltext mit Markierungen)
    → txts/document_sections.jsonl   (Metadata)
```

### 2. Text → Datenbank

```
txts/*.jsonl
    → [import_to_db_hierarchical.py]
    → PostgreSQL:
        - documents (Kapitel)
        - chunks (Text-Segmente)
        - chunk_categories (Hierarchie)
```

### 3. Datenbank → Abfragen

```
PostgreSQL
    → [SQL oder view_db.py]
    → Ergebnisse
```

## 📦 Dependencies

Siehe [requirements.txt](requirements.txt):

- `PyMuPDF` - PDF-Verarbeitung
- `psycopg2-binary` - PostgreSQL-Zugriff
- `pgvector` - Vector Extension (für Embeddings)

## 🎓 Verwendung nach Typ

### Als Entwickler:

```bash
# Code anpassen
vim src/import_to_db_hierarchical.py

# Testen
.venv/bin/python tests/quick_test.py

# Debuggen
.venv/bin/python tests/debug_import.py
```

### Als Nutzer:

```bash
# PDFs konvertieren
.venv/bin/python src/pdf2text.py pdfs/

# Importieren
.venv/bin/python src/import_to_db_hierarchical.py txts --clear

# Abfragen
.venv/bin/python src/view_db.py search "security"
```

### Als Admin:

```bash
# Setup
bash scripts/setup_db.sh

# Datenbank prüfen
PGPASSWORD='swaagent911' psql -h localhost -U swaagent -d swadocs
```

## 🗂️ Aufräum-Hinweise

### Zu behalten:

- `src/` - Haupt-Code
- `sql/` - Schema & Queries
- `docs/` - Dokumentation
- `examples/` - Beispiele

### Optional zu löschen:

- `tests/debug_*.py` - Nur für Entwicklung
- `scripts/*_backup.py` - Backup-Dateien
- `txts/*.txt` - Nach Import (regenerierbar)

### Niemals löschen:

- `.venv/` - Python Environment
- `requirements.txt` - Dependencies
- `README.md` - Hauptdokumentation
- `pdfs/` - Original-Dokumente

## 📖 Weitere Infos

- Technische Details: [docs/README_HIERARCHICAL_IMPORT.md](docs/README_HIERARCHICAL_IMPORT.md)
- Schnellstart: [docs/QUICK_START.md](docs/QUICK_START.md)
- Hauptdoku: [README.md](README.md)
