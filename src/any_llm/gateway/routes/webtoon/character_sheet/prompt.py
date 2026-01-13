from __future__ import annotations

from .schema import SceneElements

SCENE_ELEMENT_KEYS = ["subject", "action", "setting", "composition", "lighting", "style"]
SCENE_ELEMENT_LABELS = {
    "subject": "Subject(주제)",
    "action": "Action(동작)",
    "setting": "Setting(환경)",
    "composition": "Composition(구성/카메라)",
    "lighting": "Lighting(조명)",
    "style": "Style(스타일)",
}

ERA_LABELS = {
    "any": "Any",
    "modern": "Modern",
    "nineties": "1990s",
    "seventies-eighties": "1970s-80s",
    "joseon": "Joseon / Traditional",
    "future": "Future / Virtual",
}

SEASON_LABELS = {
    "any": "Any",
    "spring": "Spring",
    "summer": "Summer",
    "autumn": "Autumn",
    "winter": "Winter",
}

STYLE_PROMPTS: dict[str, dict[str, str]] = {
    "webtoon": {
        "id": "webtoon",
        "name": "Webtoon Style",
        "system_prompt": "You are a Korean webtoon professional image generation AI producing clean line art with digital coloring.",
        "image_prompt": "Korean webtoon style, clean line art, digital coloring, vibrant colors, modern illustration, professional manhwa art, detailed character design, smooth shading, clear outlines",
        "negative_prompt": "messy lines, sketch style, rough draft, watercolor, oil painting, realistic photo, 3D render, blurry, low quality",
    },
    "manga": {
        "id": "manga",
        "name": "Manga Style",
        "system_prompt": "You are a Japanese manga image generation AI using expressive line work and detailed screen tones.",
        "image_prompt": "Japanese manga style, detailed screen tones, expressive line work, dynamic composition, black and white ink art, shounen/shoujo manga aesthetic, detailed backgrounds, varied line weights",
        "negative_prompt": "colored, full color, digital painting, western comic style, realistic, photo, 3D, blurry, low detail",
    },
    "cartoon": {
        "id": "cartoon",
        "name": "Cartoon Style",
        "system_prompt": "You are a friendly cartoon image generation AI that favors simple rounded shapes and bright palettes.",
        "image_prompt": "Cute cartoon style, simple rounded shapes, bright vibrant colors, friendly character design, kawaii aesthetic, chibi proportions, clean flat colors, playful illustration",
        "negative_prompt": "realistic, detailed, complex, dark, gritty, serious, photo-realistic, 3D render, sketch",
    },
    "illustration": {
        "id": "illustration",
        "name": "Illustration Style",
        "system_prompt": "You are an emotional illustration expert delivering soft lighting and expressive atmosphere.",
        "image_prompt": "Detailed digital illustration, soft lighting, emotional atmosphere, painterly style, artistic composition, rich textures, sophisticated color palette, professional book illustration quality",
        "negative_prompt": "simple, cartoon, chibi, low detail, flat colors, sketch, rough, unfinished, photo",
    },
    "realistic": {
        "id": "realistic",
        "name": "Realistic Style",
        "system_prompt": "You are a photorealistic image generation AI delivering natural lighting and high detail.",
        "image_prompt": "Photorealistic style, realistic textures, natural lighting, high detail photography, professional photo quality, cinematic composition, realistic shadows and highlights",
        "negative_prompt": "cartoon, anime, illustration, drawn, painted, sketch, abstract, stylized, flat, low quality, blurry",
    },
    "3d": {
        "id": "3d",
        "name": "3D Render Style",
        "system_prompt": "You are a 3D rendering expert creating smooth Pixar/Disney inspired characters.",
        "image_prompt": "3D rendered style, Pixar quality, smooth 3D models, professional rendering, volumetric lighting, detailed textures, Disney/Pixar aesthetic, clean 3D animation style",
        "negative_prompt": "2D, flat, hand-drawn, sketch, photo, realistic, anime style, low poly, draft quality",
    },
}

DEFAULT_STYLE = STYLE_PROMPTS["webtoon"]

SYSTEM_PROMPT = (
    "You are a webtoon character sheet generation expert.\n"
    "Create a reference image that ensures consistent appearance across every panel.\n\n"
    "[Required Rules]\n"
    "1. The character must face forward.\n"
    "2. Pose should be neutral and simple (standing or naturally standing).\n"
    "3. Minimize facial expression (neutral or slight smile).\n"
    "4. Never include any text, letters, numbers, logos, subtitles, UI elements, or watermarks.\n"
    "5. The image must contain only the character; do not add extra objects, props, or background elements.\n"
    "6. Background must be a solid color or very simple studio backdrop.\n"
    "7. Describe the appearance clearly so the same character can be regenerated consistently.\n"
    "8. Do not mention resemblance to real people, celebrities, or public figures.\n\n"
    "[Purpose]\n"
    "This image serves as the reference for all subsequent panels, signaling, \"Draw this character exactly as shown.\"\n"
)

WORLD_SETTING_GUIDANCE = (
    "- If an era is provided, the outfit and accessories must clearly reflect it.\n"
    "- Season should adjust layers, fabrics, and color palette without overriding the era.\n"
    "- If the art style implies a different era, keep the rendering style but prioritize the chosen era.\n"
    "- Keep the background plain as required.\n"
    "- Avoid anachronistic items that break the chosen era.\n"
)

def get_style_prompt(style_id: str) -> dict[str, str]:
    return STYLE_PROMPTS.get(style_id) or DEFAULT_STYLE


def normalize_scene_elements(value: SceneElements | None) -> dict[str, str]:
    return {
        key: (getattr(value, key) or "").strip() if value else ""
        for key in SCENE_ELEMENT_KEYS
    }


def has_scene_elements(elements: dict[str, str] | None) -> bool:
    return bool(elements and any(elements[key] for key in SCENE_ELEMENT_KEYS))


def format_scene_elements(elements: dict[str, str]) -> str:
    lines: list[str] = []
    for key in SCENE_ELEMENT_KEYS:
        value = elements.get(key, "").strip()
        if value:
            label = SCENE_ELEMENT_LABELS.get(key, key)
            lines.append(f"- {label}: {value}")
    return "\n".join(lines)


def build_scene_context_block(scene_elements: SceneElements | None) -> str | None:
    normalized = normalize_scene_elements(scene_elements)
    if not has_scene_elements(normalized):
        return None
    lines = ["## Scene Context (for consistency)", format_scene_elements(normalized)]
    lines.append("Guidance: Use this only to align palette, mood, and wardrobe. Keep the background plain.")
    return "\n".join(line for line in lines if line)


def build_world_setting_block(era: str | None, season: str | None) -> str | None:
    parts: list[str] = []
    if era:
        era_label = ERA_LABELS.get(era, era)
        if era_label:
            parts.append(f"Era: {era_label}")
    if season:
        season_label = SEASON_LABELS.get(season, season)
        if season_label:
            parts.append(f"Season: {season_label}")
    if not parts:
        return None
    return "World Setting:\n" + "\n".join([
        *parts,
        "Guidance:",
        *WORLD_SETTING_GUIDANCE.split("\n"),
    ])


def build_prompt(
    style_id: str,
    character_name: str,
    character_description: str,
    style_doc: str | None,
    era: str | None,
    season: str | None,
    scene_elements: SceneElements | None,
    aspect_ratio: str,
    resolution: str,
) -> str:
    style_prompt = get_style_prompt(style_id)
    style_guide = f"{style_prompt['system_prompt']}\n{style_prompt['image_prompt']}"
    world_block = build_world_setting_block(era, season)
    scene_block = build_scene_context_block(scene_elements)
    doc_instruction = f"Reference these style notes:\n{style_doc}\n" if style_doc else ""
    character_description_text = f"{character_name}: {character_description}"
    output_format = f"PNG, {aspect_ratio}, {resolution} quality"

    sections: list[str] = [
        f"# Role\nYou are a {style_prompt['name']} image generation expert.",
        f"# System Instruction\n{SYSTEM_PROMPT}",
        "# Instruction\nAdhere strictly to the Key Style Guide below and create a single-character sheet that matches the provided data. Render the subject head-to-toe in a standing pose against a plain solid-color background. Include only the character and worn accessories; do not add props, signage, or any text.",
        f"---\n## Key Style Guide\n{style_guide}",
        "---\n## Character Data",
        f"* Character: {character_description_text}",
        "* Requirements: Show the entire body in a standing pose on a simple monochrome backdrop.",
        f"## Output Format\n{output_format}",
    ]

    if doc_instruction:
        sections.append(doc_instruction.strip())
    if world_block:
        sections.append(world_block)
    if scene_block:
        sections.append(scene_block)

    return "\n\n".join(section for section in sections if section).strip()
