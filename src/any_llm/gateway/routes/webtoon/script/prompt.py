from __future__ import annotations

from .schema import Language, SceneElements

STYLE_PROMPTS: dict[str, dict[str, str]] = {
    "webtoon": {
        "name": "웹툰 스타일",
        "imagePrompt": "Korean webtoon style, clean line art, digital coloring, vibrant colors, modern illustration, professional manhwa art, detailed character design, smooth shading, clear outlines",
    },
    "manga": {
        "name": "만화 스타일",
        "imagePrompt": "Japanese manga style, detailed screen tones, expressive line work, dynamic composition, black and white ink art, shounen/shoujo manga aesthetic, detailed backgrounds, varied line weights",
    },
    "cartoon": {
        "name": "카툰 스타일",
        "imagePrompt": "Cute cartoon style, simple rounded shapes, bright vibrant colors, friendly character design, kawaii aesthetic, chibi proportions, clean flat colors, playful illustration",
    },
    "illustration": {
        "name": "일러스트",
        "imagePrompt": "Detailed digital illustration, soft lighting, emotional atmosphere, painterly style, artistic composition, rich textures, sophisticated color palette, professional book illustration quality",
    },
    "realistic": {
        "name": "실사 스타일",
        "imagePrompt": "Photorealistic style, realistic textures, natural lighting, high detail photography, professional photo quality, cinematic composition, realistic shadows and highlights",
    },
    "3d": {
        "name": "3D 렌더링",
        "imagePrompt": "3D rendered style, Pixar quality, smooth 3D models, professional rendering, volumetric lighting, detailed textures, Disney/Pixar aesthetic, clean 3D animation style",
    },
}

LANGUAGE_LABELS: dict[Language, str] = {
    "ko": "Korean",
    "zh": "Chinese",
    "ja": "Japanese",
}

GENRE_TONE_GUIDES: dict[str, str] = {
    "daily": "Everyday comedy tone: keep it conversational and end with a twist or relatable punchline in the final panel.",
    "pets": "Pet-centered tone: keep human dialogue short and honest, and any animal speech lightly anthropomorphized.",
    "emotional": "Heartfelt tone: use calm, understated language and let the final panel rest with minimal words.",
    "satire": "Satirical tone: favor metaphor over direct criticism, keep it short and meaningful without aggression.",
    "self": "Self-development tone: focus on gentle realizations, avoid commands, and finish with a moment of personal insight.",
    "concept": "Explanation tone: use plain language, everyday comparisons, and summarize the key idea in the last panel.",
    "campaign": "Campaign tone: build empathy before delivering the message; questions are welcome, avoid feeling like an ad.",
    "sci-fi": "SF tone: start with a 'what if' premise, show the speculative idea, and land with a clever reveal.",
    "language": "Language-learning tone: use short conversational exchanges that highlight useful expressions and their meaning.",
    "relationship": "Relationship tone: trace emotional beats carefully, keep the dialogue authentic, and maintain a balanced tone.",
}

GENRE_PUNCTUATION_GUIDES: dict[str, str] = {
    "daily": "Light and playful. Use ! or ~ sparingly for humor; avoid repeated chains.",
    "pets": "Soft and cute. Prefer gentle ? or ~; avoid harsh or excessive marks.",
    "emotional": "Restrained. Minimize ?, !, ~, ^; allow only when absolutely needed.",
    "satire": "Sharp but controlled. Use ? or ! sparingly; keep it subtle.",
    "self": "Reflective. Prefer ? for contemplation; avoid ! and ~.",
    "concept": "Neutral and clear. Use ? only for rhetorical prompts; avoid ~ and ^.",
    "campaign": "Empathetic. Use ? or ! minimally to support the message.",
    "sci-fi": "Measured. Allow a single ! for a reveal; otherwise keep it minimal.",
    "language": "Conversational. Use ? and ! naturally; keep it light.",
    "relationship": "Emotional but controlled. Allow ! or ~ lightly; avoid overuse.",
}

CARICATURE_GUIDE = (
    "If the character generation mode is caricature, keep dialogue short, conversational, and snappy. "
    "Prefer 1 concise sentence per line."
)

ERA_IDS = ["any", "modern", "nineties", "seventies-eighties", "joseon", "future"]
SEASON_IDS = ["any", "spring", "summer", "autumn", "winter"]

def get_style_prompt(style_id: str) -> dict[str, str]:
    return STYLE_PROMPTS.get(
        style_id,
        {
            "name": "웹툰 스타일",
            "imagePrompt": "Korean webtoon style, clean line art, digital coloring, vibrant colors",
        },
    )

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
    }.get(era)

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
    }.get(season)

def build_world_setting_block(era_label: str | None, season_label: str | None) -> str:
    if not era_label and not season_label:
        return ""
    lines = ["World Setting:"]
    if era_label:
        lines.append(f"Era: {era_label}")
    if season_label:
        lines.append(f"Season: {season_label}")
    lines.extend(
        [
            "- If an era is provided, make it clearly visible through setting, props, and social context.",
            "- Reinterpret modern elements into era-appropriate equivalents when needed.",
            "- Dialogue should reflect era-appropriate diction/formality without becoming hard to read.",
            "- Season should color the mood and visuals but not override the era.",
            "- If the art style implies a different era, keep the rendering style but prioritize the chosen era.",
            "- Keep the core topic and genre structure unchanged.",
            "- Avoid anachronisms that break the chosen era.",
        ]
    )
    return "\n".join(lines)

def build_topic_elements_block(elements: SceneElements | None) -> str:
    if not elements:
        return ""
    return "\n".join(
        [
            "Topic Elements (6):",
            f"- Subject: {elements.subject}",
            f"- Action: {elements.action}",
            f"- Setting: {elements.setting}",
            f"- Composition: {elements.composition}",
            f"- Lighting: {elements.lighting}",
            f"- Style: {elements.style}",
        ]
    )

def build_system_prompt(language: Language, style_prompt: dict[str, str]) -> str:
    return (
        "You are a scriptwriter specialized in 4-panel webtoons.\n\n"
        "Follow these rules without exception.\n\n"
        "[General Rules]\n"
        "1. Output must be valid JSON only.\n"
        "2. Each panel's dialogue should fit directly into a speech bubble.\n"
        "3. Keep each dialogue line to 1 short sentence; use 2-3 lines if the scene benefits from a brief back-and-forth.\n"
        "4. Separate multiple dialogue lines using newline characters (\\n) with no bullet or numbering.\n"
        "5. Do not include bracketed stage directions, narrative descriptions, or explicit emotion labels in the dialogue.\n"
        "6. Dialogue must carry emotional subtext or relationship nuance; avoid dry informational lines.\n"
        f"7. Keep dialogue natural in spoken {LANGUAGE_LABELS[language]}; brief hesitations or fillers are allowed.\n"
        "8. Each line should reflect the speaker's personality and situation.\n"
        "9. You may use punctuation such as ?, !, ~, ^ when appropriate, but at most 1-2 marks per line and no repeated chains.\n"
        "10. Use these marks only when they fit the character's personality and the scene tone; keep serious or calm scenes restrained.\n"
        "11. Do not simply repeat the scene description word-for-word.\n"
        "12. Scene descriptions must include a visible emotional beat and one small sensory or atmosphere cue.\n"
        "13. The final panel must deliver the genre-appropriate payoff (comedy: punchline/reversal, drama: emotional closure, explanation: summary).\n"
        "14. Use only the actual character names as speakers; do not invent a separate “narration” character or voice.\n"
        "15. If a world setting is provided, treat the era as mandatory and make it obvious in scenes and diction while keeping it easy to read.\n"
        "16. Avoid anachronisms that break the chosen era.\n"
        "17. Avoid trendy slang, memes, or references to real people.\n"
        "18. For each panel, include a sceneElements object with subject, action, setting, composition, lighting, and style.\n"
        "19. Keep each sceneElements field concise and specific (short phrases are fine).\n"
        '20. Provide dialogue in two forms: "dialogue" (lines separated by \\n) and "dialogueLines" (array of {speaker, text}).\n'
        "\n"
        f"Art Style Reference: {style_prompt['name']}\n"
        f"Visual Tone Reference: {style_prompt['imagePrompt']}\n"
        "Return only the JSON object outlined below without additional commentary."
    )

def build_user_prompt(
    topic: str,
    style: str,
    genre: str,
    normalized_elements: SceneElements | None,
    language_label: str,
    tone_guide: str,
    punctuation_guide: str,
    caricature_mode: bool,
    world_setting: str,
    style_prompt: dict[str, str],
) -> str:
    topic_elements_block = build_topic_elements_block(normalized_elements)
    style_reference = [
        f"Style Prompt Reference: {style_prompt['name']}",
        f"Visual Tone Reference: {style_prompt['imagePrompt']}",
    ]
    lines = [
        f"This is a 4-panel webtoon concept in the {genre} genre with the {style} style.",
        f"Topic: {topic}",
    ]
    if topic_elements_block:
        lines.extend(["", topic_elements_block])
    lines.extend(
        [
            "",
            *style_reference,
            f"Scene Tone Guide: {tone_guide}",
            f"Punctuation Tone Guide: {punctuation_guide}",
        ]
    )
    if caricature_mode:
        lines.append(f"Dialogue Guide: {CARICATURE_GUIDE}")
    if world_setting:
        lines.extend(["", world_setting])
    lines.extend(
        [
            "",
            "Requirements:",
            "- Provide exactly four panels.",
            "- Each panel must include a concise scene description, a named speaker, and 1-3 dialogue lines.",
            "- Each panel must include sceneElements with the six keys: subject, action, setting, composition, lighting, style.",
            "- Keep each dialogue line to one short sentence; separate lines with \\n only.",
            '- Also provide "dialogueLines" as an array of {speaker, text} that matches the dialogue lines.',
            "- Make sure every line reflects the speaker's personality, emotional state, and relationship tension/affection.",
            "- Do not invent a separate narrator role; convey narrative beats via the scene descriptions and character dialogue only.",
            "- Deliver the appropriate genre payoff in the final panel (comedy: punchline/reversal, drama: emotional closure, explanation: summary).",
            "- Scene descriptions should include subtle body language and a sensory or atmosphere hint (sound, temperature, light).",
            f"- The generated dialogue should be written in {language_label}.",
            "",
            "Respond using only the JSON structure below:",
            "{",
            '  "panels": [',
            "    {",
            '      "panelNumber": 1,',
            '      "scene": "...",',
            '      "sceneElements": {',
            '        "subject": "...",',
            '        "action": "...",',
            '        "setting": "...",',
            '        "composition": "...",',
            '        "lighting": "...",',
            '        "style": "..."',
            "      },",
            '      "speaker": "...",',
            '      "dialogue": "...\\n...",',
            '      "dialogueLines": [',
            '        { "speaker": "...", "text": "..." }',
            "      ],",
            '      "characters": ["A", "B"]',
            "    },",
            "    ...",
            "  ],",
            '  "mainCharacters": [',
            '    { "name": "...", "description": "...", "role": "..." },',
            "    ...",
            "  ]",
            "}",
        ]
    )
    return "\n".join(lines)
