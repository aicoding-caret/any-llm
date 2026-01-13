from __future__ import annotations

from typing import Any, Mapping

from pydantic import BaseModel, Field


class CharacterSheetRequest(BaseModel):
    imageUrl: str


class CharacterSheetMetadata(BaseModel):
    summary: str | None = None
    persona: str | None = None
    outfit: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    accessories: list[str] = Field(default_factory=list)
    hair: str | None = None
    face: str | None = None
    body: str | None = None
    props: list[str] = Field(default_factory=list)
    shoes: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CharacterSheetResponse(BaseModel):
    metadata: CharacterSheetMetadata

DEFAULT_MODEL = "gemini:gemini-2.5-flash"