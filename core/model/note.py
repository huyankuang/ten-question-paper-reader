"""Data models for the reading note output (v0.2)."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class QAPair:
    """One question-answer pair in the ten-question framework."""
    id: int
    question: str
    type: str
    short_answer: str = ""          # 1-2 sentence summary
    full_answer: str = ""           # detailed answer
    citation: str = ""              # e.g. "第2节, 第8页, 表4"
    confidence: str = "中"          # 高 / 中 / 低
    # v0.2: 术语解释就地附在本问后面，随用随查，不再集中放最后。
    inline_terms: Dict[str, str] = field(default_factory=dict)


@dataclass
class FigureNote:
    """One key figure/table the reader must look at."""
    number: str                     # "Fig. 3" / "Table 2" / "图3"
    kind: str = "figure"            # figure / table
    why_focus: str = ""             # 为什么这张必须重点看
    takeaway: str = ""              # 读图/读表要点、应读出什么结论


@dataclass
class Evaluation:
    """AI evaluation of the user's self-summary."""
    score: int = 0                  # 0-100
    dimension_scores: Dict[str, int] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class Note:
    """Final reading note combining AI answers, user summary, and evaluation."""
    paper_title: str = ""
    qa_pairs: List[QAPair] = field(default_factory=list)
    # v0.2: 十问之外补充的两个工科生最缺的模块
    experiment_setup: str = ""      # 实验准备与流程（简洁要点式）
    key_figures: List[FigureNote] = field(default_factory=list)
    user_summary: str = ""
    evaluation: Optional[Evaluation] = None
    # 兜底全局术语表（v0.2 主打 inline_terms，这里仅收录未被任何问题覆盖的术语）
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
            if qa.inline_terms:
                lines.append("")
                lines.append("**🔖 本问术语随查**：")
                for term, definition in qa.inline_terms.items():
                    lines.append(f"- **{term}**：{definition}")
            lines.append("")

        if self.experiment_setup:
            lines.append("## 二、实验准备与流程")
            lines.append("")
            lines.append(self.experiment_setup.strip())
            lines.append("")

        if self.key_figures:
            lines.append("## 三、重点图表导览（工科生必看）")
            lines.append("")
            for f in self.key_figures:
                kind_label = "图" if f.kind == "figure" else "表"
                lines.append(f"### {f.number}（{kind_label}）")
                if f.why_focus:
                    lines.append(f"- **为什么重点看**：{f.why_focus}")
                if f.takeaway:
                    lines.append(f"- **读图要点**：{f.takeaway}")
                lines.append("")

        lines.append("## 我的总结（合上 AI 答案，自己写）")
        lines.append("")
        if self.user_summary:
            lines.append(self.user_summary)
        else:
            lines.append("_（待填写）_")
        lines.append("")

        if self.evaluation:
            lines.append("## AI 评价")
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
            lines.append("## 附：其余术语")
            for term, definition in self.glossary.items():
                lines.append(f"- **{term}**：{definition}")
        return "\n".join(lines)
