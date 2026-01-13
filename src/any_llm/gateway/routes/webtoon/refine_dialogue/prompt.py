from __future__ import annotations

from .schema import Language, Tone

ERA_IDS = ["any", "modern", "nineties", "seventies-eighties", "joseon", "future"]
SEASON_IDS = ["any", "spring", "summer", "autumn", "winter"]

LANGUAGE_LABELS: dict[Language, str] = {
    "ko": "한국어",
    "zh": "中文",
    "ja": "日本語",
}

TONE_LABELS: dict[Tone, str] = {
    "neutral": "자연스럽게 다듬기",
    "humor": "유머러스하게",
    "serious": "진지하게",
    "emotional": "감성적으로",
}

def resolve_era_label(value: str | None) -> str | None:
    if not value:
        return None
    era = value if value in ERA_IDS else "any"
    if era == "any":
        return None
    return {
        "modern": "Modern",
        "nineties": "1990s",
        "seventies-eighties": "1970s-80s",
        "joseon": "Joseon / Traditional",
        "future": "Future / Virtual",
    }[era]

def resolve_season_label(value: str | None) -> str | None:
    if not value:
        return None
    season = value if value in SEASON_IDS else "any"
    if season == "any":
        return None
    return {
        "spring": "Spring",
        "summer": "Summer",
        "autumn": "Autumn",
        "winter": "Winter",
    }[season]

def build_world_setting_block(era_label: str | None, season_label: str | None) -> str:
    if not era_label and not season_label:
        return ""
    lines = ["Era/season guidance:"]
    if era_label:
        lines.append(f"- Era: {era_label}")
    if season_label:
        lines.append(f"- Season: {season_label}")
    lines.extend(
        [
            "- If an era is specified, adjust tone and vocabulary to reflect it while keeping readability.",
            "- Avoid excessive archaic or slang-heavy wording.",
            "- Use season only as a mood hint.",
        ]
    )
    return "\n".join(lines)

def build_prompt(
    dialogue: str,
    tone_label: str,
    language_label: str,
    character_mode: str,
    scene: str | None,
    speaker: str | None,
    world_setting_block: str,
) -> str:
    caricature_guide = (
        "- In caricature mode, keep the dialogue shorter and more colloquial.\n" if character_mode == "caricature" else ""
    )
    lines = [
        "You are an editor refining webtoon dialogue. Follow these rules strictly.",
        "",
        "Rules:",
        "- Output only the dialogue. If input has multiple lines, preserve line count and order.",
        "- Each line should be a concise single sentence.",
        "- Output plain dialogue only, with no quotes, parentheses, prefixes, or suffixes.",
        f"- Write naturally in {language_label}.",
        "- Keep length similar to the original.",
        "- Convey emotion and relationship nuance without exaggeration.",
        "- Avoid dry, purely informational lines; add subtle subtext.",
        "- No emotion/action tags like '(sigh)' or '[sad]'.",
        "- If helpful, use short interjections (e.g., 음, 어, …) to keep it natural.",
        caricature_guide.strip(),
    ]
    if world_setting_block:
        lines.extend(["", world_setting_block])
    lines.extend(
        [
            "",
            f"Scene: {scene or '(정보 없음)'}",
            f"Speaker: {speaker or '(정보 없음)'}",
            f"Tone emphasis: {tone_label}",
            "- Use the tone and relationship cues to shape pacing, punctuation, and word choice.",
            "",
            "- Metalayer: Maintain any implied tension or curiosity from the original lines.",
            "",
            "Original dialogue:",
            dialogue,
            "",
            "Refined dialogue:",
        ]
    )
    return "\n".join(line for line in lines if line is not None)
