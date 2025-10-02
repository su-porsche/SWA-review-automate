#!/usr/bin/env python3
"""Debug: Process pages one by one with timing"""
import sys
import time
import fitz

pdf_path = 'pdfs/Leitfaden Software Architektur Dokumentation (English) _ VR6.0.2.pdf'
doc = fitz.open(pdf_path)

print(f"PDF hat {len(doc)} Seiten\n")
print("Teste Text-Extraktion pro Seite (ohne OCR):\n")

for page_num in range(1, min(10, len(doc)) + 1):
    page = doc[page_num - 1]

    start = time.time()
    raw_text = page.get_text("text") or ""
    elapsed = time.time() - start

    text_len = len(raw_text.strip())
    status = "✓" if elapsed < 1.0 else "⚠ LANGSAM"

    print(f"Seite {page_num:2d}: {elapsed:5.2f}s | {text_len:5d} chars | {status}")

    if elapsed > 5.0:
        print(f"  ⚠ WARNUNG: Seite {page_num} dauerte {elapsed:.2f}s!")
        print(f"  Erste 200 Zeichen: {raw_text[:200]}")
        break

doc.close()
print("\n✓ Test abgeschlossen")