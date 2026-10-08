"""Evaluate user's self-summary against AI-generated reference answers."""
import json
import re

from core.model.note import Note, Evaluation
from core.llm.client import chat
from core.llm.prompt_templates import EVALUATION_PROMPT


def evaluate_summary(note: Note, user_summary: str) -> Evaluation:
    """Compare user summary with reference and return structured evaluation."""
    reference = "\n\n".join(
        f"Q{qa.id}: {qa.question}\n{qa.full_answer}" for qa in note.qa_pairs
    )
    prompt = EVALUATION_PROMPT.format(
        reference=reference,
        user_summary=user_summary,
    )
    reply = chat([
        {"role": "system", "content": "你是一个严格的JSON输出器。"},
        {"role": "user", "content": prompt},
    ])
    return _parse_evaluation(reply)


def _parse_evaluation(text: str) -> Evaluation:
    """Extract JSON from LLM reply."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return Evaluation(score=0, weaknesses=["无法解析AI评价结果"])
    try:
        data = json.loads(m.group(0))
        return Evaluation(
            score=data.get("score", 0),
            dimension_scores=data.get("dimension_scores", {}),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            suggestions=data.get("suggestions", []),
        )
    except json.JSONDecodeError:
        return Evaluation(score=0, weaknesses=["评价JSON解析失败"])
