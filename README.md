# 十问文献精读器 Ten-Question Paper Reader

> **不是给你总结论文，而是教你拆解论文。**

面向工科研究生的**结构化文献半自助精读工具**。以「十问精读法」为核心方法论，把读论文从"看摘要"升级为"按框架拆解+对照原文校验+自己总结+AI评价"的闭环训练。

---

## ✨ 核心特性

- **十问精读框架**：10个递进式问题，覆盖"是什么→为什么→怎么做→怎么用"完整认知链
- **双层答案**：每问自动生成「1-2句精简版」+「带原文定位的详细版」
- **交互式术语解释**：自动高亮专业术语，点击即出定义+原文页码
- **半自助总结闭环**：填空式模板 → 你自己写总结 → AI分维度评价 → 生成最终笔记
- **本地优先**：PDF在本地解析，保护未发表论文隐私

## 📋 十问框架

| # | 问题 | 类型 |
|---|------|------|
| 1 | 核心研究主题是什么？聚焦哪个具体问题？ | 客观提取 |
| 2 | 作者为什么做？前人留下什么缺口？ | 客观提取 |
| 3 | 整体技术路线？分哪几个步骤？ | 客观提取 |
| 4 | 核心方法/模型/实验？关键参数？ | 客观提取 |
| 5 | 数据集/样本来自哪里？数量与代表性？ | 客观提取 |
| 6 | 主要结论与关键定量结果？ | 客观提取 |
| 7 | 核心创新点？和已有研究最大区别？ | 客观+分析 |
| 8 | 局限性？哪些因素没考虑到？ | 客观+分析 |
| 9 | 应用场景？工程/学术价值？ | 分析+应用 |
| 10 | 我的核心收获？哪些可直接复用？ | 主观沉淀 |

## 🚀 快速开始

### 环境要求
- Python 3.9+
- Node.js 18+（编译VS Code插件用）
- VS Code 1.80+ 或 Codex
- OpenAI API Key（兼容OpenAI接口的服务均可）

### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 2. 配置API Key
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-xxxx"
# 可选：使用兼容代理
$env:OPENAI_BASE_URL="https://your-proxy/v1"
$env:TQPR_OPENAI_MODEL="gpt-4o-mini"
```

### 3. 编译VS Code插件
```bash
cd plugins/vscode-codex
npm install
npm run compile
```

### 4. 在VS Code中运行
1. 用VS Code打开 `plugins/vscode-codex/` 文件夹
2. 按 `F5` 启动扩展开发宿主
3. 左侧活动栏点击「十问精读器」图标
4. 点击「选择论文PDF」开始分析

## 🖥️ 命令行使用（不装插件也能用）

```bash
# 第一步：解析PDF
python -m core.cli parse --pdf your_paper.pdf > paper.json

# 第二步：生成十问答案
python -m core.cli generate --paper paper.json > note.json

# 第三步：写好总结后让AI评价
python -m core.cli evaluate --note note.json --summary @my_summary.txt
```

## 📁 项目结构

```
ten-question-paper-reader/
├── core/                    # 核心逻辑（跨客户端复用）
│   ├── pdf_parser/          # PDF文本提取、术语识别
│   ├── llm/                 # LLM调用、十问生成、评价
│   ├── model/               # 数据模型
│   ├── config.py            # 全局配置、十问定义、种子词库
│   └── cli.py               # 命令行入口
├── plugins/
│   └── vscode-codex/        # VS Code/Codex 插件
├── docs/                     # 用户指南、开发指南
├── examples/                 # 示例精读笔记
├── requirements.txt
└── README.md
```

## 🗺️ 路线图

- [x] v0.1 MVP：PDF解析 + 十问生成 + 层级1术语交互 + Markdown导出
- [ ] v0.2：PDF原文联动高亮（层级2）+ 填空模板优化
- [ ] v0.3：领域术语包（材料/机械/化工/CS...）+ 多论文对比
- [ ] v1.0：Harness插件 + 中文论文优化 + Anki卡片导出

## ⚠️ 免责声明

所有AI生成内容仅供参考，**请务必对照原文核对数据、公式与结论**。本工具不替代阅读，而是提升精读效率。

## 📄 License

[MIT](LICENSE)
