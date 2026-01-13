from __future__ import annotations

import json
import re
from typing import Any

from .schema import GeneratePanelDialogueResponse


def clean_text(text: str) -> str:
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    cleaned = re.sub(r"```$", "", cleaned)
    return cleaned.strip()


def extract_text_from_response(response: Any) -> str | None:
    if not response:
        return None
    choices = getattr(response, "choices", None)
    parts: list[str] = []
    if choices:
        for choice in choices:
            message = getattr(choice, "message", None)
            content = getattr(message, "content", None) if message else None
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and isinstance(block.get("text"), str):
                        parts.append(block["text"])
    combined = "".join(parts).strip()
    return combined or None


def extract_json(text: str) -> dict[str, Any] | None:
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", candidate, re.IGNORECASE)
    payload = fenced.group(1) if fenced else candidate
    trimmed = payload.strip()
    if not trimmed:
        return None
    try:
        return json.loads(trimmed)
    except json.JSONDecodeError:
        start = trimmed.find("{")
        end = trimmed.rfind("}")
        if start >= 0 and end >= start:
            try:
                return json.loads(trimmed[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def parse_dialogue(response: Any) -> GeneratePanelDialogueResponse | None:
    text = extract_text_from_response(response)
    if not text:
        return None
    parsed = extract_json(clean_text(text))
    if not parsed:
        return None
    try:
        return GeneratePanelDialogueResponse.model_validate(parsed)
    except Exception:
        return None
