from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Language = Literal["ko", "zh", "ja"]


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


class GenerateTopicFromElementsResponse(BaseModel):
    topic: str


DEFAULT_MODEL = "gemini:gemini-2.5-flash"
