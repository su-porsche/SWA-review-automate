#!/usr/bin/env python3
"""
Import JSONL sections into PostgreSQL vector database.
Creates chunks from section text with hierarchical chapter categorization.
"""

import sys
print("[STARTUP] Script starting...", flush=True)

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

print("[STARTUP] Importing psycopg2...", flush=True)
import psycopg2
from psycopg2.extras import execute_values
print("[STARTUP] Imports complete", flush=True)


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'swadocs',
    'user': 'swaagent',
    'password': 'swaagent911',
    'port': 5432
}

# Chunking configuration
CHUNK_SIZE = 500  # characters per chunk
CHUNK_OVERLAP = 100  # overlap between chunks


def create_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to split
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks

    Returns:
        List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence ending (. ! ?) followed by space or newline
            sentence_end = text.rfind('. ', start, end)
            if sentence_end == -1:
                sentence_end = text.rfind('.\n', start, end)
            if sentence_end == -1:
                sentence_end = text.rfind('! ', start, end)
            if sentence_end == -1:
                sentence_end = text.rfind('? ', start, end)

            if sentence_end > start:
                end = sentence_end + 1
            else:
                # Fallback to word boundary
                space_pos = text.rfind(' ', start, end)
                if space_pos > start:
                    end = space_pos

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position with overlap
        start = end - overlap if end < len(text) else end

    return chunks


def get_chapter_hierarchy(section_number: str, title: str) -> List[str]:
    """
    Get all chapter categories for a section (main chapter and all parent chapters).

    Args:
        section_number: Section number (e.g., "8.6.2")
        title: Section title

    Returns:
        List of categories from most specific to most general

    Example:
        "8.6.2" -> ["8.6.2 Real-time Requirements", "8.6 Timing Behaviour", "8 Process View"]
    """
    categories = []

    if not section_number:
        return [title] if title else ["General"]

    # Add current section
    categories.append(f"{section_number} {title}")

    # Parse section number and add parent levels
    parts = section_number.split('.')

    # For each parent level, we need to create category
    # We don't have parent titles, so we'll use simplified format
    for i in range(len(parts) - 1, 0, -1):
        parent_num = '.'.join(parts[:i])
        # Simplified parent category (actual title would need lookup)
        categories.append(f"Chapter {parent_num}")

    return categories


def build_section_index(sections: List[Dict]) -> Dict[str, Dict]:
    """
    Build fast lookup index for sections by section_number.

    Args:
        sections: List of all sections

    Returns:
        Dict mapping section_number to section dict
    """
    return {s['section_number']: s for s in sections if s.get('section_number')}


def get_full_chapter_hierarchy_fast(section: Dict, section_index: Dict[str, Dict]) -> List[str]:
    """
    Get full chapter hierarchy with actual titles using pre-built index.

    Args:
        section: Current section
        section_index: Pre-built section lookup index

    Returns:
        List of categories with full titles
    """
    categories = []
    current = section
    visited = set()  # Prevent infinite loops

    # Build hierarchy from current to root
    max_depth = 10  # Safety limit
    depth = 0

    while current and depth < max_depth:
        section_num = current.get('section_number', '')

        # Check for loops
        if section_num in visited:
            break
        if section_num:
            visited.add(section_num)

        title = current.get('title', '')

        if section_num:
            categories.append(f"{section_num} {title}")
        else:
            categories.append(title)

        # Find parent using index
        parent_num = current.get('parent_number')
        if parent_num and parent_num in section_index:
            current = section_index[parent_num]
        else:
            current = None

        depth += 1

    # Return from most specific to most general
    return categories


def import_jsonl_to_db(jsonl_path: str, conn) -> int:
    """
    Import JSONL file into database.

    Args:
        jsonl_path: Path to JSONL file
        conn: Database connection

    Returns:
        Number of chunks created
    """
    print(f"Processing: {jsonl_path}", flush=True)

    # Read all sections first for hierarchy lookup
    print(f"[TRACE] Reading JSONL...", flush=True)
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        sections = [json.loads(line) for line in f]
    print(f"[TRACE] Loaded {len(sections)} sections", flush=True)

    # Build section index for fast lookups
    print(f"[TRACE] Building section index...", flush=True)
    section_index = build_section_index(sections)
    print(f"[TRACE] Index built with {len(section_index)} entries", flush=True)

    # Get document info from path
    pdf_name = sections[0]['pdf'] if sections else Path(jsonl_path).stem

    print(f"[TRACE] Creating cursor...", flush=True)
    cursor = conn.cursor()
    total_chunks = 0

    print(f"[TRACE] Starting section loop...", flush=True)
    for idx, section in enumerate(sections, 1):
        if idx % 10 == 0 or idx == 1:
            print(f"[TRACE] Section {idx}/{len(sections)}: {section.get('section_number', 'N/A')}", flush=True)

        section_num = section['section_number']
        title = section['title']
        text = section['text']
        page_start = section['page_start']
        page_end = section['page_end']
        level = section['level']

        # Get full hierarchy with actual titles using fast index
        if idx == 1:
            print(f"[TRACE]   Getting categories...", flush=True)
        categories = get_full_chapter_hierarchy_fast(section, section_index)
        if idx == 1:
            print(f"[TRACE]   Got {len(categories)} categories", flush=True)

        # Create metadata
        metadata = {
            'pdf': pdf_name,
            'section_number': section_num,
            'title': title,
            'level': level,
            'page_start': page_start,
            'page_end': page_end,
            'parent_number': section.get('parent_number'),
            'categories': categories
        }

        if idx == 1:
            print(f"[TRACE]   Inserting document...", flush=True)
        # Insert document record
        cursor.execute("""
            INSERT INTO documents (title, category, source_path, metadata)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            f"{section_num} {title}" if section_num else title,
            categories[0] if categories else "General",  # Primary category
            jsonl_path,
            json.dumps(metadata)
        ))

        document_id = cursor.fetchone()[0]
        if idx == 1:
            print(f"[TRACE]   Document ID: {document_id}", flush=True)

        if idx == 1:
            print(f"[TRACE]   Creating chunks (text length: {len(text)})...", flush=True)
        # Create chunks from section text
        chunks = create_chunks(text)
        if idx == 1:
            print(f"[TRACE]   Created {len(chunks)} chunks", flush=True)

        # Prepare chunk data
        chunk_data = []
        for chunk_idx, chunk_text in enumerate(chunks):
            chunk_data.append((
                document_id,
                chunk_text,
                chunk_idx
            ))

        # Bulk insert chunks (without embeddings for now)
        if chunk_data:
            if idx == 1:
                print(f"[TRACE]   Inserting {len(chunk_data)} chunks...", flush=True)
            execute_values(
                cursor,
                """
                INSERT INTO chunks (document_id, chunk_text, chunk_index)
                VALUES %s
                """,
                chunk_data,
                template='(%s, %s, %s)'
            )
            if idx == 1:
                print(f"[TRACE]   Chunks inserted", flush=True)

        total_chunks += len(chunks)
        if idx == 1 or idx % 10 == 0:
            print(f"  ✓ Section {section_num or 'N/A'}: {title[:50]:50} - {len(chunks)} chunks", flush=True)

    print(f"[TRACE] All sections processed. Committing transaction...", flush=True)
    conn.commit()
    print(f"[TRACE] Transaction committed", flush=True)
    print(f"[TRACE] Closing cursor...", flush=True)
    cursor.close()
    print(f"[TRACE] Import completed", flush=True)

    return total_chunks


def process_directory(jsonl_dir: str):
    """
    Process all JSONL files in directory and import to database.

    Args:
        jsonl_dir: Directory containing JSONL files
    """
    print(f"[PROC] Processing directory: {jsonl_dir}", flush=True)
    jsonl_dir = Path(jsonl_dir)

    print(f"[PROC] Checking if directory exists...", flush=True)
    if not jsonl_dir.exists():
        print(f"Error: Directory not found: {jsonl_dir}")
        return

    # Find all JSONL files
    print(f"[PROC] Looking for *_sections.jsonl files...", flush=True)
    jsonl_files = list(jsonl_dir.glob("*_sections.jsonl"))
    print(f"[PROC] Found {len(jsonl_files)} files", flush=True)

    if not jsonl_files:
        print(f"No *_sections.jsonl files found in {jsonl_dir}")
        return

    print(f"Found {len(jsonl_files)} JSONL file(s)")
    for f in jsonl_files:
        print(f"  - {f.name}", flush=True)

    print(f"[PROC] Connecting to database: {DB_CONFIG['database']}@{DB_CONFIG['host']}", flush=True)

    try:
        # Connect to database
        print(f"[PROC] Attempting connection...", flush=True)
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"[PROC] Connection successful!", flush=True)
        print("Database connection established\n", flush=True)

        total_chunks = 0
        print(f"[PROC] Starting file loop, {len(jsonl_files)} files to process", flush=True)

        for idx, jsonl_file in enumerate(jsonl_files, 1):
            print(f"[PROC] File {idx}/{len(jsonl_files)}: {jsonl_file.name}", flush=True)
            try:
                chunks_created = import_jsonl_to_db(str(jsonl_file), conn)
                total_chunks += chunks_created
                print(f"  Total chunks: {chunks_created}\n")
            except Exception as e:
                print(f"Error processing {jsonl_file}: {e}")
                conn.rollback()

        conn.close()
        print(f"\n{'='*60}")
        print(f"Import completed successfully!")
        print(f"Total chunks created: {total_chunks}")
        print(f"{'='*60}")

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    print("[MAIN] Entering main function...", flush=True)

    import argparse
    print("[MAIN] argparse imported", flush=True)

    # Declare globals at the start
    global CHUNK_SIZE, CHUNK_OVERLAP

    print("[MAIN] Creating argument parser...", flush=True)
    parser = argparse.ArgumentParser(
        description='Import JSONL sections into PostgreSQL vector database'
    )
    parser.add_argument(
        'jsonl_dir',
        help='Directory containing *_sections.jsonl files'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=CHUNK_SIZE,
        help=f'Chunk size in characters (default: {CHUNK_SIZE})'
    )
    parser.add_argument(
        '--overlap',
        type=int,
        default=CHUNK_OVERLAP,
        help=f'Chunk overlap in characters (default: {CHUNK_OVERLAP})'
    )

    print("[MAIN] Parsing arguments...", flush=True)
    args = parser.parse_args()
    print(f"[MAIN] Arguments parsed: {args.jsonl_dir}", flush=True)

    # Update global config
    CHUNK_SIZE = args.chunk_size
    CHUNK_OVERLAP = args.overlap

    print(f"Chunk configuration: size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}\n", flush=True)

    print("[MAIN] Starting processing...", flush=True)
    process_directory(args.jsonl_dir)
    print("[MAIN] Processing complete!", flush=True)


if __name__ == '__main__':
    print("[ENTRY] Script entry point reached", flush=True)
    main()