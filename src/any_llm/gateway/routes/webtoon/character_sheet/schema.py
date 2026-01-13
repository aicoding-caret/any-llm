from __future__ import annotations

from pydantic import BaseModel


class CharacterEntry(BaseModel):
    name: str
    description: str = ""


class SceneElements(BaseModel):
    subject: str | None = None
    action: str | None = None
    setting: str | None = None
    composition: str | None = None
    lighting: str | None = None
    style: str | None = None


class GenerateCharacterSheetRequest(BaseModel):
    characters: list[CharacterEntry]
    style: str
    styleDoc: str | None = None  # noqa: N815
    era: str | None = None
    season: str | None = None
    sceneElements: SceneElements | None = None  # noqa: N815
    model: str | None = None


class CharacterSheetEntry(BaseModel):
    name: str
    imageUrl: str | None  # noqa: N815
    metadata: str


class GenerateCharacterSheetResponse(BaseModel):
    characterSheets: list[CharacterSheetEntry]  # noqa: N815
