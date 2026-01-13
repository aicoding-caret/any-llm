from __future__ import annotations

import json
import re
from typing import Any

from .schema import GenerateTopicFromElementsResponse, Language, SceneElements


def clean_text(text: str) -> str:
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    cleaned = re.sub(r"```$", "", cleaned)
    return cleaned.strip()


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


def parse_topic_text(text: str) -> str | None:
    cleaned = clean_text(text)
    if not cleaned:
        return None
    try:
        parsed = json.loads(cleaned)
    except (TypeError, ValueError):
        return cleaned.strip() or None
    if not isinstance(parsed, dict):
        return None
    topic_value = parsed.get("topic")
    if isinstance(topic_value, str) and topic_value.strip():
        return topic_value.strip()
    return None


def build_fallback_topic(elements: SceneElements) -> str:
    parts = [
        elements.subject.strip(),
        elements.action.strip(),
        elements.setting.strip(),
        elements.composition.strip(),
        elements.lighting.strip(),
        elements.style.strip(),
    ]
    return " ".join(part for part in parts if part).strip()
