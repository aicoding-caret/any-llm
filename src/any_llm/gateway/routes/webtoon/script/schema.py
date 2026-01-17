from __future__ import annotations

from typing import Literal, Sequence

from pydantic import BaseModel

Language = Literal["ko", "zh", "ja"]
CharacterCount = Literal["solo", "duo", "group"]
PanelCount = Literal[1, 3, 4, 6]

DEFAULT_PANEL_COUNT: PanelCount = 4
DEFAULT_CHARACTER_COUNT: CharacterCount = "duo"

ERA_IDS = ["any", "modern", "nineties", "seventies-eighties", "joseon", "future"]
SEASON_IDS = ["any", "spring", "summer", "autumn", "winter"]


class SceneElements(BaseModel):
    subject: str
    action: str
    setting: str
    composition: str
    lighting: str
    style: str


class DialogueLine(BaseModel):
    speaker: str
    text: str


class Panel(BaseModel):
    panelNumber: int
    scene: str
    sceneElements: SceneElements
    speaker: str
    dialogue: str
    dialogueLines: Sequence[DialogueLine]
    characters: Sequence[str]


class MainCharacter(BaseModel):
    name: str
    description: str
    role: str


class GenerateScriptRequest(BaseModel):
    topic: str
    topicElements: SceneElements | None = None
    style: str
    genre: str
    era: str | None = None
    season: str | None = None
    characterGenerationMode: Literal["ai", "caricature"] | None = "ai"
    language: Language | None = None
    panelCount: PanelCount | None = None
    characterCount: CharacterCount | None = None


class GenerateScriptResponse(BaseModel):
    panels: Sequence[Panel]
    mainCharacters: Sequence[MainCharacter]


DEFAULT_MODEL = "gemini-2.5-flash"
