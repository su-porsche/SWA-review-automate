#!/usr/bin/env python3
"""
Simplified import script that works without deadlocks.
Import JSONL sections into PostgreSQL vector database.
"""

import json
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


def create_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    if not text or len(text) <= chunk_size:
        return [text] if text else []
   
    chunks = []
    start = 0
   
    while start < len(text):
        end = start + chunk_size
       
        if end < len(text):
            space_pos = text.rfind(' ', start, end)
            if space_pos > start:
                end = space_pos
       
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
       
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
       
        # Create and insert chunks
        chunks = create_chunks(text)
        chunk_data = [(doc_id, chunk, idx) for idx, chunk in enumerate(chunks)]
       
        if chunk_data:
            execute_values(
                cursor,
                "INSERT INTO chunks (document_id, chunk_text, chunk_index) VALUES %s",
                chunk_data,
                template='(%s, %s, %s)'
            )
       
        total_chunks += len(chunks)
       
        if i % 10 == 0 or i == len(sections):
            print(f"  Progress: {i}/{len(sections)} sections, {total_chunks} chunks")
   
    conn.commit()
    cursor.close()
   
    print(f"  ✓ Completed: {len(sections)} sections, {total_chunks} chunks")
    return total_chunks


def main():
    import argparse
   
    parser = argparse.ArgumentParser(description='Import JSONL to PostgreSQL')
    parser.add_argument('jsonl_dir', help='Directory with *_sections.jsonl files')
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
        sys.exit(1)


if __name__ == '__main__':
    main()
