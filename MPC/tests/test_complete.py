#!/usr/bin/env python3
import os
os.chdir("/mnt/c/Users/p355208/OneDrive - Dr. Ing. h.c. F. Porsche AG/Notebooks/Projects/AI/Arch_review/POC/MPC")

import sys
import fitz
from pdf2text import initialise_ignore_section_labels, SectionAggregator, PagePreprocessor, clean_text, annotate_page_text, should_skip_page

initialise_ignore_section_labels('ignore_sections.json')

doc = fitz.open('pdfs/Leitfaden Software Architektur Dokumentation (English) _ VR6.0.2.pdf')
aggregator = SectionAggregator()
preprocessor = PagePreprocessor()

test_pages = [1, 2, 3, 7, 31]

with open('txts/test_complete.txt', 'w', encoding='utf-8') as out:
    for page_num in test_pages:
        page = doc[page_num - 1]
        raw_text = page.get_text('text') or ''
        skip = should_skip_page(raw_text)
        cleaned = clean_text(raw_text)
        cleaned = preprocessor.clean_page(cleaned, page_num)
        if skip:
            cleaned = ""
        annotated = annotate_page_text(cleaned, page_num, aggregator)
        out.write(f"--- Seite {page_num} ---\n")
        if annotated:
            out.write(f"{annotated}\n\n")
        else:
            out.write("\n")
        sys.stdout.write(f"Seite {page_num:2d} skip={skip}\n")
        sys.stdout.flush()

sections = aggregator.finalize()
print(f"\n=== Sections: {len(sections)} ===")
for sec in sections[:15]:
    print(f"{sec.level} | {sec.number:6s} | {sec.title[:50]:50s} | S.{sec.page_start}")

doc.close()
