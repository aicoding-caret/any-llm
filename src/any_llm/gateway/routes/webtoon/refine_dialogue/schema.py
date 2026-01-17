from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Language = Literal["ko", "zh", "ja"]
Tone = Literal["neutral", "humor", "serious", "emotional"]


class RefineDialogueRequest(BaseModel):
    dialogue: str
    tone: Tone | None = None
    scene: str | None = None
    speaker: str | None = None
    characterGenerationMode: Literal["ai", "caricature"] | None = "ai"
    language: Language | None = None
    era: str | None = None
    season: str | None = None


class RefineDialogueResponse(BaseModel):
    dialogue: str

DEFAULT_MODEL = "gemini-2.5-flash"
