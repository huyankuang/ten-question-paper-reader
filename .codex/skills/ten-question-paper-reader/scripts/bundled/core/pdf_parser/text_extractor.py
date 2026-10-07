"""PDF text extractor using PyMuPDF (fitz).

Extracts full text, per-page text, title guess, and basic section structure.
Designed for English two-column engineering papers.
"""
import re
from typing import List, Tuple

try:
    import pymupdf as fitz  # PyMuPDF (modern import path; silences the legacy fitz deprecation warning)
except ImportError:
    fitz = None

from core.model.paper import Paper, PaperSection


# Heuristics for common section headings in engineering papers.
SECTION_PATTERNS = [
    r"^\s*\d*\.?\d*\s*(abstract|summary)\b",
    r"^\s*\d*\.?\d*\s*(introduction|background)\b",
    r"^\s*\d*\.?\d*\s*(method|methodology|materials? and methods?|experimental|numerical|finite element|finite element model)\b",
    r"^\s*\d*\.?\d*\s*(result|results|analysis|discussion|validation)\b",
    r"^\s*\d*\.?\d*\s*(conclusion|conclusions|summary and conclusion)\b",
    r"^\s*\d*\.?\d*\s*(reference|references|bibliography)\b",
]


def _require_fitz():
    if fitz is None:
        raise RuntimeError(
            "PyMuPDF is not installed. Run: pip install pymupdf"
        )


def extract_paper(pdf_path: str) -> Paper:
    """Parse a PDF file into a structured Paper object."""
    _require_fitz()
    doc = fitz.open(pdf_path)
    paper = Paper(source_path=pdf_path, total_pages=doc.page_count)

    page_texts: List[str] = []
    for page in doc:
        page_texts.append(page.get_text("text"))
    doc.close()

    paper.full_text = "\n".join(page_texts)

    # Guess title: largest-font-ish heuristic — first non-empty line on page 1.
    first_page_lines = [l.strip() for l in page_texts[0].splitlines() if l.strip()]
    if first_page_lines:
        paper.title = first_page_lines[0][:300]

    # Split into sections by heading patterns.
    paper.sections = _split_sections(page_texts)

    # Guess abstract.
    for s in paper.sections:
        if "abstract" in s.title.lower():
            paper.abstract = s.text[:2000]
            break

    return paper


def _split_sections(page_texts: List[str]) -> List[PaperSection]:
    """Very lightweight section splitter based on heading regex."""
    sections: List[PaperSection] = []
    current_title = "Pre-text"
    current_buf: List[str] = []
    current_start = 1

    for page_idx, text in enumerate(page_texts, start=1):
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                current_buf.append("")
                continue
            matched = False
            for pat in SECTION_PATTERNS:
                if re.match(pat, stripped, flags=re.IGNORECASE) and len(stripped) < 120:
                    # Flush previous section.
                    sections.append(
                        PaperSection(
                            title=current_title,
                            text="\n".join(current_buf).strip(),
                            start_page=current_start,
                            end_page=page_idx,
                        )
                    )
                    current_title = stripped
                    current_buf = []
                    current_start = page_idx
                    matched = True
                    break
            if not matched:
                current_buf.append(stripped)

    # Flush last.
    sections.append(
        PaperSection(
            title=current_title,
            text="\n".join(current_buf).strip(),
            start_page=current_start,
            end_page=len(page_texts),
        )
    )
    # Drop empty sections.
    return [s for s in sections if s.text.strip()]
