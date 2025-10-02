#!/usr/bin/env python3
"""Debug: Analyze page 7"""
import sys
import time
sys.path.insert(0, '/mnt/c/Users/p355208/OneDrive - Dr. Ing. h.c. F. Porsche AG/Notebooks/Projects/AI/Arch_review/POC/MPC')

import fitz
from pdf2text import clean_text, should_skip_page, PagePreprocessor, _normalise_label

pdf_path = 'pdfs/Leitfaden Software Architektur Dokumentation (English) _ VR6.0.2.pdf'
doc = fitz.open(pdf_path)
page = doc[6]  # Page 7 (0-indexed)

print("=== Seite 7 Debug ===\n")

print("Schritt 1: Text extrahieren...")
start = time.time()
raw_text = page.get_text("text") or ""
print(f"  → {time.time() - start:.2f}s | {len(raw_text)} chars")

print("\nSchritt 2: should_skip_page()...")
start = time.time()
skip = should_skip_page(raw_text)
print(f"  → {time.time() - start:.2f}s | skip={skip}")

if skip:
    print("\nSeite wird übersprungen. Erste 10 Zeilen:")
    for i, line in enumerate(raw_text.splitlines()[:10]):
        normalized = _normalise_label(line)
        print(f"  {i}: '{line[:60]}' -> '{normalized}'")

print("\nSchritt 3: clean_text()...")
start = time.time()
cleaned = clean_text(raw_text)
print(f"  → {time.time() - start:.2f}s | {len(cleaned)} chars")

print("\nSchritt 4: PagePreprocessor.clean_page()...")
preprocessor = PagePreprocessor()
start = time.time()

# Diese Funktion könnte das Problem sein!
print("  Starte clean_page()... (max 10s)")
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Timeout in clean_page!")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(10)

try:
    result = preprocessor.clean_page(cleaned, 7)
    signal.alarm(0)
    print(f"  → {time.time() - start:.2f}s | {len(result)} chars")
except TimeoutError:
    signal.alarm(0)
    print(f"  → TIMEOUT in clean_page()!")
    print(f"\n  Erste 500 Zeichen des Inputs:")
    print(f"  {repr(cleaned[:500])}")

doc.close()