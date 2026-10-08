"""Ten-question answer generator (v0.2)."""
from typing import List, Dict
import re

from core.config import TEN_QUESTIONS
from core.model.paper import Paper
from core.model.note import Note, QAPair, FigureNote
from core.llm.client import chat
from core.llm.prompt_templates import SYSTEM_PROMPT


def _build_paper_context(paper: Paper) -> str:
    """Truncate paper text to fit context window."""
    parts = [f"标题：{paper.title}", ""]
    if paper.abstract:
        parts.append(f"【摘要】\n{paper.abstract}")
        parts.append("")
    body = paper.full_text[:12000]
    parts.append(f"【正文节选】\n{body}")
    if paper.captions:
        lines = ["【已识别图表清单】（重点图表编号只能从中选）："]
        for c in paper.captions[:25]:
            lines.append(f"- {c.number}（p.{c.page}）: {c.text[:120]}")
        parts.append("\n".join(lines))
    return "\n".join(parts)


def generate_answers(paper: Paper) -> Note:
    """Generate short + full answers for all ten questions, plus
    experiment-setup summary and key-figure walkthrough."""
    context = _build_paper_context(paper)
    note = Note(paper_title=paper.title)

    numbered = "\n".join(
        f"Q{q['id']}. {q['question']}（{q['type']}）" for q in TEN_QUESTIONS
    )
    user_prompt = (
        f"论文内容如下：\n{context}\n\n"
        f"请依次回答以下十个问题，每问以【Q1】【Q2】...作为分隔标记：\n{numbered}\n\n"
        f"严格按系统提示规定的字段格式输出（精简版/详细版/原文定位/置信度/本问术语），"
        f"十问结束后再输出【实验准备与流程】和【重点图表】两个附加模块。"
    )
    reply = chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])

    note.experiment_setup = _extract_tail_block(reply, "实验准备与流程", ["重点图表"])
    note.key_figures = _parse_key_figures(reply)

    parsed = _parse_qa_blocks(reply)
    for q in TEN_QUESTIONS:
        qa = QAPair(id=q["id"], question=q["question"], type=q["type"])
        data = parsed.get(q["id"], {})
        qa.short_answer = data.get("short", "")
        qa.full_answer = data.get("full", "")
        qa.citation = data.get("citation", "") or "原文未明确"
        qa.confidence = data.get("confidence", "") or "中"
        qa.inline_terms = data.get("inline_terms", {})
        note.qa_pairs.append(qa)

    # 兜底：未被任何问题覆盖的预置术语解释。
    note.glossary = {t.name: t.definition for t in paper.terms if t.definition}
    return note


def _slice(text: str, start: str, ends: List[str]) -> str:
    """Extract text between `start` marker and the earliest of `ends` markers."""
    if start not in text:
        return ""
    rest = text.split(start, 1)[1]
    cut = len(rest)
    for em in ends:
        idx = rest.find(em)
        if idx != -1:
            cut = min(cut, idx)
    return rest[:cut].strip()


def _parse_qa_blocks(reply: str) -> Dict[int, dict]:
    """Split reply by 【Qn】 and extract each field."""
    out: Dict[int, dict] = {}
    # Cut off trailing special modules so they don't leak into Q10.
    body = reply.split("【实验准备与流程】")[0]
    for chunk in body.split("【Q")[1:]:
        try:
            qid = int(chunk.split("】", 1)[0].strip())
        except ValueError:
            continue
        block = chunk.split("】", 1)[-1] if "】" in chunk else chunk
        short = _slice(block, "【精简版】", ["【详细版】"])
        full = _slice(block, "【详细版】", ["【原文定位】"])
        citation = _slice(block, "【原文定位】", ["【置信度】"])
        confidence = _slice(block, "【置信度】", ["【本问术语】"])
        inline_raw = _slice(block, "【本问术语】", [])
        inline_terms: Dict[str, str] = {}
        for line in inline_raw.splitlines():
            line = line.strip().lstrip("-•* ").strip()
            if not line:
                continue
            m = re.match(r"^([^：:]{1,40})[：:]\s*(.+)$", line)
            if m:
                inline_terms[m.group(1).strip()] = m.group(2).strip()
        out[qid] = {
            "short": short, "full": full, "citation": citation,
            "confidence": confidence, "inline_terms": inline_terms,
        }
    return out


def _extract_tail_block(reply: str, name: str, next_blocks: List[str]) -> str:
    return _slice(reply, f"【{name}】", [f"【{n}】" for n in next_blocks])


def _parse_key_figures(reply: str) -> List[FigureNote]:
    """Parse the 【重点图表】 module into structured entries."""
    block = _extract_tail_block(reply, "重点图表", [])
    if not block:
        return []
    notes: List[FigureNote] = []
    # Split into chunks starting with 【Fig./Table/图/表 ...】
    chunks = re.split(r"(?=【(?:Fig\.?|Figure|Table|Tab\.?|图|表)\s*\d)", block)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk.startswith("【"):
            continue
        number = chunk[1: chunk.index("】")].strip() if "】" in chunk else ""
        rest = chunk.split("】", 1)[-1] if "】" in chunk else chunk
        why = _slice(rest, "为什么重点看", ["读图要点", "为什么"]).lstrip("：: ").strip()
        takeaway = _slice(rest, "读图要点", ["【"]).lstrip("：: ").strip()
        kind = "table" if re.match(r"(?i)^(table|tab|表)", number) else "figure"
        notes.append(FigureNote(number=number, kind=kind, why_focus=why, takeaway=takeaway))
    return notes
