"""Offline test for generator parsing (no LLM call)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.model.paper import Paper
import core.llm.generator as gen

# Patch chat() so no network is needed.
def make_chat(reply):
    def _fake(messages):
        return reply
    return _fake

gen.chat = make_chat(None)

# Case 1: clean JSON output
json_reply = """{
  "qa_pairs": [
    {"id":1,"question":"q1","short":"s1","full":"f1","citation":"p.1","confidence":"高","inline_terms":{"SCC":"应力腐蚀"}},
    {"id":2,"question":"q2","short":"s2","full":"f2","citation":"p.2","confidence":"中","inline_terms":{}}
  ],
  "experiment_setup": "- 材料: TC4",
  "key_figures": [{"number":"Fig.1","why_focus":"组织对比","takeaway":"EM连续"}]
}"""
gen.chat = make_chat(json_reply)
note = gen.generate_answers(Paper(title="测试论文"))
print("Case1 JSON:")
print("  Q1 short:", note.qa_pairs[0].short_answer)
print("  Q1 inline_terms:", note.qa_pairs[0].inline_terms)
print("  experiment:", note.experiment_setup)
print("  key_figures:", note.key_figures[0].number, note.key_figures[0].why_focus)
assert note.qa_pairs[0].short_answer == "s1"
assert note.experiment_setup == "- 材料: TC4"
assert note.key_figures[0].number == "Fig.1"

# Case 2: old 【Qn】 text format
text_reply = """【Q1】
【精简版】等轴组织更危险
【详细版】K1SCC=66.79
【原文定位】Table 1, p.5
【置信度】高
【本问术语】
- K1SCC: 临界应力强度因子

【Q2】
【精简版】前人没做深海
【详细版】常压研究多
【原文定位】Introduction
【置信度】高

【实验准备与流程】
- 材料 TC4 ELI
- 设备 WOL

【重点图表】
【Table 1】
为什么重点看：K1SCC全部定量依据
读图要点：EM=66.79 vs WM=80.29
"""
gen.chat = make_chat(text_reply)
note = gen.generate_answers(Paper(title="测试论文"))
print("\nCase2 text fallback:")
print("  Q1 short:", note.qa_pairs[0].short_answer)
print("  Q1 terms:", note.qa_pairs[0].inline_terms)
print("  Q2 citation:", note.qa_pairs[1].citation)
print("  experiment:", note.experiment_setup[:30])
print("  key_figures:", note.key_figures[0].number)
assert note.qa_pairs[0].short_answer == "等轴组织更危险"
assert note.qa_pairs[0].inline_terms == {"K1SCC": "临界应力强度因子"}

# Case 3: completely unstructured reply (LLM went off-rails)
gen.chat = make_chat("嗯这篇论文挺好的，我觉得作者主要讲了钛合金深海腐蚀，具体多少数据我记不清了。")
note = gen.generate_answers(Paper(title="测试论文"))
print("\nCase3 garbage fallback:")
print("  Q10 confidence:", note.qa_pairs[-1].confidence)
print("  Q10 full_answer head:", note.qa_pairs[-1].full_answer[:50])
assert "警告" in note.qa_pairs[-1].full_answer
assert note.qa_pairs[-1].confidence == "低"

print("\nAll 3 cases passed.")
