from __future__ import annotations

import json
import re
from typing import Any

from .schema import GenerateTopicFromElementsResponse, Language, SceneElements


def clean_text(text: str) -> str:
    """Remove markdown code blocks and extract clean content."""
    cleaned = text.strip()
    # Remove ```json ... ``` or ``` ... ``` blocks (multiline)
    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```$", "", cleaned)
    # Also handle inline code blocks
    cleaned = re.sub(r"^`+|`+$", "", cleaned)
    return cleaned.strip()


def extract_json_from_text(text: str) -> str | None:
    """Extract JSON object from text that may contain extra content."""
    # Try to find JSON object pattern
    match = re.search(r'\{[^{}]*"topic"\s*:\s*"[^"]*"[^{}]*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return None


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
    """Parse topic from LLM response, handling various formats."""
    if not text:
        return None

    cleaned = clean_text(text)
    if not cleaned:
        return None

    # Try direct JSON parse first
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            topic_value = parsed.get("topic")
            if isinstance(topic_value, str) and topic_value.strip():
                return topic_value.strip()
    except (TypeError, ValueError, json.JSONDecodeError):
        pass

    # Try to extract JSON from mixed content
    json_str = extract_json_from_text(cleaned)
    if json_str:
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                topic_value = parsed.get("topic")
                if isinstance(topic_value, str) and topic_value.strip():
                    return topic_value.strip()
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    # Try regex extraction for escaped quotes or malformed JSON
    match = re.search(r'"topic"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
    if match:
        topic_value = match.group(1)
        # Unescape common escapes
        topic_value = topic_value.replace('\\"', '"').replace('\\n', '\n')
        if topic_value.strip():
            return topic_value.strip()

    # If all parsing fails, return None (let caller use fallback)
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
