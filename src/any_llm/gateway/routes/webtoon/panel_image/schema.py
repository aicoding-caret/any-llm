from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from any_llm.gateway.routes.image import ImageUsage

ResolutionOption = Literal["1K", "2K", "4K"]
AspectRatioOption = Literal[
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "4:5",
    "5:4",
    "9:16",
    "16:9",
    "21:9",
]

class SceneElements(BaseModel):
    subject: Optional[str] = None
    action: Optional[str] = None
    setting: Optional[str] = None
    composition: Optional[str] = None
    lighting: Optional[str] = None
    style: Optional[str] = None

class PreviousPanel(BaseModel):
    panel: int
    scene: str
    dialogue: Optional[str] = None
    metadata: Optional[str] = None

class SceneReference(BaseModel):
    base64: str
    mimeType: Optional[str] = None
    purpose: Optional[Literal["background", "character", "style"]]

class CharacterSheetMetadataEntry(BaseModel):
    name: str
    summary: Optional[str] = None
    outfit: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    accessories: Optional[List[str]] = None
    hair: Optional[str] = None
    face: Optional[str] = None
    body: Optional[str] = None
    props: Optional[List[str]] = None
    shoes: Optional[List[str]] = None
    notes: Optional[List[str]] = None

class GeneratePanelImageRequest(BaseModel):
    scene: str
    dialogue: Optional[str] = None
    characters: List[str]
    style: str
    panelNumber: int
    era: Optional[str] = None
    season: Optional[str] = None
    characterDescriptions: Optional[List[str]] = None
    characterImages: Optional[List[str]] = None
    styleDoc: Optional[str] = None
    sceneElements: Optional[SceneElements] = None
    previousPanels: Optional[List[PreviousPanel]] = None
    characterSheetMetadata: Optional[List[CharacterSheetMetadataEntry]] = None
    characterGenerationMode: Optional[Literal["ai", "caricature"]]
    characterCaricatureStrengths: Optional[List[str]] = None
    resolution: Optional[ResolutionOption] = None
    aspectRatio: Optional[AspectRatioOption] = None
    revisionNote: Optional[str] = None
    references: Optional[List[SceneReference]] = None
    analysisLevel: Optional[Literal["fast", "full"]] = None
    model: Optional[str] = None

class GeneratePanelImageResponse(BaseModel):
    mimeType: str
    base64: str
    prompt: str
    texts: List[str] = Field(default_factory=list)
    thoughts: List[str] = Field(default_factory=list)
    usage: Optional[ImageUsage] = None
