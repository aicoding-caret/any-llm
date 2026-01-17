from __future__ import annotations

from .schema import CharacterCount, DEFAULT_PANEL_COUNT, Language, PanelCount, SceneElements

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

PANEL_COUNT_GUIDANCE: dict[int, dict[str, str]] = {
    1: {
        "structure": "single impactful scene",
        "flow": "One dramatic moment that conveys the entire message",
    },
    3: {
        "structure": "setup → development → punchline/twist",
        "flow": "Introduction → Build-up → Payoff",
    },
    4: {
        "structure": "setup → development → climax → resolution",
        "flow": "기 (Introduction) → 승 (Development) → 전 (Climax) → 결 (Resolution)",
    },
    6: {
        "structure": "extended narrative with emotional depth",
        "flow": "Hook → Setup → Rising action → Climax → Falling action → Resolution",
    },
}


def resolve_character_count_rule(character_count: CharacterCount | None) -> str:
    """Return the character count rule for the prompt."""
    if character_count and character_count in CHARACTER_COUNT_RULES:
        return CHARACTER_COUNT_RULES[character_count]
    # Default to duo for best webtoon results
    return CHARACTER_COUNT_RULES["duo"]


def resolve_panel_count_guidance(panel_count: PanelCount | None) -> dict[str, str]:
    """Return guidance for the given panel count setting."""
    if panel_count and panel_count in PANEL_COUNT_GUIDANCE:
        return PANEL_COUNT_GUIDANCE[panel_count]
    return PANEL_COUNT_GUIDANCE[DEFAULT_PANEL_COUNT]


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


SCENE_ELEMENTS_GUIDE = """Scene Elements Guide:
- Subject: WHO is in the scene? Be specific about characters and their relationship.
  (e.g., "a stoic robot barista", "two coworkers with opposite personalities", "a cat and its exhausted owner")
- Action: WHAT is happening? Describe the key interaction or event.
  (e.g., "arguing about coffee preferences", "discovering a secret", "waking someone up at dawn")
- Setting: WHERE does the scene take place? Include atmosphere.
  (e.g., "a cramped office break room", "a futuristic cafe on Mars", "a messy bedroom at 4am")
- Composition: HOW is the shot framed? Camera angle and framing.
  (e.g., "extreme close-up on facial expressions", "wide shot showing the whole scene", "low angle dramatic shot")
- Lighting: What MOOD does the light create?
  (e.g., "harsh fluorescent office lighting", "golden hour warmth", "dramatic shadows from a single lamp")
- Style: What VISUAL aesthetic defines the tone?
  (e.g., "slice-of-life comedy", "noir thriller", "warm healing", "exaggerated slapstick")"""

FEW_SHOT_EXAMPLES = """Examples:

Example 1:
Input Elements:
- Subject: 직장인 두 명
- Action: 커피 취향 논쟁
- Setting: 사무실 휴게실
- Composition: 대화 장면
- Lighting: 형광등 조명
- Style: 일상 코미디

Output:
{"topic": "매일 아침 휴게실에서 만나는 두 직장인이 아메리카노 vs 달달한 라떼로 논쟁하다가, 결국 둘 다 자판기 커피를 마시며 허탈해하는 상황"}

Example 2:
Input Elements:
- Subject: 고양이와 집사
- Action: 새벽에 밥 달라고 깨움
- Setting: 어두운 침실
- Composition: 클로즈업
- Lighting: 창문으로 들어오는 달빛
- Style: 힐링/공감

Output:
{"topic": "새벽 4시, 고양이가 얼굴을 콕콕 찌르며 집사를 깨우고, 눈을 뜨자마자 밥그릇 앞으로 안내하는 귀여우면서도 피곤한 일상"}"""


def build_prompt(
    topic: str,
    normalized_elements: SceneElements,
    genre: str | None,
    language_label: str,
    world_setting_block: str,
    character_count: CharacterCount | None = None,
    panel_count: PanelCount | None = None,
) -> str:
    character_rule = resolve_character_count_rule(character_count)
    panel_guidance = resolve_panel_count_guidance(panel_count)
    resolved_panel_count = panel_count or DEFAULT_PANEL_COUNT
    lines = [
        f"You are a creative webtoon planner who transforms scene elements into engaging {resolved_panel_count}-panel story topics.",
        "",
        f"Panel Structure: {panel_guidance['structure']}",
        f"Flow: {panel_guidance['flow']}",
        "",
        "Your task: Take the provided elements and CREATE A UNIQUE TWIST or unexpected angle.",
        "Do NOT simply summarize the elements. Instead, find a fresh perspective, a surprising turn, or a humorous spin.",
        "",
        SCENE_ELEMENTS_GUIDE,
        "",
        "Creative transformation tips:",
        "- Add an unexpected obstacle or misunderstanding",
        "- Find the hidden comedy in everyday situations",
        f"- Create a surprising reversal suitable for {resolved_panel_count}-panel progression",
        "- Exaggerate a small detail into the main conflict",
        "- Give characters contrasting reactions to the same situation",
        "",
        "Rules:",
        "- Output must be a single JSON object only.",
        '- Use only one key: "topic".',
        f"- Write naturally in {language_label}.",
        "- 2–3 sentences in a single paragraph.",
        "- The topic must feel DIFFERENT from a literal description of the elements.",
        f"- Include a clear comedic beat or emotional payoff suitable for {resolved_panel_count} panels.",
        "- No bullets, numbering, headings, quotes, or parenthetical explanations.",
        character_rule,
        "",
        FEW_SHOT_EXAMPLES,
        "",
        "---",
        "",
        f"Genre: {genre or '정보 없음'}",
        f"Panel Count: {resolved_panel_count} panels ({panel_guidance['structure']})",
    ]
    if world_setting_block:
        lines.extend(["", world_setting_block])
    lines.extend(
        [
            "",
            "Your Input Elements:",
            f"- Subject: {normalized_elements.subject or '(정보 없음)'}",
            f"- Action: {normalized_elements.action or '(정보 없음)'}",
            f"- Setting: {normalized_elements.setting or '(정보 없음)'}",
            f"- Composition: {normalized_elements.composition or '(정보 없음)'}",
            f"- Lighting: {normalized_elements.lighting or '(정보 없음)'}",
            f"- Style: {normalized_elements.style or '(정보 없음)'}",
            "",
            "Now transform these elements into a FRESH, UNEXPECTED topic.",
            "Remember: Don't just describe the scene - find the twist, the comedy, or the surprise!",
            "",
            'Output format:',
            '{"topic":"..."}',
        ]
    )
    return "\n".join(lines)
