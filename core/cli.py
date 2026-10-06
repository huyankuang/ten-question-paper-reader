"""Command-line entry point for the Ten-Question Paper Reader.

Usage:
    python -m core.cli parse --pdf <path>         # parse PDF → JSON
    python -m core.cli generate --paper <json>   # generate ten Q&A
    python -m core.cli evaluate --note <json> --summary <text>
"""
import argparse
import json
import sys
import os

# Allow running as `python core/cli.py` without installing the package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pdf_parser import extract_paper, detect_terms
from core.llm import generate_answers, evaluate_summary
from core.model.note import Note, QAPair


def cmd_parse(args):
    paper = extract_paper(args.pdf)
    detect_terms(paper, args.pdf)
    print(json.dumps(paper.to_dict(), ensure_ascii=False, indent=2))


def cmd_generate(args):
    with open(args.paper, "r", encoding="utf-8") as f:
        paper_dict = json.load(f)
    # Minimal reconstruction — we only need title + full_text for LLM context.
    from core.model.paper import Paper
    paper = Paper(
        title=paper_dict.get("title", ""),
        abstract=paper_dict.get("abstract", ""),
        full_text=paper_dict.get("full_text", ""),
        source_path=paper_dict.get("source_path", ""),
    )
    # If full_text wasn't saved in the dict, re-extract from source.
    if not paper.full_text and paper.source_path:
        paper = extract_paper(paper.source_path)
    detect_terms(paper, paper.source_path)

    note = generate_answers(paper)
    print(json.dumps({
        "paper_title": note.paper_title,
        "qa_pairs": [
            {
                "id": qa.id, "question": qa.question, "type": qa.type,
                "short_answer": qa.short_answer, "full_answer": qa.full_answer,
                "citation": qa.citation, "confidence": qa.confidence,
            } for qa in note.qa_pairs
        ],
        "glossary": note.glossary,
    }, ensure_ascii=False, indent=2))


def cmd_evaluate(args):
    with open(args.note, "r", encoding="utf-8") as f:
        note_dict = json.load(f)
    note = Note(paper_title=note_dict.get("paper_title", ""))
    note.qa_pairs = [
        QAPair(
            id=q["id"], question=q["question"], type=q.get("type", ""),
            short_answer=q.get("short_answer", ""), full_answer=q.get("full_answer", ""),
        ) for q in note_dict.get("qa_pairs", [])
    ]
    summary = args.summary
    if summary.startswith("@"):
        with open(summary[1:], "r", encoding="utf-8") as f:
            summary = f.read()
    ev = evaluate_summary(note, summary)
    print(json.dumps({
        "score": ev.score,
        "dimension_scores": ev.dimension_scores,
        "strengths": ev.strengths,
        "weaknesses": ev.weaknesses,
        "suggestions": ev.suggestions,
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(prog="tqpr")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_parse = sub.add_parser("parse", help="Parse PDF into structured JSON")
    p_parse.add_argument("--pdf", required=True)
    p_parse.set_defaults(func=cmd_parse)

    p_gen = sub.add_parser("generate", help="Generate ten-question answers")
    p_gen.add_argument("--paper", required=True, help="Path to paper JSON")
    p_gen.set_defaults(func=cmd_generate)

    p_eval = sub.add_parser("evaluate", help="Evaluate user summary")
    p_eval.add_argument("--note", required=True)
    p_eval.add_argument("--summary", required=True, help="Text or @filepath")
    p_eval.set_defaults(func=cmd_evaluate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
