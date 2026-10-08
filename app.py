"""十问文献精读器 — 极简网页版。

运行:
    pip install streamlit pymupdf openai
    streamlit run app.py

拖入 PDF → 自动解析 → 调 LLM 出十问。
技术用户/CLI 用户请用 Codex skill 形态（见 .agents/skills/）。
"""
import os
import sys
import tempfile

import streamlit as st

# 把仓库根加入 sys.path，直接复用 core 包
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.pdf_parser import extract_paper, detect_terms  # noqa: E402
from core.llm import generate_answers  # noqa: E402

st.set_page_config(page_title="十问文献精读器", page_icon="📑", layout="wide")
st.title("📑 十问文献精读器")
st.caption("工科研究生半自助论文精读工具 · 不是替你总结，是带你拆解")

# ---- 侧边栏：API 配置 ----
with st.sidebar:
    st.header("⚙️ 模型配置")
    api_key = st.text_input("OPENAI_API_KEY", value=os.getenv("OPENAI_API_KEY", ""),
                             type="password", help="OpenAI 兼容接口的 key")
    base_url = st.text_input("OPENAI_BASE_URL（可选）",
                             value=os.getenv("OPENAI_BASE_URL", ""),
                             help="国内代理如 https://api.deepseek.com/v1")
    model = st.text_input("模型名（可选）", value=os.getenv("TQPR_OPENAI_MODEL", ""))
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    if base_url:
        os.environ["OPENAI_BASE_URL"] = base_url
    if model:
        os.environ["TQPR_OPENAI_MODEL"] = model

    st.markdown("---")
    st.markdown("**进阶形态**：命令行/Codex skill 见仓库 `.agents/skills/`")

# ---- 上传 PDF ----
uploaded = st.file_uploader("拖入论文 PDF", type=["pdf"])

if uploaded is None:
    st.info("👆 先在左侧配好 API Key，再拖入一篇工科论文 PDF")
    st.stop()

if st.button("🚀 开始精读", type="primary", use_container_width=True):
    if not api_key:
        st.error("请先在左侧填入 OPENAI_API_KEY")
        st.stop()

    # 写到临时文件（extract_paper 需要真实路径）
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(uploaded.read())
        pdf_path = f.name

    try:
        with st.status("① 解析 PDF（提取标题/摘要/章节/图表）...") as s1:
            paper = extract_paper(pdf_path)
            detect_terms(paper, pdf_path)
            s1.update(label=f"✅ 解析完成：{paper.title} ｜ {len(paper.captions)} 张图表")

        with st.status("② 调 LLM 生成十问（约 30–60 秒）...") as s2:
            note = generate_answers(paper)
            s2.update(label="✅ 十问生成完成")
    finally:
        os.unlink(pdf_path)

    # ---- 展示 ----
    st.header(f"📄 {note.paper_title}")

    for qa in note.qa_pairs:
        with st.expander(f"**Q{qa.id}. {qa.question}**　｜　置信度：{qa.confidence}",
                         expanded=(qa.id <= 3)):
            st.markdown(f"**精简版**：{qa.short_answer}")
            st.markdown(f"**详细版**：{qa.full_answer}")
            st.caption(f"📍 原文定位：{qa.citation}")
            if qa.inline_terms:
                terms = "　".join(f"**{k}**：{v}" for k, v in qa.inline_terms.items())
                st.markdown(f"🔖 {terms}")

    if note.experiment_setup:
        st.subheader("🧪 实验准备与流程")
        st.markdown(note.experiment_setup)

    if note.key_figures:
        st.subheader("📊 重点图表导览")
        for f in note.key_figures:
            st.markdown(f"- **{f.number}**（{f.kind}）：{f.why_focus} → {f.takeaway}")

    st.warning("⚠️ AI 答案只是初稿，务必对照原文核对数据、公式与结论")
