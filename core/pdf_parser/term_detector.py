"""Technical term detection and location.

Strategy:
1. Match built-in SEED_TERMS against the full text.
2. Record the first page where each term appears.
3. Optionally (when LLM is available), extract paper-specific terms;
   in MVP we rely on seed terms + a simple capitalized-phrase heuristic.
"""
import re
from typing import List, Tuple

import fitz

from core.config import SEED_TERMS
from core.model.paper import Paper, Term


def detect_terms(paper: Paper, pdf_path: str) -> List[Term]:
    """Return list of detected terms with page locations."""
    terms: List[Term] = []
    seen = set()

    # 1. Seed terms
    for term_name, definition in SEED_TERMS.items():
        # Match English or Chinese variants loosely.
        pattern = re.compile(re.escape(term_name), re.IGNORECASE)
        if pattern.search(paper.full_text):
            page = _find_first_page(pdf_path, pattern)
            terms.append(
                Term(
                    name=term_name,
                    definition=definition,
                    section="",
                    page=page,
                )
            )
            seen.add(term_name.lower())

    # 2. Heuristic: capitalized multi-word phrases in abstract/title
    #    that look like domain terms (e.g. "Polynomial Chaos Kriging").
    candidates = _extract_capitalized_phrases(paper.abstract)
    for phrase in candidates:
        if phrase.lower() in seen:
            continue
        if len(phrase.split()) < 2 or len(phrase.split()) > 5:
            continue
        terms.append(
            Term(
                name=phrase,
                definition="",  # to be filled by LLM
                section="Abstract",
                page=1,
            )
        )
        seen.add(phrase.lower())

    paper.terms = terms
    return terms


def _find_first_page(pdf_path: str, pattern: re.Pattern) -> int:
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return 1
    try:
        for i, page in enumerate(doc, start=1):
            if pattern.search(page.get_text("text")):
                return i
        return doc.page_count
    finally:
        doc.close()


def _extract_capitalized_phrases(text: str) -> List[str]:
    """Extract phrases like 'Finite Element Method' from text."""
    phrases = re.findall(r"\b(?:[A-Z][a-zA-Z]+(?:\s+)){1,4}(?:[A-Z][a-zA-Z]+)\b", text)
    # Deduplicate while preserving order.
    seen = set()
    out = []
    for p in phrases:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out
