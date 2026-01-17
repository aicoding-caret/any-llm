from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, field_validator

Language = Literal["ko", "zh", "ja"]
CharacterCount = Literal["solo", "duo", "group"]
PanelCount = Literal[1, 3, 4, 6]

ERA_IDS = ["any", "modern", "nineties", "seventies-eighties", "joseon", "future"]
SEASON_IDS = ["any", "spring", "summer", "autumn", "winter"]
CHARACTER_COUNT_IDS = ["solo", "duo", "group"]
PANEL_COUNT_IDS = [1, 3, 4, 6]
DEFAULT_PANEL_COUNT: PanelCount = 4


class SceneElements(BaseModel):
    subject: str = ""
    action: str = ""
    setting: str = ""
    composition: str = ""
    lighting: str = ""
    style: str = ""

    @field_validator("subject", "action", "setting", "composition", "lighting", "style", mode="before")
    @classmethod
    def coerce_none_to_empty(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v)


class TopicCandidate(BaseModel):
    id: str
    title: str
    description: str
    sceneElements: SceneElements
    hook: str | None = None


class GenerateTopicRequest(BaseModel):
    genre: str
    language: Language | None = None
    era: str | None = None
    season: str | None = None
    characterCount: CharacterCount | None = None
    panelCount: PanelCount | None = None
    model: str | None = None
    user: str | None = None


class GenerateTopicResponse(BaseModel):
    candidates: list[TopicCandidate]

    @field_validator("candidates")
    @classmethod
    def ensure_exact_count(cls, v: list[TopicCandidate]) -> list[TopicCandidate]:
        if len(v) != 5:
            raise ValueError("Exactly five topic candidates are required")
        return v


DEFAULT_MODEL = "gemini-2.5-flash"
