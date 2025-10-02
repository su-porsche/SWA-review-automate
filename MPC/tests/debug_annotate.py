#!/usr/bin/env python3
"""Debug: Test annotate_page_text on page 7"""
import sys
import time
import signal
sys.path.insert(0, '/mnt/c/Users/p355208/OneDrive - Dr. Ing. h.c. F. Porsche AG/Notebooks/Projects/AI/Arch_review/POC/MPC')

import fitz
from pdf2text import (
    initialise_ignore_section_labels,
    SectionAggregator, PagePreprocessor,
    clean_text, annotate_page_text
)

initialise_ignore_section_labels('ignore_sections.json')

pdf_path = 'pdfs/Leitfaden Software Architektur Dokumentation (English) _ VR6.0.2.pdf'
doc = fitz.open(pdf_path)

aggregator = SectionAggregator()
preprocessor = PagePreprocessor()

print("=== Test annotate_page_text auf Seite 7 ===\n")

page = doc[6]  # Page 7
raw_text = page.get_text("text") or ""
cleaned = clean_text(raw_text)
cleaned = preprocessor.clean_page(cleaned, 7)

print(f"Input text: {len(cleaned)} chars")
print(f"Zeilen: {len(cleaned.splitlines())}")
print("\nErste 10 Zeilen:")
for i, line in enumerate(cleaned.splitlines()[:10]):
    print(f"  {i}: '{line[:70]}'")

print("\n\nStarte annotate_page_text() mit 10s Timeout...")

def timeout_handler(signum, frame):
    raise TimeoutError("Timeout!")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(10)

try:
    start = time.time()
    result = annotate_page_text(cleaned, 7, aggregator)
    signal.alarm(0)
    elapsed = time.time() - start
    print(f"✓ Erfolg nach {elapsed:.2f}s")
    print(f"Output: {len(result)} chars")
except TimeoutError:
    signal.alarm(0)
    print("✗ TIMEOUT nach 10s in annotate_page_text()!")
    print("\nDas Problem liegt in annotate_page_text() oder detect_heading()")

doc.close()