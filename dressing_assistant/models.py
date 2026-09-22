from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

WardrobeCategory = Literal[
    "dress",
    "skirt",
    "top",
    "bottom",
    "outerwear",
    "shoes",
    "hosiery",
    "accessory",
    "other",
]


class WardrobeItem(BaseModel):
    id: str
    name: str
    category: WardrobeCategory
    subtype: str | None = None
    colors: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    pattern: str | None = None
    fit: str | None = None
    style_tags: list[str] = Field(default_factory=list)
    formality: int = Field(default=3, ge=1, le=5)
    seasons: list[str] = Field(default_factory=list)
    thickness: Literal["sheer", "light", "medium", "thick", "unknown"] = "unknown"
    scenes: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    notes: str = ""
    inference_status: Literal["inferred", "confirmed"] = "inferred"


class OutfitProposal(BaseModel):
    title: str
    item_ids: list[str] = Field(default_factory=list)
    reason: str


class ProposedOperation(BaseModel):
    target: Literal["wardrobe"] = "wardrobe"
    op: Literal["add", "update", "delete"]
    item_id: str | None = None
    item: dict[str, Any] | None = None
    fields: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""


class AssistantResult(BaseModel):
    reply: str
    intent: Literal[
        "recommend",
        "list_wardrobe",
        "edit_wardrobe",
        "ask_clarification",
        "chat",
    ] = "chat"
    outfits: list[OutfitProposal] = Field(default_factory=list)
    proposed_operations: list[ProposedOperation] = Field(default_factory=list)
    temporary_exclusions: list[str] = Field(default_factory=list)
    session_summary: str = ""


class AppliedOperation(BaseModel):
    ok: bool
    message: str
