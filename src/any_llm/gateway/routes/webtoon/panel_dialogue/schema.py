from __future__ import annotations

from typing import Literal, Sequence

from pydantic import BaseModel

Language = Literal["ko", "zh", "ja"]

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


class GeneratePanelDialogueRequest(BaseModel):
    panelNumber: int | None = None
    speakers: Sequence[str]
    scene: str | None = None
    sceneElements: SceneElements | None = None
    topic: str | None = None
    genre: str | None = None
    style: str | None = None
    era: str | None = None
    season: str | None = None
    language: Language | None = None
    characterGenerationMode: Literal["ai", "caricature"] | None = "ai"


class GeneratePanelDialogueResponse(BaseModel):
    dialogueLines: Sequence[DialogueLine]

DEFAULT_MODEL = "gemini:gemini-2.5-flash"