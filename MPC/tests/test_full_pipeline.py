#!/usr/bin/env python3
"""Test full processing pipeline with detailed timing"""
import sys
import time
import signal
sys.path.insert(0, '/mnt/c/Users/p355208/OneDrive - Dr. Ing. h.c. F. Porsche AG/Notebooks/Projects/AI/Arch_review/POC/MPC')

import fitz
from pdf2text import (
    initialise_ignore_section_labels,
    SectionAggregator, PagePreprocessor,
    clean_text, annotate_page_text, should_skip_page
)

def timeout_handler(signum, frame):
    raise TimeoutError("Timeout!")

initialise_ignore_section_labels('ignore_sections.json')

pdf_path = 'pdfs/Leitfaden Software Architektur Dokumentation (English) _ VR6.0.2.pdf'
doc = fitz.open(pdf_path)

aggregator = SectionAggregator()
preprocessor = PagePreprocessor()

print("Processing pages with 30s timeout per page...\n")

for page_num in range(1, min(8, len(doc)+1)):
    print(f"Page {page_num}:")
    page = doc[page_num - 1]

    # Step 1: Extract text
    signal.alarm(5)
    try:
        start = time.time()
        raw_text = page.get_text("text") or ""
        signal.alarm(0)
        print(f"  1. Extract:    {(time.time()-start)*1000:6.1f}ms | {len(raw_text):5d} chars")
    except TimeoutError:
        print(f"  ✗ TIMEOUT in get_text!")
        break

    # Step 2: should_skip_page
    signal.alarm(5)
    try:
        start = time.time()
        skip = should_skip_page(raw_text)
        signal.alarm(0)
        print(f"  2. Skip check: {(time.time()-start)*1000:6.1f}ms | skip={skip}")
    except TimeoutError:
        print(f"  ✗ TIMEOUT in should_skip_page!")
        break

    # Step 3: clean_text
    signal.alarm(5)
    try:
        start = time.time()
        cleaned = clean_text(raw_text)
        signal.alarm(0)
        print(f"  3. Clean:      {(time.time()-start)*1000:6.1f}ms | {len(cleaned):5d} chars")
    except TimeoutError:
        print(f"  ✗ TIMEOUT in clean_text!")
        break

    # Step 4: preprocessor.clean_page
    signal.alarm(5)
    try:
        start = time.time()
        cleaned = preprocessor.clean_page(cleaned, page_num)
        signal.alarm(0)
        print(f"  4. Preprocess: {(time.time()-start)*1000:6.1f}ms | {len(cleaned):5d} chars")
    except TimeoutError:
        print(f"  ✗ TIMEOUT in clean_page!")
        break

    if skip:
        cleaned = ""

    # Step 5: annotate_page_text (THIS IS WHERE IT HANGS!)
    signal.alarm(30)
    try:
        start = time.time()
        annotated = annotate_page_text(cleaned, page_num, aggregator)
        signal.alarm(0)
        elapsed = (time.time()-start)*1000
        print(f"  5. Annotate:   {elapsed:6.1f}ms | {len(annotated):5d} chars")

        if elapsed > 1000:
            print(f"    ⚠ VERY SLOW! First 200 chars of cleaned text:")
            print(f"    {repr(cleaned[:200])}")
            break
    except TimeoutError:
        signal.alarm(0)
        print(f"  ✗ TIMEOUT in annotate_page_text!")
        print(f"    First 300 chars of cleaned text:")
        print(f"    {repr(cleaned[:300])}")
        break

doc.close()
print("\n✓ Test complete")