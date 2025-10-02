#!/usr/bin/env python3
"""
Beispiel-Abfragen für die Knowledge Base
Zeigt verschiedene Möglichkeiten, Chunks hierarchisch zu suchen
"""

import psycopg2
import sys

DB_CONFIG = {
    'host': 'localhost',
    'database': 'swadocs',
    'user': 'swaagent',
    'password': 'swaagent911',
    'port': 5432
}


def example_1_all_from_chapter_5():
    """Alle Chunks aus Kapitel 5 (inkl. Unterkapitel)"""
    print("\n📚 Beispiel 1: Alle Chunks aus Kapitel 5\n")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            c.id,
            LEFT(c.chunk_text, 80) as preview,
            STRING_AGG(DISTINCT cc.category, ' | ') as categories
        FROM chunks c
        JOIN chunk_categories cc ON c.id = cc.chunk_id
        WHERE cc.category LIKE '5%'
        GROUP BY c.id, c.chunk_text
        ORDER BY c.id
        LIMIT 5
    """)

    for row in cursor.fetchall():
        print(f"Chunk {row[0]}")
        print(f"  Preview: {row[1]}")
        print(f"  Categories: {row[2]}")
        print()

    cursor.close()
    conn.close()


def example_2_specific_document():
    """Chunks aus Kapitel 5 in einem bestimmten Dokument"""
    print("\n📄 Beispiel 2: Kapitel 5 in Leitfaden VR6.0.2\n")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            c.id,
            d.metadata->>'section_number' as section,
            LEFT(c.chunk_text, 80) as preview
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        JOIN chunk_categories cc ON c.id = cc.chunk_id
        WHERE cc.category LIKE '5%'
          AND d.metadata->>'pdf' LIKE '%VR6.0.2%'
        ORDER BY c.id
        LIMIT 5
    """)

    for row in cursor.fetchall():
        print(f"Chunk {row[0]} (Section {row[1]})")
        print(f"  {row[2]}")
        print()

    cursor.close()
    conn.close()


def example_3_hierarchy():
    """Hierarchie eines Chunks anzeigen"""
    print("\n🌳 Beispiel 3: Hierarchie eines Chunks\n")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Finde einen Chunk aus Kapitel 5
    cursor.execute("""
        SELECT DISTINCT c.id
        FROM chunks c
        JOIN chunk_categories cc ON c.id = cc.chunk_id
        WHERE cc.category LIKE '5%'
        LIMIT 1
    """)

    chunk_id = cursor.fetchone()
    if not chunk_id:
        print("Keine Chunks in Kapitel 5 gefunden")
        return

    chunk_id = chunk_id[0]

    cursor.execute("""
        SELECT
            c.id,
            LEFT(c.chunk_text, 60) as preview,
            ARRAY_AGG(cc.category ORDER BY cc.category_level) as hierarchy
        FROM chunks c
        JOIN chunk_categories cc ON c.id = cc.chunk_id
        WHERE c.id = %s
        GROUP BY c.id, c.chunk_text
    """, (chunk_id,))

    row = cursor.fetchone()
    print(f"Chunk {row[0]}")
    print(f"Preview: {row[1]}")
    print(f"Hierarchie: {' → '.join(row[2])}")
    print()

    cursor.close()
    conn.close()


def example_4_text_search():
    """Volltextsuche mit Kategorie-Filter"""
    print("\n🔍 Beispiel 4: Suche nach 'security' in Kapitel 5\n")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            c.id,
            cc.category,
            LEFT(c.chunk_text, 100) as preview
        FROM chunks c
        JOIN chunk_categories cc ON c.id = cc.chunk_id
        WHERE c.chunk_text ILIKE '%security%'
          AND cc.category LIKE '5%'
        ORDER BY c.id
        LIMIT 3
    """)

    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"Chunk {row[0]} ({row[1]})")
            print(f"  {row[2]}")
            print()
    else:
        print("Keine Chunks mit 'security' in Kapitel 5 gefunden")

    cursor.close()
    conn.close()


def example_5_statistics():
    """Statistik über Kategorien"""
    print("\n📊 Beispiel 5: Statistik über Kapitel 5\n")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            cc.category,
            COUNT(DISTINCT c.id) as chunk_count
        FROM chunks c
        JOIN chunk_categories cc ON c.id = cc.chunk_id
        WHERE cc.category LIKE '5%'
        GROUP BY cc.category
        ORDER BY cc.category
    """)

    print("Kategorie                                    | Chunks")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"{row[0]:45} | {row[1]:6}")

    cursor.close()
    conn.close()


def main():
    print("=" * 70)
    print("  Knowledge Base - Beispiel-Abfragen")
    print("=" * 70)

    try:
        example_1_all_from_chapter_5()
        example_2_specific_document()
        example_3_hierarchy()
        example_4_text_search()
        example_5_statistics()

        print("\n✅ Alle Beispiele erfolgreich ausgeführt!")
        print("\nWeitere SQL-Beispiele: sql/example_queries.sql")

    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
