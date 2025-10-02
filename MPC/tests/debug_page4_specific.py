#!/usr/bin/env python3
"""Debug page 4 of the problematic PDF"""
import sys
import time
sys.path.insert(0, '/mnt/c/Users/p355208/OneDrive - Dr. Ing. h.c. F. Porsche AG/Notebooks/Projects/AI/Arch_review/POC/MPC')

import fitz
from pdf2text import (
    initialise_ignore_section_labels,
    SectionAggregator, PagePreprocessor,
    clean_text, annotate_page_text
)

initialise_ignore_section_labels('ignore_sections.json')

pdf_path = 'pdfs/050_088_LAH.893.909_Konzern Grundanforderungen Software_DE_EN_V4.6.pdf'
doc = fitz.open(pdf_path)
page = doc[3]  # Page 4 (0-indexed)

print("=== Page 4 Debug ===\n")

# Extract text
raw_text = page.get_text("text") or ""
print(f"Raw text length: {len(raw_text)}")
print(f"\nFirst 500 chars:")
print(repr(raw_text[:500]))

# Clean text
cleaned = clean_text(raw_text)
preprocessor = PagePreprocessor()
cleaned = preprocessor.clean_page(cleaned, 4)

print(f"\nCleaned text length: {len(cleaned)}")
print(f"Number of lines: {len(cleaned.splitlines())}")

print(f"\nFirst 10 lines:")
for i, line in enumerate(cleaned.splitlines()[:10]):
    print(f"  {i:2d}: '{line[:80]}'")

print("\n" + "="*70)
print("Testing annotate_page_text line by line...")
print("="*70)

aggregator = SectionAggregator()
lines = cleaned.splitlines()

for i, line in enumerate(lines[:30]):  # Test first 30 lines
    stripped = line.strip()
    if not stripped:
        continue

    print(f"Line {i:2d}: '{stripped[:60]:60s}'", end=" ... ")
    sys.stdout.flush()

    start = time.time()
    from pdf2text import detect_heading

    try:
        heading = detect_heading(stripped, 4)
        elapsed = (time.time() - start) * 1000

        if elapsed > 100:
            print(f"SLOW! {elapsed:.1f}ms")
            print(f"  Full line: {repr(stripped)}")
            break
        else:
            print(f"OK ({elapsed:.1f}ms) heading={heading is not None}")
    except Exception as e:
        print(f"ERROR: {e}")
        break

doc.close()
print("\n✓ Done")