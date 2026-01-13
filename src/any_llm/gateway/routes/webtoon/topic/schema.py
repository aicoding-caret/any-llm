from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, validator

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
    model: str | None = None
    user: str | None = None


class GenerateTopicResponse(BaseModel):
    candidates: list[TopicCandidate]

    @validator("candidates")
    def ensure_exact_count(cls, values: list[TopicCandidate]) -> list[TopicCandidate]:
        if len(values) != 5:
            raise ValueError("Exactly five topic candidates are required")
        return values


DEFAULT_MODEL = "gemini:gemini-2.5-flash"
