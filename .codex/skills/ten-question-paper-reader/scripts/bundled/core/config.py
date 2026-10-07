"""Global configuration for Ten-Question Paper Reader."""
import os

# ---------- LLM Configuration ----------
# Supported providers: openai, anthropic, or a compatible OpenAI endpoint.
# Users set these via environment variables before running the plugin.
LLM_PROVIDER = os.getenv("TQPR_LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("TQPR_OPENAI_MODEL", "gpt-4o-mini")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("TQPR_ANTHROPIC_MODEL", "claude-3-haiku-20240307")

# ---------- PDF Parsing ----------
# Number of characters per chunk fed to the LLM (rough estimate, ~4k tokens).
PDF_CHUNK_SIZE = 6000
PDF_CHUNK_OVERLAP = 300

# ---------- Ten Questions ----------
TEN_QUESTIONS = [
    {
        "id": 1,
        "question": "这篇文献的核心研究主题是什么？聚焦哪个具体的工程/学术问题？",
        "type": "客观提取",
    },
    {
        "id": 2,
        "question": "作者为什么要做这项研究？前人工作留下了什么未解决的缺口？",
        "type": "客观提取",
    },
    {
        "id": 3,
        "question": "本文的整体研究思路/技术路线是什么？大致分为哪几个核心步骤？",
        "type": "客观提取",
    },
    {
        "id": 4,
        "question": "本文采用的核心研究方法/模型/实验方案是什么？关键参数有哪些？",
        "type": "客观提取",
    },
    {
        "id": 5,
        "question": "研究使用的数据集/样本/试验对象来自哪里？数量和代表性如何？",
        "type": "客观提取",
    },
    {
        "id": 6,
        "question": "本文最终得到了哪些主要结论和关键定量结果？",
        "type": "客观提取",
    },
    {
        "id": 7,
        "question": "这项工作的核心创新点/学术贡献是什么？和已有研究最大区别在哪？",
        "type": "客观+分析",
    },
    {
        "id": 8,
        "question": "研究存在哪些局限性？有哪些场景/因素没有考虑到？",
        "type": "客观+分析",
    },
    {
        "id": 9,
        "question": "本文的结论能应用到什么场景？有什么工程价值或学术参考意义？",
        "type": "分析+应用",
    },
    {
        "id": 10,
        "question": "我读这篇文献的核心收获是什么？有哪些方法/结论可以直接复用？",
        "type": "主观沉淀",
    },
]

# ---------- Engineering / Materials Seed Glossary ----------
# Built-in seed terms for the materials / mechanical / pipeline engineering domain.
# Can be extended per user research area.
SEED_TERMS = {
    "极限状态函数": "描述结构安全与失效边界的数学函数 g(X)，g>0 安全，g<0 失效。",
    "显式极限状态": "可写成封闭解析公式的极限状态函数，输入参数直接计算结果。",
    "隐式极限状态": "无解析公式，必须通过数值仿真（如有限元）才能求得结果的极限状态。",
    "代理模型": "用少量样本训练的数学模型，用于高精度替代昂贵的仿真/实验计算。",
    "Kriging": "一种基于空间插值的代理模型，通过半方差函数拟合变量间相关性。",
    "多项式混沌": "用正交多项式展开逼近随机变量输出的不确定性量化方法。",
    "蒙特卡洛模拟": "通过大量随机抽样统计失效概率的可靠性分析方法。",
    "重要性抽样": "在失效区域附近集中抽样以减少样本量的蒙特卡洛改进方法。",
    "子集模拟": "将小失效概率分解为多级条件概率乘积的抽样方法。",
    "有限元": "将连续体离散为单元求解力学问题的数值方法。",
    "爆破压力": "管道在内压作用下发生塑性失稳/破裂时的临界压力。",
    "腐蚀缺陷": "管道壁面因腐蚀导致的金属损失区域。",
    "相互作用腐蚀": "邻近腐蚀缺陷的应力场相互叠加，使失效压力低于孤立缺陷之和。",
    "敏感性分析": "量化各输入变量对输出结果影响程度的分析方法。",
    "不确定性量化": "用概率分布描述材料、几何、荷载等参数随机性的方法。",
    "API 5L X80": "石油天然气行业常用的高强度管线钢标准，屈服强度约555 MPa。",
    "DNV-RP-F101": "挪威船级社发布的腐蚀管道评估推荐做法。",
    "von Mises应力": "工程中常用的材料屈服判据，基于剪切应变能理论。",
    "Weibull分布": "常用于描述材料寿命、腐蚀深度等极值现象的概率分布。",
    "真应力-真应变": "考虑截面收缩和瞬时长度的材料本构关系，用于塑性大变形分析。",
}
