"""Ten-question answer generator (v0.3: JSON-first parsing with text fallback)."""
from typing import List, Dict
import json
import re

from core.config import TEN_QUESTIONS
from core.model.paper import Paper
from core.model.note import Note, QAPair, FigureNote
from core.llm.client import chat
from core.llm.prompt_templates import SYSTEM_PROMPT


def _build_paper_context(paper: Paper) -> str:
    """Build LLM context: abstract + key sections (method/results/conclusion) + captions.

    Replaces the old hard 12k-char truncation which dropped everything after
    the intro on long engineering papers.
    """
    parts = [f"标题：{paper.title}", ""]
    if paper.abstract:
        parts.append(f"【摘要】\n{paper.abstract}")
        parts.append("")

    # Prefer section-based extraction (method/results/discussion/conclusion).
    picked = []
    for s in paper.sections:
        t = s.title.lower()
        if any(k in t for k in ("method", "experimental", "result", "discussion",
                                "conclusion", "实验", "试验", "方法", "结果", "讨论", "结论")):
            picked.append(s.text[:2500])
    if picked:
        parts.append("【正文关键章节节选】")
        for p in picked[:6]:
            parts.append(p)
            parts.append("")
    else:
        # Fallback: no sections detected (e.g. Chinese paper with odd layout).
        parts.append(f"【正文节选】\n{paper.full_text[:8000]}")

    if paper.captions:
        lines = ["【已识别图表清单】（重点图表编号只能从中选）："]
        for c in paper.captions[:25]:
            lines.append(f"- {c.number}（p.{c.page}）: {c.text[:120]}")
        parts.append("\n".join(lines))
    return "\n".join(parts)


def generate_answers(paper: Paper) -> Note:
    """Generate ten Q&A + experiment setup + key figures.

    Parsing strategy: JSON-first → markdown-fenced JSON → 【Qn】text fallback →
    raw-reply fallback (never return an empty note on format drift).
    """
    context = _build_paper_context(paper)
    note = Note(paper_title=paper.title)

    numbered = "\n".join(
        f"Q{q['id']}. {q['question']}（{q['type']}）" for q in TEN_QUESTIONS
    )
    user_prompt = (
        f"论文内容如下：\n{context}\n\n"
        f"请严格按系统提示规定的 JSON 结构回答以上十个问题，"
        f"qa_pairs 数组必须包含 id 1 到 10 共十个对象。"
    )
    reply = chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])

    data = _try_json(reply)
    if data is None:
        # Fallback: old 【Qn】text format (tolerates format drift).
        data = _text_to_dict(reply)

    # Populate note from parsed dict.
    qa_by_id = {item.get("id"): item for item in data.get("qa_pairs", []) if isinstance(item, dict)}
    for q in TEN_QUESTIONS:
        qa = QAPair(id=q["id"], question=q["question"], type=q["type"])
        d = qa_by_id.get(q["id"], {})
        qa.short_answer = (d.get("short") or "").strip()
        qa.full_answer = (d.get("full") or "").strip()
        qa.citation = (d.get("citation") or "").strip() or "原文未明确"
        qa.confidence = (d.get("confidence") or "").strip() or "中"
        it = d.get("inline_terms") or {}
        if isinstance(it, dict):
            qa.inline_terms = {str(k): str(v) for k, v in it.items()}
        note.qa_pairs.append(qa)

    note.experiment_setup = (data.get("experiment_setup") or "").strip()
    note.key_figures = []
    for f in data.get("key_figures", []) or []:
        if not isinstance(f, dict):
            continue
        num = str(f.get("number", "")).strip()
        if not num:
            continue
        kind = "table" if re.match(r"(?i)^(table|tab|表)", num) else "figure"
        note.key_figures.append(FigureNote(
            number=num, kind=kind,
            why_focus=str(f.get("why_focus", "")).strip(),
            takeaway=str(f.get("takeaway", "")).strip(),
        ))

    # Final safety net: if NOTHING was parsed, dump raw reply into Q10's full
    # answer so the user sees something instead of an all-empty note.
    if not qa_by_id and not note.experiment_setup:
        note.qa_pairs[-1].full_answer = (
            "【警告：本次模型输出未遵循 JSON 格式，以下为原始输出】\n\n" + reply
        )
        note.qa_pairs[-1].confidence = "低"
        note.qa_pairs[-1].citation = "格式解析失败，原文定位不可用"

    note.glossary = {t.name: t.definition for t in paper.terms if t.definition}
    return note


def _try_json(reply: str):
    """Try to parse reply as JSON, tolerating ```json fences and leading/trailing prose."""
    candidates = [reply.strip()]
    # Strip ```json ... ``` fences if present.
    m = re.search(r"```(?:json)?\s*(.*?)```", reply, re.DOTALL)
    if m:
        candidates.append(m.group(1).strip())
    for cand in candidates:
        try:
            return json.loads(cand)
        except (json.JSONDecodeError, ValueError):
            continue
    return None


def _text_to_dict(reply: str) -> dict:
    """Legacy 【Qn】text fallback. Tolerates missing markers and minor drift."""
    out: Dict[int, dict] = {}
    body = re.split(r"【?实验准备与流程】?", reply, maxsplit=1)[0]

    # Find all Qn marker positions: 【Q1】, [Q1], **Q1**, "Q1." variants.
    marker_re = re.compile(r"【?\*{0,2}Q(\d+)\*{0,2}】?")
    matches = list(marker_re.finditer(body))
    for idx, m in enumerate(matches):
        qid = int(m.group(1))
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        block = body[m.end():end]
        short = _slice(block, "【精简版】", ["【详细版】", "【总结】"])
        full = _slice(block, "【详细版】", ["【原文定位】", "【定位】"])
        citation = _slice(block, "【原文定位】", ["【置信度】", "【可信】"])
        confidence = _slice(block, "【置信度】", ["【本问术语】", "【术语】"])
        inline_raw = _slice(block, "【本问术语】", [])
        inline_terms: Dict[str, str] = {}
        for line in inline_raw.splitlines():
            line = line.strip().lstrip("-•* ").strip()
            if not line:
                continue
            m2 = re.match(r"^([^：:]{1,40})[：:]\s*(.+)$", line)
            if m2:
                inline_terms[m2.group(1).strip()] = m2.group(2).strip()
        out[qid] = {
            "short": short, "full": full, "citation": citation,
            "confidence": confidence, "inline_terms": inline_terms,
        }

    # Tail modules.
    experiment = _slice(reply, "【实验准备与流程】", ["【重点图表】", "【重点图】"])
    key_figures_block = _slice(reply, "【重点图表】", [])

    key_figures = []
    for chunk in re.split(r"(?=【(?:Fig\.?|Figure|Table|Tab\.?|图|表)\s*\d)", key_figures_block):
        chunk = chunk.strip()
        if not chunk.startswith("【"):
            continue
        number = chunk[1: chunk.index("】")].strip() if "】" in chunk else ""
        rest = chunk.split("】", 1)[-1] if "】" in chunk else chunk
        why = _slice(rest, "为什么重点看", ["读图要点"]).lstrip("：: ").strip()
        takeaway = _slice(rest, "读图要点", ["【"]).lstrip("：: ").strip()
        key_figures.append({"number": number, "why_focus": why, "takeaway": takeaway})

    return {
        "qa_pairs": [{"id": k, **v} for k, v in out.items()],
        "experiment_setup": experiment,
        "key_figures": key_figures,
    }


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
