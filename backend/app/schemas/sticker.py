"""TRACE Schemas for Sticker Garden Catalogue and Ownership."""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

StickerTheme = Literal["botanical", "creatures", "vintage", "humor", "cozy", "planner"]
StickerRarity = Literal["common", "uncommon", "rare", "legendary"]
StickerUnlockType = Literal["starter", "milestone", "streak", "manual"]
StickerOwnershipSource = Literal["daily_reward", "milestone_reward", "manual_grant"]


class StickerResponse(BaseModel):
    """Schema representing an individual sticker definition in the catalogue."""

    id: str = Field(..., description="Stable, unique identifier for the sticker.")
    name: str = Field(..., description="Display name of the sticker.")
    description: str = Field(..., description="Charming caption or flavor text.")
    theme: StickerTheme = Field(..., description="Theme grouping for the sticker.")
    rarity: StickerRarity = Field(..., description="Sticker rarity category.")
    asset_path: str = Field(..., description="Relative asset path for the transparent PNG artwork.")
    unlock_type: StickerUnlockType = Field(..., description="How this sticker is unlocked.")
    tags: List[str] = Field(default_factory=list, description="Searchable thematic tags.")
    milestone_requirement: Optional[Dict[str, Any]] = Field(
        None, description="Optional milestone requirement specification."
    )
    is_asset_available: bool = Field(
        False, description="Whether the transparent PNG artwork file exists on disk."
    )


class StickerPackResponse(BaseModel):
    """Schema representing a reward sticker pack definition."""

    id: str = Field(..., description="Stable, unique identifier for the sticker pack.")
    name: str = Field(..., description="Display name of the sticker pack.")
    description: str = Field(..., description="Flavor text explaining the pack's theme.")
    milestone_requirement: Dict[str, Any] = Field(
        ..., description="Requirement needed to earn this pack."
    )
    sticker_ids: List[str] = Field(
        ..., description="List of valid sticker IDs contained in this pack."
    )


class StickerOwnershipResponse(BaseModel):
    """Schema representing a persistent ownership record for an unlocked sticker."""

    id: str = Field(..., description="Stable identifier for the ownership record.")
    sticker_id: str = Field(..., description="Catalogue ID of the unlocked sticker.")
    unlocked_at: str = Field(..., description="ISO 8601 timestamp when the sticker was earned.")
    unlock_reason: str = Field(..., description="Human-readable reason for unlocking.")
    source: str = Field(..., description="Source of the unlock (e.g. daily_reward, milestone_reward, manual_grant).")


class OwnedStickerResponse(BaseModel):
    """Composite schema presenting both the ownership record and the sticker's catalogue metadata."""

    id: str = Field(..., description="Ownership record ID.")
    sticker_id: str = Field(..., description="Catalogue sticker ID.")
    unlocked_at: str = Field(..., description="ISO timestamp of unlock.")
    unlock_reason: str = Field(..., description="Why this sticker was awarded.")
    source: str = Field(..., description="Award source.")
    sticker: StickerResponse = Field(..., description="Full sticker metadata from the catalogue.")


class GrantStickerRequest(BaseModel):
    """Request payload for granting a sticker to the user's collection."""

    sticker_id: str = Field(..., min_length=1, description="Catalogue sticker ID to grant.")
    unlock_reason: str = Field(
        default="Granted to explorer collection",
        max_length=200,
        description="Reason for the unlock.",
    )
    source: StickerOwnershipSource = Field(
        default="manual_grant",
        description="Originating source of the reward.",
    )


class MilestoneProgress(BaseModel):
    """Progress status for a reward milestone."""

    id: str = Field(..., description="Milestone ID (e.g. milestone-7d)")
    name: str = Field(..., description="Display name of the milestone pack")
    streak_threshold: int = Field(..., description="Number of consecutive qualifying days required")
    pack_id: str = Field(..., description="Reward pack ID")
    is_achieved: bool = Field(..., description="Whether this milestone has been achieved and claimed")
    is_current: bool = Field(..., description="Whether this milestone is the next immediate target")
    is_locked: bool = Field(..., description="Whether this milestone remains locked")
    days_remaining: int = Field(..., description="Days needed to reach this milestone from current streak")
    claimed_at: Optional[str] = Field(None, description="ISO timestamp when achieved and claimed")


class StreakSummaryResponse(BaseModel):
    """Authoritative exploration streak and progress summary derived from persisted traces."""

    current_streak: int = Field(..., description="Current consecutive qualifying exploration days")
    longest_streak: int = Field(..., description="All-time longest streak in qualifying days")
    total_qualifying_days: int = Field(..., description="Total unique calendar days with at least one saved trace")
    today_qualified: bool = Field(..., description="Whether at least one trace has been saved on today's calendar date")
    today_reward_claimed: bool = Field(..., description="Whether today's daily sticker reward has already been claimed")
    today_reward_available: bool = Field(..., description="Whether a new daily sticker is available to earn today")
    today_reward_reason: Optional[str] = Field(None, description="Status message regarding today's reward availability")
    next_milestone_days: Optional[int] = Field(None, description="Target streak length for next milestone")
    days_to_next_milestone: Optional[int] = Field(None, description="Qualifying days remaining until next milestone")
    total_stickers_owned: int = Field(..., description="Total unique stickers currently owned")
    milestones: List[MilestoneProgress] = Field(default_factory=list, description="Milestone tracks and achievement status")


class StreakEvaluationResult(BaseModel):
    """Result of an evaluation of rewards following a trace save."""

    daily_sticker_awarded: Optional[OwnedStickerResponse] = None
    milestones_unlocked: List[StickerPackResponse] = Field(default_factory=list)
    streak_summary: StreakSummaryResponse
    streak_extended: bool = Field(
        default=False,
        description="Whether this evaluation extended or started today's exploration streak on a qualifying day.",
    )

