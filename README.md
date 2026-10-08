# 十问文献精读器 Ten-Question Paper Reader

> **不是给你总结论文，而是教你拆解论文。**

面向工科研究生的**结构化文献半自助精读工具**。以「十问精读法」为核心方法论，把读论文从"看摘要"升级为"按框架拆解+对照原文校验+自己总结+AI评价"的闭环训练。

> ### 🆚 我直接把 PDF 丢给豆包/DeepSeek 不就行了？
> 真不一样。我们拿一篇真实论文（TC4 ELI 深海 SCC，*Materials Today Communications* 2026）做了并排对比：
> - [对照组：直接问 AI「总结一下」](./examples/demo/direct-ai-output.md) → 250 字流畅总结，读着爽，但没有原文定位、没有批判性追问、你全程没动脑。
> - [实验组：十问精读器输出](./examples/demo/tqpr-output.md) → 每问带页码定位+置信度，Q7/Q10 直接拆穿论文的软肋（氢没实测、n=2），Q8 给你 3 个可落地选题。
> - [并排对比分析](./examples/demo/COMPARISON.md)：哪个该看、为什么，一表说清。
>
> **直接把 PDF 丢给 AI = 看别人替你做的笔记；十问精读器 = AI 陪你做笔记并批改你的答案。**

---

## ✨ 核心特性

- **十问精读框架**：10个递进式问题，覆盖"是什么→为什么→怎么做→怎么用"完整认知链
- **双层答案**：每问自动生成「1-2句精简版」+「带原文定位的详细版」
- **交互式术语解释**：自动高亮专业术语，点击即出定义+原文页码
- **半自助总结闭环**：填空式模板 → 你自己写总结 → AI分维度评价 → 生成最终笔记
- **本地优先**：PDF在本地解析，保护未发表论文隐私

## 📋 十问框架（v0.2）

| # | 问题 | 类型 |
|---|------|------|
| 1 | 核心研究主题是什么？聚焦哪个具体问题？ | 客观提取 |
| 2 | 作者为什么做？前人留下什么缺口？ | 客观提取 |
| 3 | 整体技术路线？分哪几个步骤？ | 客观提取 |
| 4 | 核心方法/模型/实验？关键参数？ | 客观提取 |
| 5 | 主要结论与关键定量结果？ | 客观提取 |
| 6 | 核心创新点？和已有研究最大区别？ | 客观+分析 |
| 7 | 局限性？哪些因素没考虑到？ | 客观+分析 |
| 8 | 针对本文不足，提出三个可落地的后续选题方向 | 分析+应用 |
| 9 | 作为同方向研究生，哪些部分值得逐句精读？为什么？ | 分析+应用 |
| 10 | 结合本文方向，推荐 3–5 篇顶刊必读论文，说清核心贡献与阅读价值 | 分析+应用 |

> v0.2 新增：术语就地随查（不集中堆放）、十问后附「实验准备与流程」+「重点图表导览」两个模块、自述按 5 条引导问题逐条作答。

## 🚀 快速开始

> **v0.3 起，本项目已从「Codex 专属插件」改造为跨平台 Agent Skill：不再需要打开 VS Code，也不绑定某一家 agent。**
> 之前的 VSIX 单独安装后会报错，是因为插件把 Python `core/` 的位置硬编码为"扩展目录往上三级 = 仓库根"，
> 打包成 VSIX 后这个相对路径指向 VS Code 扩展安装目录，那里没有 `core/`。
> 现在同一份 skill 放在三个目录，主流 agent 打开本仓库即可直接识别（见下表）。

### 环境要求
- Python 3.9+（依赖：`pip install -r requirements.txt`，即 pymupdf、openai）
- OpenAI 兼容接口的 API Key（设为环境变量 `OPENAI_API_KEY`）
- **不需要 Node.js、不需要 VS Code**（仅在你想重新打包侧边栏插件时才需要 Node 18+）

### 方式一：在任意 AI Agent 里直接用（推荐）

本仓库内置**跨平台 Agent Skill**，同一份内容放在三个目录，覆盖主流 agent：

| 你用的 Agent | 识别路径 | 本仓库目录 |
|---|---|---|
| Codex CLI（新版）、Gemini CLI、VS Code Copilot | `.agents/skills/`（厂商中立） | `.agents/skills/ten-question-paper-reader/` |
| Claude Code | `.claude/skills/` | `.claude/skills/ten-question-paper-reader/` |
| Cursor（兼容读旧目录） | `.codex/skills/` | `.codex/skills/ten-question-paper-reader/` |

1. 用你习惯的 AI Agent 打开本仓库目录。
2. 直接对它说：「帮我精读这篇论文：`/path/to/your_paper.pdf`」。
3. Agent 自动识别 skill，按三步流水线执行：解析 PDF → 生成十问答案 → 你写完自述后做四维评价。全过程不需要打开任何 IDE。

> 想全局可用（任何目录都能用）？把对应目录的 `ten-question-paper-reader/` 整个文件夹拷到你的 agent 用户级目录：
> Codex/Gemini/Copilot → `~/.agents/skills/`；Claude Code → `~/.claude/skills/`；Codex 旧版/Cursor → `~/.codex/skills/`。skill 内已带 `scripts/bundled/core/` 自包含运行时，拷到哪都能跑。

### 方式二：纯命令行（不依赖任何 AI 助手）

```powershell
# 路径以 .agents 主版本为例；.claude / .codex 下的脚本完全相同
# 第一步：解析PDF
python .agents/skills/ten-question-paper-reader/scripts/tqpr.py parse --pdf your_paper.pdf > paper.json

# 第二步：生成十问答案
python .agents/skills/ten-question-paper-reader/scripts/tqpr.py generate --paper paper.json > note.json

# 第三步：写好总结后让AI评价
python .agents/skills/ten-question-paper-reader/scripts/tqpr.py evaluate --note note.json --summary @my_summary.txt
```

### 方式三：VS Code 侧边栏插件（可选，已修复路径问题）

```bash
cd plugins/vscode-codex
npm install
npm run compile
```
- 用 VS Code 打开本仓库源码目录后按 `F5`；
- 或在设置里手动指定 `tqpr.corePath` 为仓库根目录，再单独安装 VSIX。
- 注：这只是 GUI 外壳，核心逻辑和方式一/二完全同一份 `core/`。

## 🖥️ 旧版裸命令（等价）

```bash
python -m core.cli parse --pdf your_paper.pdf > paper.json
python -m core.cli generate --paper paper.json > note.json
python -m core.cli evaluate --note note.json --summary @my_summary.txt
```

## 📁 项目结构

```
ten-question-paper-reader/
├── .agents/
│   └── skills/
│       └── ten-question-paper-reader/   # ← 主版本（Codex新版/Gemini/Copilot 识别）
│           ├── SKILL.md                 # 触发描述 + 工作流指令
│           ├── agents/openai.yaml        # Codex 专属元数据（其他平台忽略）
│           ├── scripts/
│           │   ├── tqpr.py              # 自定位启动入口（核心）
│           │   ├── bundled/core/         # 自包含 Python 运行时（兜底）
│           │   └── requirements.txt
│           └── references/
│               └── ten-questions.md     # 十问框架与输出模板
├── .claude/skills/ten-question-paper-reader/   # Claude Code 副本（内容同上）
├── .codex/skills/ten-question-paper-reader/    # Codex旧版/Cursor 副本（内容同上）
├── tools/sync-skills.ps1                # 改完主版本后一键同步到上面两处副本
├── AGENTS.md                  # 各 AI 代理进仓库首先读到的说明
├── core/                      # 核心逻辑（canonical 源，改完需同步到 bundled）
│   ├── pdf_parser/           # PDF文本提取、术语识别
│   ├── llm/                  # LLM调用、十问生成、评价
│   ├── model/                # 数据模型
│   ├── config.py            # 全局配置、十问定义、种子词库
│   └── cli.py                # 命令行入口
├── plugins/
│   └── vscode-codex/         # VS Code 侧边栏插件（可选 GUI，已修复 core/ 定位）
├── docs/                      # 用户指南、开发指南
├── examples/                  # 示例精读笔记（含 test-sample.pdf 烟雾测试）
├── requirements.txt
└── README.md
```

## 🗺️ 路线图

- [x] v0.1 MVP：PDF解析 + 十问生成 + Markdown导出
- [x] v0.2：十问精简重组（选题方向/精读重点/审稿攻击点）+ 术语就地随查 + 实验流程与图表导览 + 自述引导问题
- [ ] v0.3：PDF原文联动高亮 + 领域术语包（材料/机械/化工/CS...）+ 多论文对比
- [ ] v1.0：中文论文优化 + Anki卡片导出

## ⚠️ 免责声明

所有AI生成内容仅供参考，**请务必对照原文核对数据、公式与结论**。本工具不替代阅读，而是提升精读效率。

## 📄 License

[MIT](LICENSE)
