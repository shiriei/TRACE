"""TRACE Domain and Persistence Model for Stickers and Ownership."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StickerDefinition:
    """Domain model representing a sticker definition in the catalogue."""

    id: str
    name: str
    description: str
    theme: str  # "botanical" | "creatures" | "vintage" | "humor" | "cozy" | "planner"
    rarity: str  # "common" | "uncommon" | "rare" | "legendary"
    asset_path: str
    unlock_type: str  # "starter" | "milestone" | "streak" | "manual"
    tags: List[str] = field(default_factory=list)
    milestone_requirement: Optional[Dict[str, Any]] = None
    is_asset_available: bool = False


@dataclass
class StickerPackDefinition:
    """Domain model representing a reward sticker pack definition."""

    id: str
    name: str
    description: str
    milestone_requirement: Dict[str, Any]
    sticker_ids: List[str] = field(default_factory=list)


@dataclass
class StickerOwnershipModel:
    """Domain model representing a user's persistent ownership of an unlocked sticker."""

    id: str
    sticker_id: str
    unlocked_at: str
    unlock_reason: str
    source: str  # "daily_reward" | "milestone_reward" | "manual_grant"
