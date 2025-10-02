#!/usr/bin/env python3
"""Debug: Process page 7 line by line"""
import sys
import time
sys.path.insert(0, '/mnt/c/Users/p355208/OneDrive - Dr. Ing. h.c. F. Porsche AG/Notebooks/Projects/AI/Arch_review/POC/MPC')

import fitz
from pdf2text import (
    initialise_ignore_section_labels,
    SectionAggregator,
    detect_heading, should_ignore_section,
    clean_text, PagePreprocessor
)

initialise_ignore_section_labels('ignore_sections.json')

pdf_path = 'pdfs/Leitfaden Software Architektur Dokumentation (English) _ VR6.0.2.pdf'
doc = fitz.open(pdf_path)
page = doc[6]  # Page 7

raw_text = page.get_text("text") or ""
cleaned = clean_text(raw_text)
preprocessor = PagePreprocessor()
cleaned = preprocessor.clean_page(cleaned, 7)

print("Processing 35 lines from page 7:")
print("=" * 70)

aggregator = SectionAggregator()

for i, line in enumerate(cleaned.splitlines()[:20]):  # Only first 20 lines
    stripped = line.strip()
    if not stripped:
        continue

    start = time.time()
    heading = detect_heading(stripped, 7)
    elapsed_detect = (time.time() - start) * 1000

    if heading:
        level, number, title = heading
        start = time.time()
        ignore = should_ignore_section(number, title)
        elapsed_ignore = (time.time() - start) * 1000

        print(f"Line {i:2d} ({elapsed_detect:5.1f}ms + {elapsed_ignore:5.1f}ms): HEADING {level} | {number:6s} | {title[:30]:30s} | ignore={ignore}")

        if elapsed_detect > 100 or elapsed_ignore > 100:
            print(f"  ⚠ LANGSAM! line='{stripped[:80]}'")
            break
    else:
        if elapsed_detect > 100:
            print(f"Line {i:2d} ({elapsed_detect:5.1f}ms): TEXT (LANGSAM!) | '{stripped[:50]}'")
            break

print("\n✓ Abgeschlossen")
doc.close()