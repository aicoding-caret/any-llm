from __future__ import annotations

import json
import re
from typing import Any

from .schema import GenerateTopicResponse, Language, SceneElements, TopicCandidate


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


def parse_topic_candidates(text: str) -> GenerateTopicResponse | None:
    cleaned = clean_text(text)
    if not cleaned:
        return None
    try:
        parsed = json.loads(cleaned)
    except (TypeError, ValueError):
        return None
    try:
        return GenerateTopicResponse.model_validate(parsed)
    except Exception:
        return None


def build_fallback_topics(title: str, language: Language) -> GenerateTopicResponse:
    candidates: list[TopicCandidate] = []
    for idx in range(5):
        candidate_id = f"T{idx + 1}"
        scene_elements = SceneElements(
            subject=title,
            action="",
            setting="",
            composition="",
            lighting="",
            style="",
        )
        if language == "zh":
            candidates.append(
                TopicCandidate(
                    id=candidate_id,
                    title=f"{title} 主题草案 {idx + 1}",
                    description=f"围绕 {title} 的四格漫画短场景设定（想法 {idx + 1}）。",
                    sceneElements=scene_elements,
                    hook="结尾会怎样？",
                )
            )
        elif language == "ja":
            candidates.append(
                TopicCandidate(
                    id=candidate_id,
                    title=f"{title} 仮テーマ {idx + 1}",
                    description=f"{title} を題材にした4コマ向けの短い設定（案 {idx + 1}）。",
                    sceneElements=scene_elements,
                    hook="オチはどうなる？",
                )
            )
        else:
            candidates.append(
                TopicCandidate(
                    id=candidate_id,
                    title=f"{title} 임시 주제 {idx + 1}",
                    description=f"{title}을(를) 배경으로 한 4컷용 짧은 설정입니다 (아이디어 {idx + 1}).",
                    sceneElements=scene_elements,
                    hook="결말은 어떻게 될까요?",
                )
            )
    return GenerateTopicResponse(candidates=candidates)
