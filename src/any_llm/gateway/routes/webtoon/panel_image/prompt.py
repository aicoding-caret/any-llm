from __future__ import annotations

from typing import Iterable

from .schema import GeneratePanelImageRequest, SceneElements, SceneReference, PreviousPanel

SCENE_ELEMENT_LABELS = (
    ("subject", "Subject"),
    ("action", "Action"),
    ("setting", "Setting"),
    ("composition", "Composition"),
    ("lighting", "Lighting"),
    ("style", "Scene Style"),
)

THOUGHT_INSTRUCTIONS = (
    "Use the provided dialogue and scene cues to convey emotion.",
    "Keep the focus on the characters and avoid background complexity unless requested.",
)


def _format_list(values: Iterable[str]) -> str:
    return ", ".join(value.strip() for value in values if value and value.strip())


def _scene_elements_block(scene_elements: SceneElements | None) -> str | None:
    if not scene_elements:
        return None
    lines = []
    for key, label in SCENE_ELEMENT_LABELS:
        value = getattr(scene_elements, key)
        if value:
            lines.append(f"- {label}: {value}")
    if not lines:
        return None
    return "Scene Elements:\n" + "\n".join(lines)


def _references_block(references: list[SceneReference] | None) -> str | None:
    if not references:
        return None
    summary: list[str] = []
    for ref in references:
        if ref.purpose:
            summary.append(f"{ref.purpose} reference provided")
        else:
            summary.append("reference provided")
    if not summary:
        return None
    return "References:\n- " + "\n- ".join(summary)


def _previous_panels_block(previous_panels: list[PreviousPanel] | None) -> str | None:
    if not previous_panels:
        return None
    lines = ["Previous panels context:"]
    for panel in previous_panels:
        line = f"Panel {panel.panel}: {panel.scene}"
        if panel.dialogue:
            line += f" | Dialogue: {panel.dialogue}"
        if panel.metadata:
            line += f" | Notes: {panel.metadata}"
        lines.append(line)
    return "\n".join(lines)


def build_prompt(request: GeneratePanelImageRequest) -> str:
    instructions: list[str] = [
        "Generate a single-panel webtoon illustration that clearly communicates the provided story data.",
        "Render only the characters and a minimal studio-like background; do not add any UI overlays, text, or logos.",
        "Match the requested art style exactly and keep character proportions consistent across panels.",
    ]

    if request.analysisLevel == "full":
        instructions.append("Provide rich environmental detail, lighting, and composition cues so the scene feels cinematic.")
    else:
        instructions.append("Prioritize clarity and readability; focus on essential props/lighting without over-rendering details.")

    components: list[str] = [
        f"Panel Number: {request.panelNumber}",
        f"Style: {request.style}",
    ]

    if request.era:
        components.append(f"Era: {request.era}")
    if request.season:
        components.append(f"Season: {request.season}")

    components.append(f"Scene: {request.scene}")

    if request.dialogue:
        components.append(f"Dialogue: {request.dialogue}")

    if request.characters:
        characters = _format_list(request.characters)
        components.append(f"Characters: {characters}")

    if request.characterDescriptions:
        descriptions = _format_list(request.characterDescriptions)
        components.append(f"Character details: {descriptions}")

    if request.sceneElements:
        elements = _scene_elements_block(request.sceneElements)
        if elements:
            components.append(elements)

    if request.previousPanels:
        components.append(_previous_panels_block(request.previousPanels))

    if request.characterSheetMetadata:
        summaries: list[str] = []
        for entry in request.characterSheetMetadata:
            summary_lines: list[str] = []
            if entry.summary:
                summary_lines.append(entry.summary)
            if entry.outfit:
                summary_lines.append("Outfit: " + _format_list(entry.outfit))
            if entry.colors:
                summary_lines.append("Colors: " + _format_list(entry.colors))
            if entry.accessories:
                summary_lines.append("Accessories: " + _format_list(entry.accessories))
            if entry.hair:
                summary_lines.append("Hair: " + entry.hair)
            if entry.body:
                summary_lines.append("Body: " + entry.body)
            if summary_lines:
                summaries.append(f"{entry.name} -> " + "; ".join(summary_lines))
        if summaries:
            components.append("Character references:\n" + "\n".join(f"- {line}" for line in summaries))

    if request.styleDoc:
        components.append(f"Style notes: {request.styleDoc}")

    if request.characterGenerationMode:
        components.append(f"Character generation mode: {request.characterGenerationMode}.")
    if request.characterCaricatureStrengths:
        strengths = _format_list(request.characterCaricatureStrengths)
        components.append(f"Caricature strengths: {strengths}")

    if request.revisionNote:
        components.append(f"Revision note: {request.revisionNote}")

    references_block = _references_block(request.references)
    if references_block:
        components.append(references_block)

    instructions_block = "\n".join(line for line in instructions if line)
    content_block = "\n".join(component for component in components if component)

    return f"{instructions_block}\n\n{content_block}".strip()
