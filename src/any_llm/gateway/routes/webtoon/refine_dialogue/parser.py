from __future__ import annotations

import re
from typing import Any

from .schema import RefineDialogueResponse


def clean_text(text: str) -> str:
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    cleaned = re.sub(r"```$", "", cleaned)
    return cleaned.strip()


def extract_text_from_response(response: Any) -> str | None:
    if not response:
        return None
    choices = getattr(response, "choices", None) or []
    parts: list[str] = []
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


def parse_refined_dialogue(response: Any) -> RefineDialogueResponse | None:
    text = extract_text_from_response(response)
    if not text:
        return None
    cleaned = clean_text(text)
    return RefineDialogueResponse(dialogue=cleaned)
