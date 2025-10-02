#!/usr/bin/env python3
"""Debug: Test import times"""
import time
import sys

print("Test 1: Import fitz...")
start = time.time()
import fitz
print(f"  → {time.time() - start:.2f}s")

print("\nTest 2: Import pytesseract...")
start = time.time()
import pytesseract
print(f"  → {time.time() - start:.2f}s")

print("\nTest 3: Import PIL...")
start = time.time()
from PIL import Image
print(f"  → {time.time() - start:.2f}s")

print("\nTest 4: Import pdf2text module...")
start = time.time()
sys.path.insert(0, '/mnt/c/Users/p355208/OneDrive - Dr. Ing. h.c. F. Porsche AG/Notebooks/Projects/AI/Arch_review/POC/MPC')

print("  4a: Importing pdf2text...")
import pdf2text
print(f"  → {time.time() - start:.2f}s")

print("\nTest 5: Call initialise_ignore_section_labels...")
start = time.time()
pdf2text.initialise_ignore_section_labels('ignore_sections.json')
print(f"  → {time.time() - start:.2f}s")

print("\n✓ Alle Imports erfolgreich")