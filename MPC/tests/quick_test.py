#!/usr/bin/env python3
import json
import psycopg2
from psycopg2.extras import execute_values

# Quick minimal test
conn = psycopg2.connect(host='localhost', database='swadocs', user='swaagent', password='swaagent911')
cursor = conn.cursor()

with open('test_dir/test_small_sections.jsonl') as f:
    sections = [json.loads(line) for line in f]

print(f"Processing {len(sections)} sections...")

for i, s in enumerate(sections, 1):
    print(f"{i}/{len(sections)}: {s['section_number']} {s['title']}")
   
    cursor.execute(
        "INSERT INTO documents (title, category, source_path, metadata) VALUES (%s, %s, %s, %s) RETURNING id",
        (s['title'], s['section_number'], 'test', json.dumps({'test': 'data'}))
    )
    doc_id = cursor.fetchone()[0]
   
    text = s['text']
    if text:
        cursor.execute(
            "INSERT INTO chunks (document_id, chunk_text, chunk_index) VALUES (%s, %s, %s)",
            (doc_id, text[:500], 0)
        )
   
    conn.commit()

cursor.close()
conn.close()
print("Done!")
