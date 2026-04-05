"""
Gọi LLM đa nhà cung cấp cho demo & pipeline.
Biến môi trường: CLAUDE_API_KEY, DEEPSEEK_API_KEY, GOOGLE_API_KEY, GEMINI_MODEL
"""

from __future__ import annotations

import os
from typing import Literal

import anthropic
import httpx

Provider = Literal["gemini", "deepseek", "claude"]


def _require(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        raise EnvironmentError(f"Thiếu biến môi trường {name}")
    return v


def complete_chat(
    provider: Provider,
    user_prompt: str,
    *,
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str:
    """Gửi một turn user → trả về nội dung text."""
    if provider == "claude":
        return _claude(user_prompt, max_tokens=max_tokens, temperature=temperature)
    if provider == "deepseek":
        return _deepseek(user_prompt, max_tokens=max_tokens, temperature=temperature)
    if provider == "gemini":
        return _gemini(user_prompt, max_tokens=max_tokens, temperature=temperature)
    raise ValueError(f"Provider không hỗ trợ: {provider}")


def _claude(user_prompt: str, *, max_tokens: int, temperature: float) -> str:
    key = _require("CLAUDE_API_KEY")
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return msg.content[0].text


def _deepseek(user_prompt: str, *, max_tokens: int, temperature: float) -> str:
    key = _require("DEEPSEEK_API_KEY")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    url = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/chat/completions")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    with httpx.Client(timeout=120.0) as client:
        r = client.post(
            url,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
    return data["choices"][0]["message"]["content"]


def _gemini(user_prompt: str, *, max_tokens: int, temperature: float) -> str:
    import google.generativeai as genai
    import re

    _require("GOOGLE_API_KEY")
    # Lưu ý: model id thực tế trên Google AI Studio có thể khác dấu/chuẩn đặt tên.
    # Nếu sai, hãy override bằng env `GEMINI_MODEL_CANDIDATES` (phân tách bởi comma/; newline).
    default_candidates = [
        "gemma-4-26b",
        "gemma-4-31b",
        "gemini-3-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
    ]

    raw = os.environ.get("GEMINI_MODEL_CANDIDATES", "").strip()
    if raw:
        models = [m.strip() for m in re.split(r"[,\n;]+", raw) if m.strip()]
    else:
        # Ưu tiên danh sách theo yêu cầu, không phụ thuộc GEMINI_MODEL đơn lẻ.
        models = default_candidates

    # Loại trùng giữ thứ tự
    seen: set[str] = set()
    models = [m for m in models if not (m in seen or seen.add(m))]

    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    def is_quota_exceeded(err: Exception) -> bool:
        s = str(err).lower()
        # Một số lỗi Gemini/Google API trả về message chứa "quota" + "exceeded",
        # hoặc HTTP 429 / ResourceExhausted.
        return (
            ("quota" in s and "exceed" in s)
            or ("resourceexhausted" in s)
            or ("429" in s)
        )

    def is_model_not_found_or_unsupported(err: Exception) -> bool:
        s = str(err).lower()
        # Ví dụ error bạn cung cấp:
        # "404 models/gemma-4-26b is not found for API version v1beta, or is not supported for generateContent..."
        return (
            ("404" in s and ("not found" in s or "models/" in s))
            or ("not supported for generatecontent" in s)
            or ("is not supported for generatecontent" in s)
            or ("not found for api version" in s)
        )

    last_err: Exception | None = None

    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            gen = model.generate_content(
                user_prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                },
            )

            t = getattr(gen, "text", None)
            if t and t.strip():
                return t.strip()

            # Fallback: đôi khi text nằm trong candidates/parts
            if gen.candidates and gen.candidates[0].content.parts:
                extracted = "".join(
                    getattr(p, "text", "") or "" for p in gen.candidates[0].content.parts
                ).strip()
                if extracted:
                    return extracted

            # Không có nội dung: thử model khác để đảm bảo có "context phân tích"
            last_err = RuntimeError(
                f"Gemini không trả về nội dung cho model {model_name}."
            )
            continue

        except Exception as e:
            if is_quota_exceeded(e) or is_model_not_found_or_unsupported(e):
                last_err = e
                kind = "quota exceeded" if is_quota_exceeded(e) else "model not found/unsupported"
                print(f"[Gemini] {model_name} lỗi ({kind}). Thử model khác...")
                continue
            raise

    raise (last_err or RuntimeError("Gemini không trả về nội dung với mọi model đã thử."))  # type: ignore[misc]
