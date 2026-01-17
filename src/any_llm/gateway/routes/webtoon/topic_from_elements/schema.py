from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Language = Literal["ko", "zh", "ja"]
CharacterCount = Literal["solo", "duo", "group"]
PanelCount = Literal[1, 3, 4, 6]
DEFAULT_PANEL_COUNT: PanelCount = 4


class SceneElements(BaseModel):
    subject: str
    action: str
    setting: str
    composition: str
    lighting: str
    style: str


class GenerateTopicFromElementsRequest(BaseModel):
    sceneElements: SceneElements
    genre: str | None = None
    language: Language | None = None
    era: str | None = None
    season: str | None = None
    characterCount: CharacterCount | None = None
    panelCount: PanelCount | None = None


class GenerateTopicFromElementsResponse(BaseModel):
    topic: str


DEFAULT_MODEL = "gemini-2.5-flash"
