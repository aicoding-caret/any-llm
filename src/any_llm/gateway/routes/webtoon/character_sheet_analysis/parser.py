from __future__ import annotations

import json
import re
from typing import Any

from .schema import CharacterSheetMetadata


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


def parse_metadata(text: str) -> CharacterSheetMetadata | None:
    cleaned = clean_text(text)
    if not cleaned:
        return None
    try:
        payload = json.loads(cleaned)
    except (TypeError, ValueError):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            payload = json.loads(cleaned[start : end + 1])
        except (TypeError, ValueError):
            return None
    if not isinstance(payload, dict):
        return None
    try:
        return CharacterSheetMetadata.model_validate(payload)
    except Exception:
        return None
