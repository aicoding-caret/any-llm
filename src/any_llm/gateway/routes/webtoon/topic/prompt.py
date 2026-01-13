from __future__ import annotations

from typing import Iterable

from .schema import ERA_IDS, SEASON_IDS, Language

LANGUAGE_LABELS: dict[Language, str] = {
    "ko": "Korean",
    "zh": "Chinese",
    "ja": "Japanese",
}

SYSTEM_PROMPT_TEMPLATE = (
    "You are a 4-panel webtoon planner.\n"
    "You are tasked with suggesting high-potential topics aligned with the selected genre.\n\n"
    "Common rules:\n"
    "1. The output must be valid JSON only.\n"
    "2. Each topic must be executable as a four-panel structure.\n"
    "3. Avoid vague or overly abstract prompts.\n"
    "4. Describe situations vividly so each panel is easily imagined.\n"
    "5. Mix approaches (empathy, twist, message, explanation) across the candidates.\n"
    "6. Do not include political attacks, hateful language, discrimination or insults toward real individuals.\n"
    "7. Every topic should be ready for immediate scriptwriting.\n"
    "8. Each candidate must include sceneElements with subject, action, setting, composition, lighting, and style.\n"
    "9. Each description must be a single paragraph that integrates the six elements naturally (no bullet lists).\n"
    "10. All text values must be written in {language_label}."
)

GENRE_TEMPLATES: dict[str, dict[str, str]] = {
    "daily": {
        "title": "Relatable Daily Life & Comedy",
        "criteria": (
            "- Situations anyone could encounter\n"
            "- In a four-panel structure, the last panel has a funny twist or relatable punchline\n"
            "- More realistic than exaggerated"
        ),
        "request": (
            "Suggest 5 webtoon topics about small daily inconveniences, bittersweet-funny moments,"
            " and relatable reality."
        ),
    },
    "pets": {
        "title": "Pets",
        "criteria": (
            "- From the pet's perspective or centered on the relationship with the owner\n"
            "- Conveyed through actions/expressions without dialogue\n"
            "- Focus on cute or relatable moments"
        ),
        "request": "Suggest 5 webtoon topics based on daily episodes of living with pets.",
    },
    "emotional": {
        "title": "Heartwarming / Healing",
        "criteria": (
            "- Small changes felt in family, friendship, or one's relationship with oneself\n"
            "- Gentle aftertaste; the final panel resolves the emotion or delivers the message"
        ),
        "request": "Suggest 5 topics for short but heartwarming stories.",
    },
    "satire": {
        "title": "Social Satire",
        "criteria": (
            "- Express situations and structures via metaphor without real names\n"
            "- Deliver humor and message together\n"
            "- Avoid excessive aggression or hateful expressions"
        ),
        "request": "Suggest 5 topics that satirically portray social phenomena or everyday contradictions.",
    },
    "self": {
        "title": "Self-Development / Mindset",
        "criteria": (
            "- Focus on everyday realizations without being too preachy\n"
            "- Structure that shows behavior change or mindset shifts\n"
            "- The final panel clearly conveys the message"
        ),
        "request": "Suggest 5 webtoon topics with the keywords habits, growth, and mindset shifts.",
    },
    "concept": {
        "title": "Concept Explanation & Principles",
        "criteria": (
            "- Explain difficult concepts through everyday situations\n"
            "- Understanding builds step by step across panels\n"
            "- The final panel summarizes the key point"
        ),
        "request": "Suggest 5 topics that explain concepts in economics, society, science, or IT in an easy way.",
    },
    "campaign": {
        "title": "Campaign / Brand Message",
        "criteria": (
            "- Public-interest message or encouraging positive action\n"
            "- Avoid an overt advertising tone\n"
            "- Structure: empathy -> problem awareness -> message delivery"
        ),
        "request": "Suggest 5 topics suitable for public campaigns or brand messages.",
    },
    "sci-fi": {
        "title": "Alternate History / Sci-Fi",
        "criteria": (
            "- Start from a 'What if ___?' premise\n"
            "- The worldbuilding fits within four panels without being overdone\n"
            "- A twist or core idea is key"
        ),
        "request": "Suggest 5 topics based on imagined settings or sci-fi ideas.",
    },
    "language": {
        "title": "Language Learning",
        "criteria": (
            "- Short conversational situations\n"
            "- Expressions people can actually use\n"
            "- The final panel naturally reveals the meaning of the expression"
        ),
        "request": "Suggest 5 topics centered on situational dialogues that help learn a foreign language.",
    },
    "relationship": {
        "title": "Romance / Relationships",
        "criteria": (
            "- Centered on flirting, romance conflicts, or friendships\n"
            "- High relatability, but tone control is important\n"
            "- Emotion-driven scenes with delicate direction"
        ),
        "request": "Suggest 5 relatable webtoon topics about romance and relationships.",
    },
}


def resolve_genre_prompt(genre: str) -> dict[str, str]:
    return GENRE_TEMPLATES.get(
        genre,
        {
            "title": genre,
            "criteria": "- Provide four-panel topics that match the selected genre",
            "request": "Suggest 5 topics that fit the genre.",
        },
    )


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


def build_world_setting_block(era_label: str | None, season_label: str | None) -> str:
    if not era_label and not season_label:
        return ""

    lines = ["World Setting:"]
    if era_label:
        lines.append(f"Era: {era_label}")
    if season_label:
        lines.append(f"Season: {season_label}")
    lines.append("Guidance:")
    lines.extend(
        [
            "- If an era is provided, make it clearly visible through setting, props, and events.",
            "- Reinterpret modern elements into era-appropriate equivalents when needed.",
            "- Season should color the mood and visuals but not override the era.",
            "- Keep the genre structure and core message intact.",
            "- Avoid heavy historical exposition or forced slang.",
            "- Avoid anachronisms that break the chosen era.",
        ]
    )
    return "\n".join(lines)


def build_prompt(genre_prompt: dict[str, str], language_label: str, era_label: str | None, season_label: str | None) -> str:
    world_setting_block = build_world_setting_block(era_label, season_label)
    prompt_lines = [
        f"Genre: {genre_prompt['title']}",
        "",
        "Guidelines:",
        genre_prompt["criteria"],
        "",
        "Scene Elements Guidance:",
        "- subject: protagonist or main focus",
        "- action: key action or moment",
        "- setting: place, time, or environment",
        "- composition: camera angle or framing",
        "- lighting: light direction or time of day",
        "- style: visual style notes",
        "",
        "Request:",
        genre_prompt["request"],
        "",
    ]
    if world_setting_block:
        prompt_lines.extend([world_setting_block, ""])
    prompt_lines.extend(
        [
            "Language:",
            language_label,
            "",
            "Produce exactly one JSON object in the following format:",
            "{",
            '  "candidates": [',
            "    {",
            '      "id": "T1",',
            '      "title": "...",',
            '      "description": "A single paragraph that blends the six elements naturally",',
            '      "sceneElements": {',
            '        "subject": "...",',
            '        "action": "...",',
            '        "setting": "...",',
            '        "composition": "...",',
            '        "lighting": "...",',
            '        "style": "..."',
            "      },",
            '      "hook": "..."',
            "    }",
            "  ]",
            "}",
        ]
    )
    return "\n".join(prompt_lines)


def build_system_prompt(language_label: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(language_label=language_label)
