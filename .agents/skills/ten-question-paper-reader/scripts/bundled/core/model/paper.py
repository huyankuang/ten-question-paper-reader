"""Data models for structured paper representation."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Term:
    """A detected technical term with its location in the paper."""
    name: str
    definition: str = ""
    section: str = ""
    page: int = 0
    context: str = ""


@dataclass
class PaperSection:
    """A logical section of the paper."""
    title: str
    text: str
    start_page: int = 0
    end_page: int = 0


@dataclass
class Caption:
    """A figure/table caption extracted verbatim from the PDF.

    Used to give the LLM real Figure/Table numbers so chart analysis
    references actual captions instead of hallucinated indices.
    """
    number: str          # e.g. "Fig. 3" / "Table 2" / "图3"
    kind: str           # "figure" | "table"
    text: str = ""      # caption text after the number
    page: int = 0


@dataclass
class Paper:
    """Structured representation of an academic paper."""
    title: str = ""
    authors: str = ""
    abstract: str = ""
    full_text: str = ""
    total_pages: int = 0
    sections: List[PaperSection] = field(default_factory=list)
    terms: List[Term] = field(default_factory=list)
    captions: List[Caption] = field(default_factory=list)
    source_path: str = ""

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "full_text": self.full_text,
            "total_pages": self.total_pages,
            "source_path": self.source_path,
            "sections": [
                {"title": s.title, "text": s.text[:2000], "start_page": s.start_page}
                for s in self.sections
            ],
            "terms": [
                {"name": t.name, "definition": t.definition, "section": t.section, "page": t.page}
                for t in self.terms
            ],
            "captions": [
                {"number": c.number, "kind": c.kind, "text": c.text, "page": c.page}
                for c in self.captions
            ],
        }
