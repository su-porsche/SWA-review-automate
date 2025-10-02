#!/usr/bin/env python3
"""
Interaktives Tool zum Durchsuchen der Vector-Datenbank.
"""

import psycopg2
import json
import sys

DB_CONFIG = {
    'host': 'localhost',
    'database': 'swadocs',
    'user': 'swaagent',
    'password': 'swaagent911'
}

def get_stats(cursor):
    """Zeige Statistiken."""
    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM chunks")
    chunk_count = cursor.fetchone()[0]
    
    print(f"\n📊 Statistik:")
    print(f"   Dokumente: {doc_count}")
    print(f"   Chunks: {chunk_count}")

def list_documents(cursor, limit=20):
    """Liste Dokumente."""
    cursor.execute(f"""
        SELECT d.id, d.title, d.category,
               (SELECT COUNT(*) FROM chunks WHERE document_id = d.id) as chunks
        FROM documents d
        ORDER BY d.id DESC
        LIMIT {limit}
    """)
    
    print(f"\n📄 Dokumente (letzte {limit}):")
    print(f"   {'ID':5} | {'Titel':50} | {'Kategorie':30} | Chunks")
    print(f"   {'-'*5}-+-{'-'*50}-+-{'-'*30}-+-------")
    
    for doc_id, title, cat, chunks in cursor.fetchall():
        title_short = (title[:47] + '...') if len(title) > 50 else title
        cat_short = (cat[:27] + '...') if len(cat) > 30 else cat
        print(f"   {doc_id:5} | {title_short:50} | {cat_short:30} | {chunks:6}")

def show_document(cursor, doc_id):
    """Zeige ein Dokument im Detail."""
    cursor.execute("""
        SELECT d.id, d.title, d.category, d.source_path, d.metadata, d.created_at
        FROM documents d
        WHERE d.id = %s
    """, (doc_id,))
    
    row = cursor.fetchone()
    if not row:
        print(f"❌ Dokument ID {doc_id} nicht gefunden")
        return
    
    doc_id, title, category, source, metadata_str, created = row
    metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
    
    print(f"\n" + "="*80)
    print(f"📄 Dokument ID: {doc_id}")
    print("="*80)
    print(f"Titel: {title}")
    print(f"Kategorie: {category}")
    print(f"Quelle: {source}")
    print(f"Erstellt: {created}")
    
    print(f"\n📋 Metadaten:")
    for key, value in metadata.items():
        if key == 'categories':
            print(f"  {key}:")
            for cat in value:
                print(f"    → {cat}")
        else:
            print(f"  {key}: {value}")
    
    # Chunks
    cursor.execute("""
        SELECT id, chunk_text, chunk_index
        FROM chunks
        WHERE document_id = %s
        ORDER BY chunk_index
    """, (doc_id,))
    
    chunks = cursor.fetchall()
    print(f"\n📦 Chunks ({len(chunks)} gesamt):")
    
    for chunk_id, text, idx in chunks:
        print(f"\n  Chunk {idx} (ID: {chunk_id}):")
        # Zeige erste 200 Zeichen
        preview = text[:200].replace('\n', ' ')
        print(f"  {preview}...")
        if len(text) > 200:
            print(f"  (... {len(text) - 200} weitere Zeichen)")

def search_documents(cursor, search_term):
    """Suche nach Dokumenten."""
    cursor.execute("""
        SELECT d.id, d.title, d.category
        FROM documents d
        WHERE d.title ILIKE %s OR d.category ILIKE %s
        ORDER BY d.id
    """, (f'%{search_term}%', f'%{search_term}%'))
    
    results = cursor.fetchall()
    print(f"\n🔍 Suchergebnisse für '{search_term}': {len(results)} gefunden")
    
    if results:
        print(f"   {'ID':5} | {'Titel':60} | {'Kategorie':30}")
        print(f"   {'-'*5}-+-{'-'*60}-+-{'-'*30}")
        for doc_id, title, cat in results[:20]:
            title_short = (title[:57] + '...') if len(title) > 60 else title
            cat_short = (cat[:27] + '...') if len(cat) > 30 else cat
            print(f"   {doc_id:5} | {title_short:60} | {cat_short:30}")
        
        if len(results) > 20:
            print(f"\n   ... und {len(results) - 20} weitere Ergebnisse")

def main():
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python view_db.py stats              - Zeige Statistiken")
        print("  python view_db.py list [N]           - Liste N Dokumente (default: 20)")
        print("  python view_db.py show <ID>          - Zeige Dokument mit ID")
        print("  python view_db.py search <Begriff>   - Suche nach Begriff")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        if command == 'stats':
            get_stats(cursor)
        
        elif command == 'list':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            list_documents(cursor, limit)
        
        elif command == 'show':
            if len(sys.argv) < 3:
                print("❌ Bitte Dokument-ID angeben: python view_db.py show <ID>")
                sys.exit(1)
            doc_id = int(sys.argv[2])
            show_document(cursor, doc_id)
        
        elif command == 'search':
            if len(sys.argv) < 3:
                print("❌ Bitte Suchbegriff angeben: python view_db.py search <Begriff>")
                sys.exit(1)
            search_term = ' '.join(sys.argv[2:])
            search_documents(cursor, search_term)
        
        else:
            print(f"❌ Unbekannter Befehl: {command}")
            sys.exit(1)
        
        cursor.close()
        conn.close()
    
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
