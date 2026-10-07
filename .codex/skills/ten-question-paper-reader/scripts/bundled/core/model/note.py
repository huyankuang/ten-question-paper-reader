"""Data models for the reading note output."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class QAPair:
    """One question-answer pair in the ten-question framework."""
    id: int
    question: str
    type: str
    short_answer: str = ""      # 1-2 sentence summary
    full_answer: str = ""       # detailed answer
    citation: str = ""          # e.g. "第2章 Stage 5, 第8页, 表4"
    confidence: str = "中"      # 高 / 中 / 低


@dataclass
class Evaluation:
    """AI evaluation of the user's self-summary."""
    score: int = 0              # 0-100
    dimension_scores: Dict[str, int] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class Note:
    """Final reading note combining AI answers, user summary, and evaluation."""
    paper_title: str = ""
    qa_pairs: List[QAPair] = field(default_factory=list)
    user_summary: str = ""
    evaluation: Optional[Evaluation] = None
    glossary: Dict[str, str] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [f"# 精读笔记：{self.paper_title}", ""]
        lines.append("## 一、十问拆解")
        lines.append("")
        for qa in self.qa_pairs:
            lines.append(f"### Q{qa.id}. {qa.question}")
            lines.append(f"- **类型**：{qa.type}  ")
            lines.append(f"- **置信度**：{qa.confidence}  ")
            lines.append(f"- **原文定位**：{qa.citation}  ")
            lines.append(f"- **精简版**：{qa.short_answer}  ")
            lines.append("")
            lines.append(f"**详细回答**：")
            lines.append(qa.full_answer)
            lines.append("")
        if self.user_summary:
            lines.append("## 二、我的总结")
            lines.append(self.user_summary)
            lines.append("")
        if self.evaluation:
            lines.append("## 三、AI评价")
            lines.append(f"- **总分**：{self.evaluation.score}/100")
            for k, v in self.evaluation.dimension_scores.items():
                lines.append(f"  - {k}：{v}/25")
            lines.append("")
            lines.append("**优点**：")
            for s in self.evaluation.strengths:
                lines.append(f"- {s}")
            lines.append("")
            lines.append("**改进建议**：")
            for s in self.evaluation.suggestions:
                lines.append(f"- {s}")
            lines.append("")
        if self.glossary:
            lines.append("## 四、核心术语表")
            for term, definition in self.glossary.items():
                lines.append(f"- **{term}**：{definition}")
        return "\n".join(lines)
