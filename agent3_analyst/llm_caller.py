"""
LLM Caller — Agent 3
Wrapper gọi Claude API: nạp prompt template, điền biến, gọi API, trả về text.
API key đọc từ biến môi trường CLAUDE_API_KEY (file .env).
"""

import os
import time
import anthropic
from pathlib import Path


CLAUDE_MODEL      = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 1500   # Agent 3 cần output dài hơn (JSON + phân tích)
MAX_RETRIES       = 3
RETRY_DELAY       = 5


def _load_api_key() -> str:
    key = os.environ.get("CLAUDE_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "CLAUDE_API_KEY chưa được đặt. "
            "Hãy thêm vào file .env hoặc export trước khi chạy."
        )
    return key


def load_prompt(prompt_file: str, variables: dict) -> str:
    base_dir = Path(__file__).parent
    path = base_dir / prompt_file

    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy prompt: {path}")

    template = path.read_text(encoding="utf-8")
    lines = [ln for ln in template.splitlines() if not ln.strip().startswith("#")]
    template = "\n".join(lines).strip()

    for key, value in variables.items():
        template = template.replace("{" + key + "}", str(value))

    return template


def call_claude(prompt_file: str, variables: dict,
                max_tokens: int = CLAUDE_MAX_TOKENS) -> str:
    """Gọi Claude API với retry tự động."""
    client = anthropic.Anthropic(api_key=_load_api_key())
    prompt = load_prompt(prompt_file, variables)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        except anthropic.RateLimitError:
            if attempt < MAX_RETRIES:
                print(f"[Rate limit] Thử lại sau {RETRY_DELAY * attempt}s...")
                time.sleep(RETRY_DELAY * attempt)
            else:
                raise

        except anthropic.APIError as e:
            if attempt < MAX_RETRIES:
                print(f"[API Error] {e} — Thử lại...")
                time.sleep(RETRY_DELAY)
            else:
                raise

    return ""
