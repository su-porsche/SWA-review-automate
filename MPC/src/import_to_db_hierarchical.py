#!/usr/bin/env python3
"""
Improved import script with hierarchical category support.
- Chunks are cut at chapter boundaries (respecting max size)
- Each chunk is linked to all parent categories (e.g., chunk in 1.2.3 → belongs to 1.2.3, 1.2, and 1)
"""

import json
import re
import sys
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values


DB_CONFIG = {
    'host': 'localhost',
    'database': 'swadocs',
    'user': 'swaagent',
    'password': 'swaagent911',
    'port': 5432
}

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def extract_chapter_markers(text):
    """
    Extract chapter markers from text (e.g., ###{1.2}[Title])
    Returns list of (position, section_number, title)
    """
    pattern = r'###\{([^}]+)\}\[([^\]]+)\]'
    markers = []

    for match in re.finditer(pattern, text):
        markers.append({
            'position': match.start(),
            'section_number': match.group(1),
            'title': match.group(2),
            'full_marker': match.group(0)
        })

    return markers


def create_chunks_with_chapters(text, section_metadata, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Split text into chunks, respecting chapter boundaries.
    Each chunk knows which chapter(s) it belongs to.

    Returns: list of {'text': str, 'categories': [str], 'start_pos': int}
    """
    if not text or len(text) <= chunk_size:
        # Small text - one chunk with current section's categories
        return [{
            'text': text,
            'categories': section_metadata.get('categories', []),
            'start_pos': 0
        }] if text else []

    # Extract chapter markers
    markers = extract_chapter_markers(text)

    chunks = []
    start = 0
    current_categories = section_metadata.get('categories', [])

    while start < len(text):
        # Check if we're crossing a chapter boundary
        next_marker_pos = None
        next_marker = None

        for marker in markers:
            if marker['position'] > start and marker['position'] < start + chunk_size:
                next_marker_pos = marker['position']
                next_marker = marker
                break

        # Determine chunk end
        if next_marker_pos:
            # Cut at chapter boundary
            end = next_marker_pos
        else:
            # Normal chunk
            end = start + chunk_size

            # Try to break at word boundary
            if end < len(text):
                space_pos = text.rfind(' ', start, end)
                if space_pos > start:
                    end = space_pos

        # Extract chunk text
        chunk_text = text[start:end].strip()

        # Remove chapter markers from chunk text
        chunk_text_clean = re.sub(r'###\{[^}]+\}\[[^\]]+\]', '', chunk_text).strip()

        if chunk_text_clean:
            chunks.append({
                'text': chunk_text_clean,
                'categories': current_categories.copy(),
                'start_pos': start
            })

        # Move to next position
        if next_marker_pos and next_marker:
            # Update categories based on the marker we just encountered
            # This would require building the category hierarchy for the subchapter
            # For now, keep current categories
            start = end
        else:
            # Overlap for better context
            start = end - overlap if end < len(text) else end

    return chunks


def get_categories(section, section_index):
    """Build category hierarchy for a section."""
    categories = []
    current = section
    max_depth = 10

    for _ in range(max_depth):
        if not current:
            break

        num = current.get('section_number', '')
        title = current.get('title', '')

        if num:
            categories.append(f"{num} {title}")
        elif title:
            categories.append(title)

        parent_num = current.get('parent_number')
        current = section_index.get(parent_num) if parent_num else None

    return categories


def insert_chunk_with_categories(cursor, doc_id, chunk_data, chunk_index):
    """
    Insert a chunk and its category relationships.
    """
    # Insert chunk
    cursor.execute("""
        INSERT INTO chunks (document_id, chunk_text, chunk_index)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (doc_id, chunk_data['text'], chunk_index))

    chunk_id = cursor.fetchone()[0]

    # Insert category relationships
    categories = chunk_data['categories']
    if categories:
        category_data = [
            (chunk_id, cat, idx + 1)
            for idx, cat in enumerate(categories)
        ]

        execute_values(
            cursor,
            """INSERT INTO chunk_categories (chunk_id, category, category_level)
               VALUES %s""",
            category_data,
            template='(%s, %s, %s)'
        )

    return chunk_id


def process_jsonl(jsonl_path, conn):
    """Process one JSONL file."""
    print(f"\nProcessing: {jsonl_path}")

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        sections = [json.loads(line) for line in f]

    print(f"  Loaded {len(sections)} sections")

    # Build index
    section_index = {s['section_number']: s for s in sections if s.get('section_number')}

    cursor = conn.cursor()
    total_chunks = 0

    for i, section in enumerate(sections, 1):
        section_num = section['section_number']
        title = section['title']
        text = section['text']

        categories = get_categories(section, section_index)

        metadata = {
            'pdf': section.get('pdf', ''),
            'section_number': section_num,
            'title': title,
            'level': section.get('level', 1),
            'page_start': section.get('page_start', 0),
            'page_end': section.get('page_end', 0),
            'parent_number': section.get('parent_number'),
            'categories': categories
        }

        # Insert document
        cursor.execute("""
            INSERT INTO documents (title, category, source_path, metadata)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            f"{section_num} {title}" if section_num else title,
            categories[0] if categories else "General",
            str(jsonl_path),
            json.dumps(metadata)
        ))

        doc_id = cursor.fetchone()[0]

        # Create chunks with chapter awareness
        metadata['categories'] = categories
        chunks = create_chunks_with_chapters(text, metadata)

        # Insert chunks with categories
        for chunk_idx, chunk_data in enumerate(chunks):
            insert_chunk_with_categories(cursor, doc_id, chunk_data, chunk_idx)

        total_chunks += len(chunks)

        if i % 10 == 0 or i == len(sections):
            print(f"  Progress: {i}/{len(sections)} sections, {total_chunks} chunks")

    conn.commit()
    cursor.close()

    print(f"  ✓ Completed: {len(sections)} sections, {total_chunks} chunks")
    return total_chunks


def ensure_chunk_categories_table(conn):
    """Create chunk_categories table if it doesn't exist."""
    cursor = conn.cursor()

    print("Checking chunk_categories table...")

    # Check if table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'chunk_categories'
        );
    """)

    table_exists = cursor.fetchone()[0]

    if table_exists:
        print("  ✓ Table chunk_categories already exists")
        cursor.close()
        return

    print("  Creating chunk_categories table...")

    try:
        # Create table
        cursor.execute("""
            CREATE TABLE chunk_categories (
                id SERIAL PRIMARY KEY,
                chunk_id INTEGER REFERENCES chunks(id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                category_level INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX idx_chunk_categories_chunk
            ON chunk_categories(chunk_id)
        """)

        cursor.execute("""
            CREATE INDEX idx_chunk_categories_category
            ON chunk_categories(category)
        """)

        cursor.execute("""
            CREATE INDEX idx_chunk_categories_level
            ON chunk_categories(category_level)
        """)

        conn.commit()
        print("  ✓ Table chunk_categories created successfully")

    except psycopg2.Error as e:
        print(f"  ⚠️  Could not create table: {e}")
        print("  ℹ️  You may need to run: sudo -u postgres psql swadocs < CREATE_TABLE.sql")
        conn.rollback()
        raise

    cursor.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Import JSONL to PostgreSQL with hierarchical categories')
    parser.add_argument('jsonl_dir', help='Directory with *_sections.jsonl files')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before import')
    args = parser.parse_args()

    jsonl_dir = Path(args.jsonl_dir)
    if not jsonl_dir.exists():
        print(f"Error: Directory not found: {jsonl_dir}")
        sys.exit(1)

    jsonl_files = list(jsonl_dir.glob("*_sections.jsonl"))
    if not jsonl_files:
        print(f"No *_sections.jsonl files found in {jsonl_dir}")
        sys.exit(1)

    print(f"Found {len(jsonl_files)} file(s)")
    for f in jsonl_files:
        print(f"  - {f.name}")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("\n✓ Connected to database\n")

        # Ensure chunk_categories table exists
        ensure_chunk_categories_table(conn)

        if args.clear:
            print("⚠️  Clearing existing data...")
            cursor = conn.cursor()

            # Check if chunk_categories exists before truncating
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'chunk_categories'
                );
            """)
            has_categories = cursor.fetchone()[0]

            try:
                # Try TRUNCATE (faster but requires special permissions)
                if has_categories:
                    cursor.execute("TRUNCATE documents, chunks, chunk_categories RESTART IDENTITY CASCADE")
                else:
                    cursor.execute("TRUNCATE documents, chunks RESTART IDENTITY CASCADE")
            except psycopg2.Error:
                # Rollback failed transaction
                conn.rollback()

                # Fallback: DELETE (slower but works with standard permissions)
                print("  ℹ️  Using DELETE instead of TRUNCATE (no TRUNCATE permission)")
                if has_categories:
                    cursor.execute("DELETE FROM chunk_categories")
                cursor.execute("DELETE FROM chunks")
                cursor.execute("DELETE FROM documents")
                # Note: Cannot reset sequences without owner permissions
                # IDs will continue from last value, but that's okay

            conn.commit()
            cursor.close()
            print("✓ Data cleared\n")

        total = 0
        for jsonl_file in jsonl_files:
            total += process_jsonl(jsonl_file, conn)

        conn.close()

        print(f"\n{'='*60}")
        print(f"✓ Import completed!")
        print(f"  Total chunks created: {total}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
