---
name: ten-question-paper-reader
description: 用「十问精读法」结构化拆解一篇学术论文 PDF，生成双层（精简版+带原文定位的详细版）十问答案、术语表，并对用户自己写的总结做四维度 AI 评价。当用户给出论文 PDF 路径并说"精读/拆解/读这篇论文/做文献笔记/十问"时使用；也适用于工科研究生需要把论文从"看摘要"升级为"按框架拆解+对照原文校验+自己总结"的场景。不依赖 VS Code，全程通过本地 Python 脚本运行。
---

# 十问文献精读器（Ten-Question Paper Reader）

不是替用户总结论文，而是带用户完成「拆解 → 对照原文 → 自己总结 → AI 评价」的闭环训练。

## 何时使用

- 用户提供一篇论文 PDF（路径或拖入对话），想读/拆解/做笔记。
- 用户提到"十问精读""精读论文""文献拆解""读这篇 paper"。

## 前置环境检查（每次新会话先确认）

1. Python 3.9+ 可用：`python --version`
2. 依赖已装：`python -c "import fitz, openai"`，缺则先 `pip install -r requirements.txt`（requirements.txt 在 skill 的 `scripts/` 旁）。
3. LLM 凭证：`OPENAI_API_KEY` 环境变量已设置；如需国内代理再设 `OPENAI_BASE_URL` 与 `TQPR_OPENAI_MODEL`。
   - 若用户未配置 key：脚本会优雅降级，返回提示文本而非崩溃；此时把脚本解析出的论文标题/摘要/章节结构直接交给对话模型（你自己）来按十问框架作答即可，不必报错中断。

## 运行方式

所有命令统一通过 skill 自带的启动脚本执行，脚本会自动定位 Python 运行时（优先仓库根 `core/`，找不到则用 skill 内 bundled 副本），**不要手写 `python -m core.cli`**：

```bash
# 设 SKILL_DIR 为本 SKILL.md 所在目录（含 scripts/ 的那一层）
python "$SKILL_DIR/scripts/tqpr.py" parse --pdf <论文.pdf>        # ① 解析 PDF → paper.json
python "$SKILL_DIR/scripts/tqpr.py" generate --paper paper.json    # ② 调 LLM 生成十问答案 → note.json
python "$SKILL_DIR/scripts/tqpr.py" evaluate --note note.json --summary @my_summary.txt  # ③ 评价用户自己写的总结
```

`@文件路径` 表示从文件读取总结正文；直接传字符串也行。

## 标准工作流（按此顺序推进，不要跳步）

1. **解析**：跑 `parse`，把 stdout 的 JSON 写到当前工作目录的 `paper.json`。从中确认标题、页数、识别到的章节和术语。
2. **生成十问答案**：跑 `generate`（首次约 30–60 秒），输出存为 `note.json`。然后**把结果整理成中文清单呈现给用户**：每问给「1–2 句精简版」，并附上详细版里的原文定位（第 X 节/页/表/图）。十问框架详表见 `references/ten-questions.md`。
3. **请用户自己总结**：明确告诉用户"现在合上 AI 答案，按十问框架用自己的话写一段总结"。把用户写的总结存成 `my_summary.txt`。
4. **评价**：跑 `evaluate`，把四维打分（各 25 分）、优点、不足、改进建议反馈给用户。
5. **落盘笔记**：用 `note.json` + 用户总结 + 评价，生成一份 Markdown 精读笔记保存到用户当前目录（可用 `core/model/note.py` 里 `Note.to_markdown()` 的结构，或直接按 references 里的模板写）。

## 硬性要求

- AI 答案只是**初稿**：每次呈现时都要提醒用户"务必对照原文核对数据、公式与结论"，低置信度问题重点标注。
- 不要替用户写总结；总结必须由用户自己产出，skill 只负责评价。
- PDF 文本在本地用 PyMuPDF 解析，只有论文文本发给用户配置的 LLM；不要把整篇论文外发到未经用户授权的服务。
- 遇到 `generate` 返回"【未配置API Key】"之类降级文本时，改用你自己（对话模型）基于 `paper.json` 里的摘要与正文节选直接作答，并在开头说明"未检测到 OPENAI_API_KEY，本次由当前对话模型直接精读"。

## 参考文件

- `references/ten-questions.md`：十问框架完整定义、每问类型、输出 Markdown 模板。
- `scripts/bundled/core/`：自包含 Python 运行时（core 包副本），skill 被拷贝到 `~/.codex/skills/` 单独使用时由它兜底。
