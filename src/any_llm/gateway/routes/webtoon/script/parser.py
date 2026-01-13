from __future__ import annotations

import json
import re
from typing import Any

from .schema import GenerateScriptResponse


def extract_text_from_response(response: Any) -> str | None:
    parts: list[str] = []
    choices = getattr(response, "choices", None) or []
    for choice in choices:
        message = getattr(choice, "message", None)
        if not message:
            continue
        content = getattr(message, "content", None)
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text")
                    if isinstance(text, str):
                        parts.append(text)
    combined = "".join(parts).strip()
    return combined or None


def clean_text(text: str) -> str:
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    cleaned = re.sub(r"```$", "", cleaned)
    return cleaned.strip()


def parse_script_response(text: str) -> GenerateScriptResponse | None:
    cleaned = clean_text(text)
    if not cleaned:
        return None
    try:
        parsed = json.loads(cleaned)
    except (TypeError, ValueError):
        return None
    try:
        return GenerateScriptResponse.model_validate(parsed)
    except Exception:
        return None
