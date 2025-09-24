#!/usr/bin/env python3
"""
PDF to text converter with OCR fallback, section labelling, and configurable ignore rules.

Features:
- Processes PDFs page by page to keep memory usage low
- Extracts embedded text and falls back to OCR (Tesseract) when necessary
- Normalises text output and removes noisy whitespace or artefacts
- Detects numbered chapter and section headings (e.g. "2", "2.1", "2.1.1")
- Annotates the text output with Markdown-style headings for downstream chunking
- Optionally writes a JSONL file with structured section metadata for RAG pipelines
- Supports configurable lists of sections to ignore completely (e.g. change history, table of contents)
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

HEADING_RE = re.compile(
    r"^(?P<number>\d+(?:\.\d+)*)(?:\s*[)\-\u2013\u2014:]|\s+)(?P<title>.+)$"
)
ALL_CAPS_RE = re.compile(
    r"^[A-Z\u00c4\u00d6\u00dc][A-Z0-9\u00c4\u00d6\u00dc\u00df\s/-]{3,}$"
)
TOC_SPACING_RE = re.compile(r"\.{2,}")
TOP_LEVEL_DOT_HEADING_RE = re.compile(r"^(\d+)\.\s+")
IGNORE_LINE_PATTERNS = [
    re.compile(r"^se?ite?\s*\d+(?:\s+von\s+\d+)?$", re.IGNORECASE),
    re.compile(r"^\u00a9?\s*dr\.?\s*ing\.", re.IGNORECASE),
    re.compile(r"^ege2$", re.IGNORECASE),
    re.compile(r"^guide for software architecture documentation", re.IGNORECASE),
    re.compile(r"^version\s+\d", re.IGNORECASE),
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
]
DEFAULT_IGNORE_SECTION_NAMES = {
    "change history",
    "revision history",
    "summary of changes",
    "\u00e4nderungshistorie",
    "\u00e4nderungsverlauf",
    "historique des modifications",
    "historique",
    "table of contents",
    "contents",
    "content",
    "table des mati\u00e8res",
    "sommaire",
    "inhalt",
    "inhaltsverzeichnis",
    "verzeichnis"
}
IGNORE_SECTION_LABELS: Set[str] = set()


def _normalise_label(label: str) -> str:
    cleaned = label.strip()
    cleaned = re.sub(r"^\[[^\]]+\]\s*", "", cleaned)
    cleaned = re.sub(r"^\d+(?:\.\d+)*\s*", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.lower()


def _prepare_ignore_labels(values: Iterable[str]) -> Set[str]:
    labels: Set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        normalised = _normalise_label(value)
        if normalised:
            labels.add(normalised)
    return labels


def load_ignore_section_config(path: Optional[str]) -> Set[str]:
    if not path:
        return set()
    config_path = Path(path)
    if not config_path.exists():
        return set()
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"Warnung: Konnte Konfigurationsdatei {config_path} nicht laden ({exc}).")
        return set()

    entries: Iterable[str]
    if isinstance(data, dict):
        entries = data.get("ignore_sections", []) or []
    elif isinstance(data, list):
        entries = data
    else:
        return set()

    collected: List[str] = []
    for entry in entries:
        if isinstance(entry, str):
            collected.append(entry)
        elif isinstance(entry, dict):
            candidate = entry.get("label") or entry.get("name") or entry.get("value")
            if isinstance(candidate, str):
                collected.append(candidate)
    return _prepare_ignore_labels(collected)


def initialise_ignore_section_labels(config_path: Optional[str]) -> None:
    global IGNORE_SECTION_LABELS
    labels = _prepare_ignore_labels(DEFAULT_IGNORE_SECTION_NAMES)

    config_candidates: List[str] = []
    if config_path:
        config_candidates.append(config_path)
    else:
        default_path = Path(__file__).resolve().parent / "ignore_sections.json"
        if default_path.exists():
            config_candidates.append(str(default_path))

    for candidate in config_candidates:
        labels.update(load_ignore_section_config(candidate))

    IGNORE_SECTION_LABELS = labels


class PagePreprocessor:
    def __init__(
        self,
        header_window: int = 4,
        footer_window: int = 4,
        min_repeats: int = 2,
    ) -> None:
        self.header_window = header_window
        self.footer_window = footer_window
        self.min_repeats = min_repeats
        self.header_counts: Dict[str, int] = {}
        self.footer_counts: Dict[str, int] = {}
        self.header_lines: Set[str] = set()
        self.footer_lines: Set[str] = set()

    @staticmethod
    def _normalise_line(line: str) -> str:
        return re.sub(r"\s+", " ", line.strip()).lower()

    @staticmethod
    def _is_ignore_pattern(line: str) -> bool:
        for pattern in IGNORE_LINE_PATTERNS:
            if pattern.match(line.strip()):
                return True
        return False

    @staticmethod
    def _looks_like_toc(lines: List[str], page_num: int) -> bool:
        if not lines:
            return False
        limit = max(20, (2 * len(lines)) // 3)
        prefix = " ".join(line.lower() for line in lines[:limit])
        if "table of contents" in prefix or "table des mati" in prefix:
            return True
        if page_num <= 5:
            count = sum(
                1
                for line in lines
                if re.match(r"^(\d+(?:\.\d+)*)\s+.+", line.strip())
            )
            if count >= max(6, len(lines) // 2):
                return True
        return False

    def _update_profiles(self, lines: List[str]) -> None:
        header_slice = [line for line in lines[: self.header_window] if line.strip()]
        footer_slice = [line for line in lines[-self.footer_window :] if line.strip()]
        for item in header_slice:
            key = self._normalise_line(item)
            count = self.header_counts.get(key, 0) + 1
            self.header_counts[key] = count
            if count >= self.min_repeats:
                self.header_lines.add(key)
        for item in footer_slice:
            key = self._normalise_line(item)
            count = self.footer_counts.get(key, 0) + 1
            self.footer_counts[key] = count
            if count >= self.min_repeats:
                self.footer_lines.add(key)

    def clean_page(self, text: str, page_num: int) -> str:
        if not text:
            return ""
        lines = text.splitlines()
        self._update_profiles(lines)
        if self._looks_like_toc(lines, page_num):
            return ""
        filtered: List[str] = []
        total = len(lines)
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                filtered.append("")
                continue
            normalised = self._normalise_line(stripped)
            if self._is_ignore_pattern(stripped):
                continue
            if idx < self.header_window and normalised in self.header_lines:
                continue
            if total - idx <= self.footer_window and normalised in self.footer_lines:
                continue
            filtered.append(stripped)
        return "\n".join(filtered).strip()


@dataclass
class SectionBlock:
    level: int
    number: str
    title: str
    page_start: int
    page_end: int
    parent_number: Optional[str] = None
    lines: List[str] = field(default_factory=list)
    closed: bool = False

    def heading_text(self) -> str:
        parts = [self.number.strip(), self.title.strip()]
        return " ".join(part for part in parts if part)

    def add_line(self, line: str, page_num: int) -> None:
        if line.strip():
            self.lines.append(line)
        self.page_end = max(self.page_end, page_num)


class SectionAggregator:
    def __init__(self) -> None:
        self.active: List[SectionBlock] = []
        self.all_blocks: List[SectionBlock] = []
        self.ignore_section_active: bool = False
        self._ignore_level: Optional[int] = None

    def _close_until(self, level: int) -> None:
        while self.active and self.active[-1].level >= level:
            block = self.active.pop()
            block.closed = True

    def begin_ignored_section(self, level: int) -> None:
        self._close_until(level)
        self.ignore_section_active = True
        self._ignore_level = level

    def end_ignored_section(self) -> None:
        self.ignore_section_active = False
        self._ignore_level = None

    def _find_parent(self, level: int) -> Optional[str]:
        for block in reversed(self.active):
            if block.level < level and block.number and block.number != "0":
                return block.number
        return None

    def _update_page_end(self, page_num: int) -> None:
        for block in self.active:
            block.page_end = max(block.page_end, page_num)

    def start_section(self, level: int, number: str, title: str, page_num: int) -> None:
        number = number.strip()
        title = title.strip()
        self._close_until(level)
        parent = self._find_parent(level)
        block = SectionBlock(
            level=level,
            number=number,
            title=title,
            page_start=page_num,
            page_end=page_num,
            parent_number=parent,
        )
        heading_line = block.heading_text()
        if heading_line and not (level == 0 and number == "0"):
            block.lines.append(heading_line)
        self.active.append(block)
        self.all_blocks.append(block)
        self._update_page_end(page_num)

    def add_text(self, line: str, page_num: int) -> None:
        if self.ignore_section_active:
            return
        if not line.strip():
            return
        if not self.active:
            self.start_section(0, "0", "Document", page_num)
        self._update_page_end(page_num)
        self.active[-1].add_line(line, page_num)

    def finalize(self) -> List[SectionBlock]:
        self.end_ignored_section()
        self._close_until(0)
        closed_blocks = [block for block in self.all_blocks if block.closed]
        filtered = [
            block
            for block in closed_blocks
            if not (block.level == 0 and block.number == "0")
        ]
        if not filtered:
            filtered = [
                block
                for block in closed_blocks
                if block.level == 0 and block.number == "0"
            ]
        filtered.sort(key=lambda b: (b.page_start, b.level))
        return filtered


def clean_text(text: str) -> str:
    normalised = unicodedata.normalize("NFKC", text)
    normalised = normalised.replace("\u2022", "-").replace("\uf0b7", "-")
    sanitized = re.sub(
        r"[^\t\n\r\x20-\x7E\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df\u20ac]",
        "",
        normalised,
    )
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)
    sanitized = re.sub(r"^e\s*$", "", sanitized, flags=re.MULTILINE)
    return sanitized.strip()


def _normalise_heading_title(title: str, page_num: int) -> Tuple[str, bool]:
    cleaned = TOC_SPACING_RE.sub(" ", title)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    parts = cleaned.rsplit(" ", 1)
    if len(parts) == 2:
        head, tail = parts
        tail_stripped = tail.strip().rstrip(".:)")
        if tail_stripped.isdigit() and len(tail_stripped) <= 3:
            referenced_page = int(tail_stripped)
            if abs(referenced_page - page_num) > 1:
                return head.strip(), True
            cleaned = head.strip()
    return cleaned, False


def detect_heading(line: str, page_num: int) -> Optional[Tuple[int, str, str]]:
    stripped = line.strip()
    candidate = stripped
    match = HEADING_RE.match(candidate)
    if not match:
        alternative = TOP_LEVEL_DOT_HEADING_RE.sub(r"\1 ", stripped, count=1)
        if alternative != stripped:
            candidate = alternative
            match = HEADING_RE.match(candidate)
    if match:
        number = match.group("number").rstrip(".")
        raw_title = match.group("title").strip(" \t-\u2013\u2014:)")
        title, looks_like_toc = _normalise_heading_title(raw_title, page_num)
        if looks_like_toc:
            return None
        if title and any(char.isalpha() for char in title):
            level = len(number.split("."))
            return level, number, title
    if ALL_CAPS_RE.match(stripped):
        title, looks_like_toc = _normalise_heading_title(stripped, page_num)
        if looks_like_toc:
            return None
        if title:
            return 1, "", title
    return None


def should_skip_page(raw_text: str) -> bool:
    if not raw_text:
        return False
    lowered = raw_text.lower()
    for label in IGNORE_SECTION_LABELS:
        if label and label in lowered:
            return True
    return False


def should_ignore_section(number: str, title: str) -> bool:
    heading = " ".join(part for part in [number.strip(), title.strip()] if part)
    candidates = [heading, title]
    candidates.extend(_normalise_label(item) for item in candidates)
    for candidate in candidates:
        if _normalise_label(candidate) in IGNORE_SECTION_LABELS:
            return True
    return False


def format_heading(level: int, number: str, title: str) -> str:
    level = max(1, min(level, 6))
    prefix = "#" * level
    heading_parts = [number.strip(), title.strip()]
    heading_text = " ".join(part for part in heading_parts if part)
    return f"{prefix} {heading_text}".strip()


def annotate_page_text(cleaned_text: str, page_num: int, aggregator: SectionAggregator) -> str:
    if not cleaned_text:
        return ""
    annotated_lines: List[str] = []
    for raw_line in cleaned_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            if not aggregator.ignore_section_active:
                annotated_lines.append("")
            continue
        heading = detect_heading(stripped, page_num)
        if heading:
            level, number, title = heading
            if should_ignore_section(number, title):
                aggregator.begin_ignored_section(level)
                continue
            aggregator.end_ignored_section()
            aggregator.start_section(level, number, title, page_num)
            annotated_lines.append(format_heading(level, number, title))
            continue
        if aggregator.ignore_section_active:
            continue
        aggregator.add_text(stripped, page_num)
        annotated_lines.append(stripped)
    if aggregator.ignore_section_active:
        annotated_lines = [line for line in annotated_lines if line]
    return "\n".join(annotated_lines)


def write_section_jsonl(
    sections: List[SectionBlock],
    pdf_path: str,
    structured_path: str,
) -> None:
    with open(structured_path, "w", encoding="utf-8") as handle:
        for block in sections:
            text_body = "\n".join(block.lines).strip()
            record = {
                "pdf": os.path.basename(pdf_path),
                "section_number": block.number or None,
                "title": block.title,
                "level": block.level,
                "parent_number": block.parent_number,
                "page_start": block.page_start,
                "page_end": block.page_end,
                "heading": block.heading_text(),
                "text": text_body,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def process_pdf(
    pdf_path: str,
    out_path: str,
    lang: str = "de",
    write_structure: bool = False,
) -> None:
    doc = fitz.open(pdf_path)
    aggregator = SectionAggregator()
    preprocessor = PagePreprocessor()
    total_pages = len(doc)

    with open(out_path, "w", encoding="utf-8") as handle:
        for index in range(total_pages):
            page_num = index + 1
            page = doc[index]
            raw_text = page.get_text("text") or ""
            skip_page = should_skip_page(raw_text)

            if not skip_page and (not raw_text or len(raw_text.strip()) < 30):
                pix = page.get_pixmap(dpi=200)
                image_bytes = pix.tobytes("png")
                image = Image.open(io.BytesIO(image_bytes))
                try:
                    raw_text = pytesseract.image_to_string(image, lang=lang)
                finally:
                    image.close()
                skip_page = should_skip_page(raw_text) or skip_page

            cleaned = clean_text(raw_text)
            cleaned = preprocessor.clean_page(cleaned, page_num)
            if skip_page:
                cleaned = ""

            annotated = annotate_page_text(cleaned, page_num, aggregator)
            handle.write(f"--- Seite {page_num} ---\n")
            if annotated:
                handle.write(f"{annotated}\n\n")
            else:
                handle.write("\n")

            print(f"[{os.path.basename(pdf_path)}] Seite {page_num}/{total_pages} verarbeitet")

    sections = aggregator.finalize()
    if write_structure and sections:
        structured_path = os.path.splitext(out_path)[0] + "_sections.jsonl"
        write_section_jsonl(sections, pdf_path, structured_path)

    doc.close()
def main() -> None:
    parser = argparse.ArgumentParser(
        description="PDF zu Text mit OCR-Fallback, Kapitel-Markierung und Ignore-Listen"
    )
    parser.add_argument("input_dir", help="Verzeichnis mit PDF-Dateien")
    parser.add_argument("output_dir", help="Zielverzeichnis fuer Textdateien")
    parser.add_argument("--lang", default="de", help="OCR-Sprache (default: de)")
    parser.add_argument(
        "--json-structure",
        action="store_true",
        help="Erzeugt zusaetzlich eine JSONL-Datei mit Abschnittsmetadaten",
    )
    parser.add_argument(
        "--ignore-config",
        help="Pfad zu einer JSON-Datei mit Abschnittsbezeichnungen, die ignoriert werden sollen",
    )
    args = parser.parse_args()

    initialise_ignore_section_labels(args.ignore_config)

    os.makedirs(args.output_dir, exist_ok=True)

    for file_name in os.listdir(args.input_dir):
        if file_name.lower().endswith(".pdf"):
            pdf_path = os.path.join(args.input_dir, file_name)
            txt_path = os.path.join(
                args.output_dir,
                os.path.splitext(file_name)[0] + ".txt",
            )
            process_pdf(pdf_path, txt_path, args.lang, args.json_structure)


def _entry_point() -> None:
    main()


if __name__ == "__main__":
    _entry_point()

