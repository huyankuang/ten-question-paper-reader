---
name: ten-question-paper-reader
description: 用「十问精读法」结构化拆解工科论文 PDF（v0.2：新十问框架，含选题方向/值得精读部分/顶刊论文推荐；术语就地随查；实验流程与重点图表导览；引导用户写自述并做四维度评价）。当用户给出论文 PDF 并说"精读/拆解/读这篇论文/做文献笔记/十问"时使用。不依赖 VS Code，全程本地 Python 脚本。
---

# 十问文献精读器（Ten-Question Paper Reader）v0.2

不是替用户总结论文，而是带用户完成「拆解 → 对照原文 → 自己总结 → AI 评价」的闭环训练。

## 何时使用

- 用户提供一篇论文 PDF（路径或拖入对话），想读/拆解/做笔记。
- 用户提到"十问精读""精读论文""文献拆解""读这篇 paper"。

## 前置环境检查（每次新会话先确认）

1. Python 3.9+ 可用：`python --version`
2. 依赖已装：`python -c "import pymupdf, openai"`，缺则先 `pip install -r requirements.txt`（在 skill 的 `scripts/` 旁）。
3. LLM 凭证：`OPENAI_API_KEY` 环境变量已设置；如需国内代理再设 `OPENAI_BASE_URL` 与 `TQPR_OPENAI_MODEL`。
   - 若用户未配置 key：脚本会优雅降级，返回提示文本而非崩溃；此时把脚本解析出的论文标题/摘要/章节/图表清单直接交给对话模型（你自己）按框架作答，不必报错中断。

## 运行方式

所有命令统一通过 skill 自带启动脚本执行（脚本内部用 `__file__` 自定位运行时，不依赖当前工作目录），**不要手写 `python -m core.cli`**。

约定：`SKILL_ROOT` = 本 SKILL.md 所在目录（即包含 `scripts/` 的那一层）。启动脚本路径为 `<SKILL_ROOT>/scripts/tqpr.py`。按当前 shell 选择写法：

```bash
# bash / zsh（macOS、Linux、Git Bash）
python "$SKILL_ROOT/scripts/tqpr.py" parse --pdf <论文.pdf>
python "$SKILL_ROOT/scripts/tqpr.py" generate --paper paper.json
python "$SKILL_ROOT/scripts/tqpr.py" evaluate --note note.json --summary @my_summary.txt
```

```powershell
# PowerShell（Windows）
python "$SKILL_ROOT\scripts\tqpr.py" parse --pdf <论文.pdf>
python "$SKILL_ROOT\scripts\tqpr.py" generate --paper paper.json
python "$SKILL_ROOT\scripts\tqpr.py" evaluate --note note.json --summary "@my_summary.txt"
```

三个子命令依次是：① 解析 PDF → `paper.json`；② 生成十问答案 + 实验流程 + 图表导览 → `note.json`；③ 评价用户自述。`@文件路径` 表示从文件读取正文，直接传字符串也行。

## 标准工作流（按此顺序推进，不要跳步）

1. **解析**：跑 `parse`，stdout 的 JSON 写到 `paper.json`。确认标题、页数、章节、识别到的图表清单（captions）。
2. **生成十问答案**：跑 `generate`，输出 `note.json`。然后按下面结构整理成中文清单呈现：
   - Q1–Q10 每问：精简版 + 详细版 + **原文定位** + **置信度**，本问涉及的术语就地附上解释（🔖 随查），不要把术语堆到最后；
   - **实验准备与流程**：要点式讲清材料/设备/工况/变量/步骤；
   - **重点图表导览**：列出 2–4 个真实 Fig./Table 编号，告诉用户每张重点看什么、读出什么结论。
3. **引导用户自己写总结**：**不要让用户写一段散文**。把 references 里的 5 条自述引导问题逐条贴给他，让他按条作答：
   ① 问题/方法/关键数据/结论一句话说清；② 结论在什么前提范围体系下成立；
   ③ 假设→设计→变量控制→数据→结论 的完整推理链；④ 最脆弱的数据/假设、复现先验证哪步；
   ⑤ 方法搬到自己研究对象上要改什么。把用户回答存成 `my_summary.txt`。
4. **评价**：跑 `evaluate`，把四维打分（问题与结论/方法与推理链/数据与边界/批判与迁移，各25分）、优点、不足、改进建议反馈给用户。
5. **落盘笔记**：按 `references/ten-questions.md` 里的 Markdown 结构（十问 → 实验流程 → 重点图表 → 我的总结 → AI评价）保存到用户当前目录。

## 硬性要求

- 每问必须带**置信度**和**原文定位**；图表编号只能来自 `paper.json` 的 captions 清单，不许编造 Fig./Table 号。
- AI 答案只是**初稿**：提醒用户"务必对照原文核对数据、公式与结论"，低置信度问题重点标注。
- 不要替用户写总结；总结必须用户自己产出，skill 只负责评价。
- PDF 文本在本地 PyMuPDF 解析，只有论文文本发给用户配置的 LLM；不要外发到未授权服务。
- 遇到降级文本时，改用你自己基于 `paper.json` 的摘要/正文/图表清单直接作答，并说明"未检测到 OPENAI_API_KEY，本次由当前对话模型直接精读"。

## 参考文件

- `references/ten-questions.md`：v0.2 十问框架、输出 Markdown 模板、5 条自述引导问题、评价维度。
- `scripts/bundled/core/`：自包含 Python 运行时（core 包副本），skill 被拷到任何 agent 的用户级目录（`~/.agents/skills/`、`~/.codex/skills/`、`~/.claude/skills/` 等）单独使用时由它兜底。
