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

from core.model.paper import Paper, PaperSection, Caption


# Heuristics for common section headings in engineering papers (EN + ZH).
SECTION_PATTERNS = [
    r"^\s*\d*\.?\d*\s*(abstract|summary)\b",
    r"^\s*\d*\.?\d*\s*(introduction|background)\b",
    r"^\s*\d*\.?\d*\s*(method|methodology|materials? and methods?|experimental|experiments?|numerical|finite element|finite element model)\b",
    r"^\s*\d*\.?\d*\s*(result|results|analysis|discussion|validation)\b",
    r"^\s*\d*\.?\d*\s*(conclusion|conclusions|summary and conclusion)\b",
    r"^\s*\d*\.?\d*\s*(reference|references|bibliography)\b",
    # Chinese headings (common in domestic journals)
    r"^\s*\d*\.?\d*\s*(摘要|关键词)\s*[:：]?",
    r"^\s*\d*\.?\d*\s*(引言|介绍|前言|绪论)\s*$",
    r"^\s*\d*\.?\d*\s*(实验|试验|方法|材料与方法|研究方法)\s*$",
    r"^\s*\d*\.?\d*\s*(结果|结果与分析|分析与讨论|讨论)\s*$",
    r"^\s*\d*\.?\d*\s*(结论|结论与展望|结语)\s*$",
    r"^\s*\d*\.?\d*\s*(参考文献|引用标准)\s*$",
]

# Robust abstract anchor: covers "ABSTRACT", "A B S T R A C T" (spaced, common
# in two-column Elsevier layout), "Abstract", and Chinese "摘要".
_ABSTRACT_ANCHOR_RE = re.compile(
    r"^\s*A\s*B\s*S\s*T\s*R\s*A\s*C\s*T\s*[:：]?\s*$"
    r"|^\s*(abstract|summary)\s*[:：]?\s*$"
    r"|^\s*摘\s*要\s*[:：]?\s*$",
    flags=re.IGNORECASE,
)
# Stop collecting abstract text once we hit the next heading.
_ABSTRACT_STOP_RE = re.compile(
    r"^\s*(keywords?|key\s*words|关键词|1[\.\s]+(introduction|引言|介绍)|1\s*\.?\s*introduction)\b",
    flags=re.IGNORECASE,
)

# Caption line anchors: "Fig. 3:", "Figure 2.", "Table IV", "图3", "表1".
_CAPTION_RE = re.compile(
    r"^\s*(?P<kind>Fig\.?|Figure|FIG\.?|Table|TABLE|Tab\.?|表|图)\s*"
    r"(?P<num>\d+[.\d]*[a-zA-Z]?)\s*[:：.\-]?\s*(?P<rest>.*)$",
    flags=re.IGNORECASE,
)


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

    # Guess abstract (robust: handles "A B S T R A C T" spaced layout,
    # plain "Abstract", and Chinese "摘要").
    paper.abstract = _extract_abstract(page_texts)

    # Extract figure/table captions verbatim so chart analysis can reference
    # real numbers instead of hallucinating indices.
    paper.captions = _extract_captions(page_texts)

    return paper


def _extract_abstract(page_texts: List[str]) -> str:
    """Walk page 1 (and page 2 overflow) for an abstract anchor, then collect
    text until the next heading (keywords / 1. Introduction)."""
    buf: List[str] = []
    in_abstract = False
    for page_idx, text in enumerate(page_texts[:2], start=1):
        for line in text.splitlines():
            stripped = line.strip()
            if not in_abstract:
                if _ABSTRACT_ANCHOR_RE.match(stripped):
                    in_abstract = True
                continue
            # Already inside abstract body.
            if _ABSTRACT_STOP_RE.match(stripped):
                return " ".join(buf).strip()[:2000]
            if stripped:
                buf.append(stripped)
    return " ".join(buf).strip()[:2000]


def _extract_captions(page_texts: List[str]) -> List[Caption]:
    """Scan pages for caption lines (Fig.x / Table x / 图x / 表x).

    A caption block runs from the anchor line through following non-empty
    continuation lines until a blank line or the next caption/section anchor.
    """
    captions: List[Caption] = []
    pending: Caption | None = None
    pending_lines: List[str] = []

    def flush():
        nonlocal pending, pending_lines
        if pending is not None:
            text = (pending.text + " " + " ".join(pending_lines)).strip()
            pending.text = text[:400]
            captions.append(pending)
        pending = None
        pending_lines = []

    for page_idx, text in enumerate(page_texts, start=1):
        for line in text.splitlines():
            stripped = line.strip()
            m = _CAPTION_RE.match(stripped)
            # Distinguish real captions from in-text citations:
            #   real caption: "Fig. 1. The Metallographic..."  -> rest starts UPPERCASE
            #   in-text cite: "Fig. 2 shows the stress..."     -> rest starts lowercase verb
            # Also skip explicit citation phrasings like "see Fig. 3 for ...".
            rest_head = m.group("rest")[:1] if m else ""
            is_intext_cite = (
                not m
                or len(stripped) >= 200
                or stripped.lower().startswith(("see fig", "as fig", "fig. s"))
                or (rest_head and not rest_head.isupper())
            )
            if is_intext_cite:
                # Body line (or an in-text Fig. citation) — continue appending
                # to current caption block, but flush if body line is long.
                if pending is not None:
                    if not stripped:
                        flush()
                    elif len(stripped) < 200:
                        pending_lines.append(stripped)
                    else:
                        flush()
                continue
            flush()
            kind_raw = m.group("kind").lower()
            kind = "table" if kind_raw.startswith(("table", "tab", "表")) else "figure"
            number = f"{m.group('kind')} {m.group('num')}".replace(". ", ".").strip()
            pending = Caption(number=number, kind=kind, text=m.group("rest").strip(), page=page_idx)
            pending_lines = []
    flush()

    # Deduplicate by number, keep first occurrence.
    seen = set()
    out = []
    for c in captions:
        key = c.number.lower().replace(" ", "")
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


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
