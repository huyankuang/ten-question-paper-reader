# 开发指南

## 架构总览

```
┌─────────────────────────────────┐
│ VS Code Webview (TypeScript)   │  用户交互面板
├─────────────────────────────────┤
│ extension.ts (VS Code API)      │  命令注册、IPC桥接
├─────────────────────────────────┤
│ Python CLI (core/cli.py)        │  通过 child_process 调用
├─────────────────────────────────┤
│ core/                           │
│  ├── pdf_parser/  PyMuPDF解析  │
│  ├── llm/         OpenAI兼容   │
│  ├── model/       数据结构      │
│  └── config.py    十问+词库     │
└─────────────────────────────────┘
```

## 开发环境搭建

```bash
# Python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pytest  # 开发测试

# Node
cd plugins/vscode-codex
npm install
npm run watch  # 自动编译
```

## 核心模块说明

### core/pdf_parser/text_extractor.py
- 用PyMuPDF提取全文与分页文本
- 通过正则识别章节标题（Abstract/Introduction/Method/Results/Conclusion）
- 输出结构化 `Paper` 对象

### core/pdf_parser/term_detector.py
- 匹配 `config.py` 中的 `SEED_TERMS`
- 用正则查找术语首次出现页码
- 启发式提取摘要中的大写专业短语

### core/llm/generator.py
- 组装论文上下文（摘要+前12000字符正文）
- 一次性调用LLM生成十问答案
- 解析返回文本中的【Q1】...【Q10】块

### core/llm/evaluator.py
- 将用户总结与标准答案对比
- 要求LLM输出严格JSON
- 解析为 `Evaluation` 对象

### plugins/vscode-codex/
- `src/extension.ts`：插件入口，注册命令与WebviewViewProvider
- `src/panel/TenQuestionPanel.ts`：Webview面板，通过execFile调用Python CLI
- `src/panel/main.js`：前端交互逻辑（Vanilla JS）
- `src/panel/main.css`：VS Code主题样式

## 添加新的领域术语包

编辑 `core/config.py` 中的 `SEED_TERMS` 字典：
```python
SEED_TERMS = {
    "新术语": "一句话解释。",
    ...
}
```
后续版本会支持按领域加载独立JSON词库。

## 自定义十问

编辑 `core/config.py` 中的 `TEN_QUESTIONS` 列表。每问包含 `id`、`question`、`type` 三个字段。

## 测试

```bash
# CLI冒烟测试（需要配置好API Key）
python -m core.cli parse --pdf examples/sample.pdf > /tmp/paper.json
python -m core.cli generate --paper /tmp/paper.json
```

## 发布到VS Code Marketplace

```bash
cd plugins/vscode-codex
npm install -g vsce
vsce package          # 生成 .vsix
vsce publish          # 发布（需要Microsoft账号）
```

## 注意事项

- **不要把 `.env` 或API Key提交到Git**
- Webview的CSP策略禁止内联脚本，所有JS必须通过nonce加载
- Python路径通过VS Code设置 `tqpr.pythonPath` 配置
- 核心逻辑保持与客户端解耦，方便后续适配Harness等其他客户端
