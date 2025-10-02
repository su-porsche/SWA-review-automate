#!/usr/bin/env python3
"""Debug: Process pages with full pipeline and timeout per page"""
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

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Timeout!")

initialise_ignore_section_labels('ignore_sections.json')

pdf_path = 'pdfs/Leitfaden Software Architektur Dokumentation (English) _ VR6.0.2.pdf'
doc = fitz.open(pdf_path)
aggregator = SectionAggregator()
preprocessor = PagePreprocessor()

print(f"Verarbeite {len(doc)} Seiten (max 60s pro Seite)\n")

for page_num in range(1, min(10, len(doc)) + 1):
    page = doc[page_num - 1]

    start = time.time()

    try:
        # Set alarm for 60 seconds
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)

        raw_text = page.get_text("text") or ""
        skip = should_skip_page(raw_text)
        cleaned = clean_text(raw_text)
        cleaned = preprocessor.clean_page(cleaned, page_num)

        if skip:
            cleaned = ""

        annotated = annotate_page_text(cleaned, page_num, aggregator)

        # Cancel alarm
        signal.alarm(0)

        elapsed = time.time() - start
        status = "✓" if elapsed < 1.0 else "⚠"
        print(f"Seite {page_num:2d}: {elapsed:6.2f}s | skip={skip:5} | {len(annotated):5d} chars | {status}")

        if elapsed > 10.0:
            print(f"  ⚠ WARNUNG: Sehr langsam!")
            print(f"  raw_text length: {len(raw_text)}")
            print(f"  cleaned length: {len(cleaned)}")
            break

    except TimeoutError:
        print(f"Seite {page_num:2d}: TIMEOUT nach 60s!")
        break
    except Exception as e:
        print(f"Seite {page_num:2d}: ERROR - {e}")
        break

doc.close()
print("\n✓ Test abgeschlossen")