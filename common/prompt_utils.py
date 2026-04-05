"""Load prompt template (.txt) và thay thế placeholder {key} bằng giá trị."""

from pathlib import Path


def load_prompt_template(path: Path, variables: dict[str, object]) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy prompt: {path}")

    template = path.read_text(encoding="utf-8")
    lines = [ln for ln in template.splitlines() if not ln.strip().startswith("#")]
    template = "\n".join(lines).strip()

    for key, value in variables.items():
        template = template.replace("{" + key + "}", str(value))

    return template
