# AGENTS.md — 给 Codex / AI 代理的仓库说明

本仓库是「十问文献精读器」：一个用十问精读法结构化拆解学术论文 PDF 的工具。

## 首选使用方式：作为 Codex Skill（无需 VS Code）

本仓库已内置一个 Codex Agent Skill，打开本目录后 Codex 即可直接识别：

```
.codex/skills/ten-question-paper-reader/
├── SKILL.md                  # 触发描述 + 工作流指令
├── agents/openai.yaml
├── scripts/tqpr.py          # 自定位启动入口
├── scripts/bundled/core/     # 自包含 Python 运行时（兜底）
└── references/ten-questions.md
```

当用户给出论文 PDF 并要求精读时，**优先读取 `.codex/skills/ten-question-paper-reader/SKILL.md`** 并按其中三步流水线执行（parse → generate → evaluate），不要再要求用户用 VS Code 按 F5 启动扩展开发宿主。

## 直接命令行（不开任何 IDE）

```powershell
# 在仓库根目录
python .codex/skills/ten-question-paper-reader/scripts/tqpr.py parse --pdf <paper.pdf> > paper.json
python .codex/skills/ten-question-paper-reader/scripts/tqpr.py generate --paper paper.json > note.json
python .codex/skills/ten-question-paper-reader/scripts/tqpr.py evaluate --note note.json --summary @my_summary.txt
```

等价的裸命令是 `python -m core.cli ...`（需要 cwd 在仓库根）。

## 环境

- Python 3.9+，依赖：`pip install -r requirements.txt`（pymupdf、openai）
- LLM：`OPENAI_API_KEY` 环境变量；可选 `OPENAI_BASE_URL`、`TQPR_OPENAI_MODEL`
- 未配置 Key 时脚本会优雅降级（返回提示文本而非崩溃），此时由当前对话模型直接按十问框架作答。

## 目录速览

- `core/` — 跨客户端复用的 Python 逻辑（PDF 解析、LLM 调用、十问生成、评价）
- `plugins/vscode-codex/` — 旧的 VS Code 侧边栏扩展（已修复 core/ 定位逻辑；仅在需要 GUI 面板时使用）
- `docs/` — 用户/开发指南
- `examples/` — 示例精读笔记

## 修改约束

- 改 `core/` 后，**必须同步**复制到 `.codex/skills/ten-question-paper-reader/scripts/bundled/core/`，否则脱离仓库单独使用 skill 时会跑旧代码。
- 不要在 VS Code 扩展里再硬编码相对路径定位 core/；统一用扩展内新增的 `resolveCoreRoot()` 解析器（向上探查 + 工作区回退 + `tqpr.corePath` 配置项兜底）。
