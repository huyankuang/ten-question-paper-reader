"""Ten-question answer generator."""
from typing import List
import json

from core.config import TEN_QUESTIONS, PDF_CHUNK_SIZE
from core.model.paper import Paper
from core.model.note import Note, QAPair
from core.llm.client import chat
from core.llm.prompt_templates import SYSTEM_PROMPT, SHORT_SYSTEM_PROMPT


def _build_paper_context(paper: Paper) -> str:
    """Truncate paper text to fit context window (MVP: first ~12k chars)."""
    parts = [f"标题：{paper.title}", ""]
    if paper.abstract:
        parts.append(f"【摘要】\n{paper.abstract}")
        parts.append("")
    # Include first 12000 chars of full text.
    budget = 12000
    body = paper.full_text[:budget]
    parts.append(f"【正文节选】\n{body}")
    return "\n".join(parts)


def generate_answers(paper: Paper) -> Note:
    """Generate both short and full answers for all ten questions."""
    context = _build_paper_context(paper)
    note = Note(paper_title=paper.title)

    # Full answers in one call (more cost-effective).
    numbered = "\n".join(f"Q{q['id']}. {q['question']}（{q['type']}）" for q in TEN_QUESTIONS)
    user_prompt = (
        f"论文内容如下：\n{context}\n\n"
        f"请依次回答以下十个问题，每个问题用【Q1】【Q2】...作为分隔：\n{numbered}\n\n"
        f"每个问题请输出两部分：\n"
        f"【精简版】1-2句话核心结论\n"
        f"【详细版】展开回答，保留关键数据，并标注原文定位。"
    )
    reply = chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])

    parsed = _parse_reply(reply)
    for q in TEN_QUESTIONS:
        qa = QAPair(
            id=q["id"],
            question=q["question"],
            type=q["type"],
        )
        if q["id"] in parsed:
            qa.short_answer = parsed[q["id"]].get("short", "")
            qa.full_answer = parsed[q["id"]].get("full", "")
        # Extract citation if present.
        if "【原文定位】" in qa.full_answer:
            qa.citation = qa.full_answer.split("【原文定位】")[-1].split("\n")[0].strip()
        note.qa_pairs.append(qa)

    # Glossary from detected terms.
    note.glossary = {t.name: t.definition for t in paper.terms if t.definition}
    return note


def _parse_reply(reply: str) -> dict:
    """Split LLM reply by 【Qn】 markers."""
    out = {}
    blocks = reply.split("【Q")
    for block in blocks[1:]:
        try:
            qid = int(block.split("】")[0].strip())
        except ValueError:
            continue
        body = block.split("】", 1)[-1] if "】" in block else block
        short = ""
        full = ""
        if "【精简版】" in body:
            short = body.split("【精简版】")[-1].split("【详细版】")[0].strip()
        if "【详细版】" in body:
            full = body.split("【详细版】")[-1].strip()
        out[qid] = {"short": short, "full": full}
    return out
