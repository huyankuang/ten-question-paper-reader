"""LLM client wrapper supporting OpenAI-compatible APIs."""
import os
from typing import List, Dict

from core.config import (
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL, LLM_PROVIDER,
)


def chat(messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
    """Send a chat completion request and return the text reply.

    Uses OpenAI-compatible endpoint by default. Falls back gracefully
    with a clear error if no API key is configured.
    """
    if LLM_PROVIDER == "openai" or not ANTHROPIC_API_KEY:
        return _chat_openai(messages, temperature)
    return _chat_anthropic(messages, temperature)


def _chat_openai(messages: List[Dict[str, str]], temperature: float) -> str:
    if not OPENAI_API_KEY:
        return (
            "【未配置API Key】请设置环境变量 OPENAI_API_KEY 后重试。"
            "你可以将论文文本复制到任意AI工具中，手动套用十问框架。"
        )
    try:
        from openai import OpenAI
    except ImportError:
        return "【缺少依赖】请运行 pip install openai"

    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""


def _chat_anthropic(messages: List[Dict[str, str]], temperature: float) -> str:
    try:
        import anthropic
    except ImportError:
        return "【缺少依赖】请运行 pip install anthropic"

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    # Anthropic expects system separately.
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    user_msgs = [m for m in messages if m["role"] != "system"]
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": m["role"], "content": m["content"]} for m in user_msgs],
        temperature=temperature,
    )
    return "".join(getattr(b, "text", "") for b in resp.content)
