#!/usr/bin/env python3
"""Test full annotate_page_text on page 4"""
import sys
import time
import threading
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
page = doc[3]  # Page 4

raw_text = page.get_text("text") or ""
cleaned = clean_text(raw_text)
preprocessor = PagePreprocessor()
cleaned = preprocessor.clean_page(cleaned, 4)

aggregator = SectionAggregator()

print("Testing annotate_page_text with 10 second timeout...")
print(f"Input: {len(cleaned)} chars, {len(cleaned.splitlines())} lines\n")

result = [None]
error = [None]

def run_annotate():
    try:
        result[0] = annotate_page_text(cleaned, 4, aggregator)
    except Exception as e:
        error[0] = e

thread = threading.Thread(target=run_annotate)
thread.daemon = True

start = time.time()
thread.start()
thread.join(timeout=10.0)

if thread.is_alive():
    print("✗ TIMEOUT after 10s!")
    print("\nThe function is stuck. Likely in:")
    print("  - A regex catastrophic backtracking")
    print("  - An infinite loop in SectionAggregator")
    print("  - should_ignore_section() hanging")
else:
    elapsed = time.time() - start
    if error[0]:
        print(f"✗ ERROR after {elapsed:.2f}s: {error[0]}")
    else:
        print(f"✓ SUCCESS after {elapsed:.2f}s")
        print(f"Output: {len(result[0])} chars")

doc.close()