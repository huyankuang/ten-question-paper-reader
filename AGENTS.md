# AGENTS.md — 给 AI 代理（Codex / Claude / Gemini / Copilot / Cursor）的仓库说明

本仓库是「十问文献精读器」：一个用十问精读法结构化拆解学术论文 PDF 的工具。

## 首选使用方式：作为 Agent Skill（无需 VS Code）

本仓库内置同一份 skill 的**多平台副本**，内容完全一致：

```
.agents/skills/ten-question-paper-reader/   # ← 主版本（厂商中立路径，改这里）
├── SKILL.md                  # 触发描述 + 工作流指令
├── agents/openai.yaml        # Codex 专属元数据，其他平台自动忽略
├── scripts/tqpr.py          # 自定位启动入口
├── scripts/bundled/core/     # 自包含 Python 运行时（兜底）
└── references/ten-questions.md
.claude/skills/ten-question-paper-reader/   # Claude Code 专用副本（Claude 不读 .agents）
.codex/skills/ten-question-paper-reader/  # Codex 旧版 / Cursor 兼容读取副本
```

各平台识别路径对照：

| 平台 | 识别路径 | 本仓库对应目录 |
|---|---|---|
| Codex CLI（新版） | `.agents/skills/` | `.agents/skills/` |
| Gemini CLI | `.gemini/skills/` 或 `.agents/skills/` | `.agents/skills/`（直接认） |
| VS Code Copilot / APM | `.agents/skills/` | `.agents/skills/`（直接认） |
| Claude Code | `.claude/skills/` | `.claude/skills/` |
| Cursor | `.cursor/skills/`，兼容读 `.claude/`、`.codex/` | `.codex/skills/`（直接认） |

当用户给出论文 PDF 并要求精读时，**优先读取本平台对应目录下的 `SKILL.md`**，按其中三步流水线执行（parse → generate → evaluate），不要要求用户用 VS Code 按 F5 启动扩展开发宿主。

## 直接命令行（不开任何 IDE）

```powershell
# 在仓库根目录（以 .agents 主版本为例）
python .agents/skills/ten-question-paper-reader/scripts/tqpr.py parse --pdf <paper.pdf> > paper.json
python .agents/skills/ten-question-paper-reader/scripts/tqpr.py generate --paper paper.json > note.json
python .agents/skills/ten-question-paper-reader/scripts/tqpr.py evaluate --note note.json --summary @my_summary.txt
```

等价的裸命令是 `python -m core.cli ...`（需要 cwd 在仓库根）。

## 环境

- Python 3.9+，依赖：`pip install -r requirements.txt`（pymupdf、openai）
- LLM：`OPENAI_API_KEY` 环境变量；可选 `OPENAI_BASE_URL`、`TQPR_OPENAI_MODEL`
- 未配置 Key 时脚本会优雅降级（返回提示文本而非崩溃），此时由当前对话模型直接按十问框架作答。

## 目录速览

- `core/` — 跨客户端复用的 Python 逻辑（PDF 解析、LLM 调用、十问生成、评价）
- `tools/sync-skills.ps1` — 把 `.agents/skills/` 主版本同步到 `.claude/` 与 `.codex/` 的脚本
- `plugins/vscode-codex/` — 旧的 VS Code 侧边栏扩展（已修复 core/ 定位；仅 GUI 需要时用）
- `docs/` — 用户/开发指南
- `examples/` — 示例精读笔记

## 修改约束

- 改 `core/` 后，**必须**：① 复制到 `.agents/skills/ten-question-paper-reader/scripts/bundled/core/`；② 运行 `powershell -File tools/sync-skills.ps1` 同步到 `.claude/` 与 `.codex/` 两处副本。三处哈希必须一致（用 `tools/_check_sigs.py` 校验）。
- 只在 `.agents/skills/ten-question-paper-reader/` 里改 SKILL.md / references，改完跑同步脚本，不要手改另外两处。
- 不要在 VS Code 扩展里硬编码相对路径定位 core/；统一用 `resolveCoreRoot()` 解析器（向上探查 + 工作区回退 + `tqpr.corePath` 配置兜底）。
