# 用户使用指南

## 安装步骤

### 前置依赖
1. **Python 3.9 或更高版本**：https://www.python.org/downloads/
2. **VS Code**：https://code.visualstudio.com/
3. **OpenAI API Key**：https://platform.openai.com/api-keys

### 安装Python依赖
```bash
cd ten-question-paper-reader
pip install -r requirements.txt
```

### 配置环境变量
```powershell
# Windows PowerShell（当前会话）
$env:OPENAI_API_KEY="sk-你的key"

# 永久设置（推荐）
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-你的key", "User")
```

如需使用国内代理或其他OpenAI兼容服务：
```powershell
$env:OPENAI_BASE_URL="https://your-proxy.com/v1"
$env:TQPR_OPENAI_MODEL="gpt-4o-mini"
```

### 安装VS Code插件
```bash
cd plugins/vscode-codex
npm install
npm run compile
```
然后在VS Code中按 `F5` 启动扩展开发宿主即可。

## 使用流程

### 第一步：上传论文
- 点击左侧活动栏的「📑 十问精读器」图标
- 点击「选择论文PDF」
- 等待解析（首次约30-60秒，取决于LLM响应速度）

### 第二步：精简概览
- 默认打开「精简概览」标签
- 每问1-2句话，1分钟了解论文全貌
- 判断这篇论文是否值得精读

### 第三步：深度精读
- 切换到「深度精读」标签
- 每问展示详细回答 + 原文定位（章节/页码/图表号）
- **点击蓝色下划线的专业术语**，弹出解释卡片
- 对照原文阅读，核对AI答案

### 第四步：自己总结
- 切换到「我的总结」标签
- 按十问框架填写自己的理解
- 点击「AI评价我的总结」获取分维度评分与建议

### 第五步：导出笔记
- 点击「导出精读笔记」保存为Markdown
- 可导入Obsidian、Notion、Logseq等笔记软件

## 常见问题

**Q: 提示"分析失败"怎么办？**
A: 依次检查：
1. Python是否在PATH中（或在设置 `tqpr.pythonPath` 中指定完整路径）
2. 是否运行了 `pip install -r requirements.txt`
3. OPENAI_API_KEY是否正确设置
4. 网络能否访问OpenAI API（或配置了代理）

**Q: 生成的答案有错误怎么办？**
A: AI答案是初稿，**必须对照原文核对**。插件标注了置信度，低置信度的问题请重点检查。你可以在「我的总结」中纠正错误理解。

**Q: 支持中文论文吗？**
A: MVP版本优先支持英文论文。中文论文在v0.3版本优化。

**Q: 我的论文隐私安全吗？**
A: PDF在本地用PyMuPDF解析，仅论文文本内容发送给你配置的LLM API。不要使用共享API Key处理未发表的涉密论文。
