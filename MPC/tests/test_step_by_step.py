#!/usr/bin/env python3
"""Test import_to_db step by step with timeouts."""

import json
import sys
import signal
from pathlib import Path

# Timeout handler
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Step took too long!")

signal.signal(signal.SIGALRM, timeout_handler)

def test_with_timeout(func, timeout_sec, step_name):
    """Run function with timeout."""
    print(f"\n[TEST] {step_name}...", flush=True)
    signal.alarm(timeout_sec)
    try:
        result = func()
        signal.alarm(0)  # Cancel alarm
        print(f"[TEST] ✓ {step_name} completed", flush=True)
        return result
    except TimeoutError:
        print(f"[TEST] ✗ {step_name} TIMEOUT after {timeout_sec}s", flush=True)
        sys.exit(1)
    except Exception as e:
        signal.alarm(0)
        print(f"[TEST] ✗ {step_name} failed: {e}", flush=True)
        sys.exit(1)

# Step 1: Import psycopg2
def step1_import():
    import psycopg2
    from psycopg2.extras import execute_values
    return psycopg2, execute_values

psycopg2, execute_values = test_with_timeout(step1_import, 5, "Import psycopg2")

# Step 2: Connect to database
def step2_connect():
    conn = psycopg2.connect(
        host='localhost',
        database='swadocs',
        user='swaagent',
        password='swaagent911'
    )
    return conn

conn = test_with_timeout(step2_connect, 5, "Connect to database")

# Step 3: Read JSONL file
def step3_read_jsonl():
    jsonl_path = "txts_test/Leitfaden Software Architektur Dokumentation (English) _ VR6.0.2_sections.jsonl"
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        sections = [json.loads(line) for line in f]
    print(f"  Loaded {len(sections)} sections", flush=True)
    return sections

sections = test_with_timeout(step3_read_jsonl, 5, "Read JSONL file")

# Step 4: Test get_full_chapter_hierarchy with first section
def step4_test_hierarchy():
    from import_to_db import get_full_chapter_hierarchy

    # Test with first section
    section = sections[0]
    print(f"  Testing section: {section['section_number']} {section['title']}", flush=True)

    categories = get_full_chapter_hierarchy(section, sections)
    print(f"  Categories: {len(categories)}", flush=True)
    for cat in categories[:3]:
        print(f"    - {cat}", flush=True)
    return categories

print("\n" + "="*60)
print("Testing get_full_chapter_hierarchy - THIS IS THE SUSPECTED DEADLOCK")
print("="*60)
categories = test_with_timeout(step4_test_hierarchy, 10, "Test hierarchy function")

# Step 5: Insert one document
def step5_insert_one():
    cursor = conn.cursor()

    section = sections[0]
    metadata = {
        'pdf': section['pdf'],
        'section_number': section['section_number'],
        'title': section['title'],
        'level': section['level'],
        'categories': categories
    }

    print(f"  Inserting: {section['section_number']} {section['title']}", flush=True)
    cursor.execute("""
        INSERT INTO documents (title, category, source_path, metadata)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        f"{section['section_number']} {section['title']}",
        categories[0] if categories else "General",
        "test",
        json.dumps(metadata)
    ))

    doc_id = cursor.fetchone()[0]
    print(f"  Document ID: {doc_id}", flush=True)
    conn.commit()
    cursor.close()
    return doc_id

doc_id = test_with_timeout(step5_insert_one, 10, "Insert one document")

# Clean up
conn.close()
print("\n[TEST] ✓ All steps completed successfully!", flush=True)
