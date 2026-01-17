from __future__ import annotations

from .schema import CharacterCount, Language, SceneElements

LANGUAGE_LABELS: dict[Language, str] = {
    "ko": "한국어",
    "zh": "중국어",
    "ja": "일본어",
}

ERA_IDS = ["any", "modern", "nineties", "seventies-eighties", "joseon", "future"]
SEASON_IDS = ["any", "spring", "summer", "autumn", "winter"]


def normalize_scene_elements(value: SceneElements | None) -> SceneElements:
    if not value:
        return SceneElements(subject="", action="", setting="", composition="", lighting="", style="")
    return value


def build_scene_summary(elements: SceneElements, fallback: str = "") -> str:
    parts = [
        elements.subject,
        elements.action,
        elements.setting,
        elements.composition,
        elements.lighting,
        elements.style,
    ]
    cleaned = [part.strip() for part in parts if part.strip()]
    if not cleaned:
        return fallback.strip()
    return " ".join(cleaned).strip()


def resolve_era_label(value: str | None) -> str | None:
    if not value:
        return None
    era = value if value in ERA_IDS else "any"
    if era == "any":
        return None
    labels = {
        "modern": "Modern",
        "nineties": "1990s",
        "seventies-eighties": "1970s-80s",
        "joseon": "Joseon / Traditional",
        "future": "Future / Virtual",
    }
    return labels.get(era)


def resolve_season_label(value: str | None) -> str | None:
    if not value:
        return None
    season = value if value in SEASON_IDS else "any"
    if season == "any":
        return None
    labels = {
        "spring": "Spring",
        "summer": "Summer",
        "autumn": "Autumn",
        "winter": "Winter",
    }
    return labels.get(season)


CHARACTER_COUNT_RULES: dict[str, str] = {
    "solo": "- The topic should focus on a single character's internal journey, monologue, or self-reflection.",
    "duo": "- IMPORTANT: The topic MUST feature exactly 2 characters interacting with each other through dialogue or action.",
    "group": "- IMPORTANT: The topic MUST feature 3 or more characters interacting in a group dynamic.",
}


def resolve_character_count_rule(character_count: CharacterCount | None) -> str:
    """Return the character count rule for the prompt."""
    if character_count and character_count in CHARACTER_COUNT_RULES:
        return CHARACTER_COUNT_RULES[character_count]
    # Default to duo for best webtoon results
    return CHARACTER_COUNT_RULES["duo"]


def build_world_setting_block(era_label: str | None, season_label: str | None) -> str:
    if not era_label and not season_label:
        return ""
    lines = ["시대/계절 보정:"]
    if era_label:
        lines.append(f"- 시대: {era_label}")
    if season_label:
        lines.append(f"- 계절: {season_label}")
    lines.extend(
        [
            "- 시대가 있으면 배경/소품/말투에서 드러나게 반영.",
            "- 계절은 분위기 힌트로만 사용.",
            "- 장르 톤을 해치지 않도록 자연스럽게 섞기.",
        ]
    )
    return "\n".join(lines)


def build_prompt(
    topic: str,
    normalized_elements: SceneElements,
    genre: str | None,
    language_label: str,
    world_setting_block: str,
    character_count: CharacterCount | None = None,
) -> str:
    character_rule = resolve_character_count_rule(character_count)
    lines = [
        "You are a planner refining the topic for a 4-panel webtoon.",
        "",
        "Rules:",
        "- Output must be a single JSON object only.",
        '- Use only one key: "topic".',
        f"- Write naturally in {language_label}.",
        "- 2–3 sentences in a single paragraph.",
        "- Naturally incorporate all six elements.",
        "- No bullets, numbering, headings, quotes, or parenthetical explanations.",
        "- Avoid abstract lists; include concrete scene details.",
        "- The situation must be suitable for a 4-panel progression.",
        character_rule,
        "",
        f"Genre: {genre or '정보 없음'}",
    ]
    if world_setting_block:
        lines.extend(["", world_setting_block])
    lines.extend(
        [
            "",
            "Six elements:",
            f"- Subject: {normalized_elements.subject or '(정보 없음)'}",
            f"- Action: {normalized_elements.action or '(정보 없음)'}",
            f"- Setting: {normalized_elements.setting or '(정보 없음)'}",
            f"- Composition: {normalized_elements.composition or '(정보 없음)'}",
            f"- Lighting: {normalized_elements.lighting or '(정보 없음)'}",
            f"- Style: {normalized_elements.style or '(정보 없음)'}",
            "",
            'Output format:',
            '{"topic":"..."}',
        ]
    )
    return "\n".join(lines)
