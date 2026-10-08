"""LLM client wrapper supporting OpenAI-compatible APIs."""
import os
from typing import List, Dict


def _openai_settings():
    """Read env vars fresh on every call so UI-sidebar changes take effect
    without restarting the process (important for Streamlit)."""
    return {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": os.getenv("TQPR_OPENAI_MODEL", "gpt-4o-mini"),
    }


def _anthropic_settings():
    return {
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "model": os.getenv("TQPR_ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
    }


def chat(messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
    """Send a chat completion request and return the text reply.

    Uses OpenAI-compatible endpoint by default. Falls back gracefully
    with a clear error if no API key is configured.
    """
    provider = os.getenv("TQPR_LLM_PROVIDER", "openai")
    if provider == "openai" or not _anthropic_settings()["api_key"]:
        return _chat_openai(messages, temperature)
    return _chat_anthropic(messages, temperature)


def _chat_openai(messages: List[Dict[str, str]], temperature: float) -> str:
    s = _openai_settings()
    if not s["api_key"]:
        return (
            "【未配置API Key】请设置环境变量 OPENAI_API_KEY 后重试。"
            "你可以将论文文本复制到任意AI工具中，手动套用十问框架。"
        )
    try:
        from openai import OpenAI
    except ImportError:
        return "【缺少依赖】请运行 pip install openai"

    client = OpenAI(
        api_key=s["api_key"],
        base_url=s["base_url"],
        timeout=180.0,          # 10问长输出给足3分钟
        max_retries=2,          # 超时/限流自动重试2次
    )
    resp = client.chat.completions.create(
        model=s["model"],
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""


def _chat_anthropic(messages: List[Dict[str, str]], temperature: float) -> str:
    s = _anthropic_settings()
    try:
        import anthropic
    except ImportError:
        return "【缺少依赖】请运行 pip install anthropic"

    client = anthropic.Anthropic(api_key=s["api_key"])
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    user_msgs = [m for m in messages if m["role"] != "system"]
    resp = client.messages.create(
        model=s["model"],
        max_tokens=4096,
        system=system,
        messages=[{"role": m["role"], "content": m["content"]} for m in user_msgs],
        temperature=temperature,
    )
    return "".join(getattr(b, "text", "") for b in resp.content)
