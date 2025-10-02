#!/bin/bash
# Beispiel-Workflow: Von PDF bis zur Datenbank-Abfrage

echo "========================================="
echo "  PDF to Knowledge Base - Workflow"
echo "========================================="
echo ""

# Schritt 1: PDF zu Text konvertieren
echo "📄 Schritt 1: PDF konvertieren..."
.venv/bin/python src/pdf2text.py data/pdfs/

# Schritt 2: In Datenbank importieren
echo ""
echo "💾 Schritt 2: In Datenbank importieren..."
.venv/bin/python src/import_to_db_hierarchical.py data/txts --clear

# Schritt 3: Statistik anzeigen
echo ""
echo "📊 Schritt 3: Datenbank-Statistik..."
.venv/bin/python src/view_db.py stats

# Schritt 4: Beispiel-Abfrage
echo ""
echo "🔍 Schritt 4: Beispiel-Abfrage - Chunks aus Kapitel 5..."
PGPASSWORD='swaagent911' psql -h localhost -U swaagent -d swadocs -c "
SELECT COUNT(*) as chunk_count
FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category LIKE '5%';
"

echo ""
echo "✅ Workflow abgeschlossen!"
echo ""
echo "Weitere Abfragen: sql/example_queries.sql"
echo "Dokumentation: docs/QUICK_START.md"
