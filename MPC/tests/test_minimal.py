#!/usr/bin/env python3
"""Minimaler Test ohne Imports von pdf2text"""
import sys
import time
import fitz

print("Step 1: Open PDF...")
start = time.time()
pdf_path = 'pdfs/Leitfaden Software Architektur Dokumentation (English) _ VR6.0.2.pdf'
doc = fitz.open(pdf_path)
print(f"  ✓ {time.time() - start:.2f}s | {len(doc)} pages")

print("\nStep 2: Extract text from first 10 pages...")
for page_num in range(1, min(11, len(doc)+1)):
    start = time.time()
    page = doc[page_num - 1]
    text = page.get_text("text") or ""
    elapsed = time.time() - start
    print(f"  Page {page_num:2d}: {elapsed:.3f}s | {len(text):5d} chars")
    if elapsed > 1.0:
        print(f"    ⚠ SLOW!")

doc.close()
print("\n✓ Done")