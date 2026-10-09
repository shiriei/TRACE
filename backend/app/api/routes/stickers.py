"""TRACE Sticker Garden API Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.sticker import (
    GrantStickerRequest,
    OwnedStickerResponse,
    StickerPackResponse,
    StickerResponse,
    StreakEvaluationResult,
    StreakSummaryResponse,
)
from app.services.sticker_service import (
    StickerAlreadyOwnedError,
    StickerNotFoundError,
    StickerService,
    get_sticker_service,
)

logger = logging.getLogger("trace.api.stickers")

router = APIRouter()


@router.get(
    "",
    response_model=List[StickerResponse],
    summary="Retrieve sticker catalogue",
    description="Returns all available stickers in the catalogue, with optional theme filter.",
)
async def list_stickers(
    theme: Optional[str] = Query(default=None, description="Filter by theme (botanical, creatures, etc.)"),
    service: StickerService = Depends(get_sticker_service),
):
    """List stickers from the catalogue."""
    return service.get_catalogue(theme=theme)


@router.get(
    "/packs",
    response_model=List[StickerPackResponse],
    summary="Retrieve reward sticker packs",
    description="Returns all defined reward sticker packs and their metadata.",
)
async def list_packs(
    service: StickerService = Depends(get_sticker_service),
):
    """List reward pack definitions."""
    return service.get_packs()


@router.get(
    "/collection",
    response_model=List[OwnedStickerResponse],
    summary="Retrieve user sticker collection",
    description="Returns all stickers earned and owned by the explorer, ordered by unlock time.",
)
async def get_user_collection(
    service: StickerService = Depends(get_sticker_service),
):
    """List earned sticker collection."""
    return service.get_user_collection()


@router.post(
    "/collection/grant",
    response_model=OwnedStickerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant a sticker to user collection",
    description="Grants ownership of a catalogue sticker. Fails if unknown or already owned.",
)
async def grant_sticker(
    payload: GrantStickerRequest,
    service: StickerService = Depends(get_sticker_service),
):
    """Grant a sticker to user collection."""
    try:
        return service.grant_sticker(
            sticker_id=payload.sticker_id,
            unlock_reason=payload.unlock_reason,
            source=payload.source,
        )
    except StickerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except StickerAlreadyOwnedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/streak",
    response_model=StreakSummaryResponse,
    summary="Retrieve exploration streak summary",
    description="Returns current streak, longest streak, qualifying status, and milestone progression derived from traces.",
)
async def get_streak_summary(
    tz_offset_minutes: Optional[int] = Query(default=None, description="Timezone offset in minutes (JS getTimezoneOffset())"),
    tz_name: Optional[str] = Query(default=None, description="Timezone name or offset string"),
    service: StickerService = Depends(get_sticker_service),
):
    """Retrieve exploration streak and milestone progress."""
    return service.get_streak_summary(tz_offset_minutes=tz_offset_minutes, tz_name=tz_name)


@router.post(
    "/streak/evaluate",
    response_model=StreakEvaluationResult,
    summary="Evaluate exploration rewards and streak",
    description="Evaluates streak progression, unlocks eligible milestone packs, and awards daily sticker if eligible.",
)
async def evaluate_streak_rewards(
    tz_offset_minutes: Optional[int] = Query(default=None, description="Timezone offset in minutes (JS getTimezoneOffset())"),
    tz_name: Optional[str] = Query(default=None, description="Timezone name or offset string"),
    service: StickerService = Depends(get_sticker_service),
):
    """Evaluate and claim eligible exploration rewards."""
    return service.evaluate_rewards(tz_offset_minutes=tz_offset_minutes, tz_name=tz_name)


@router.get(
    "/{sticker_id}",
    response_model=StickerResponse,
    summary="Retrieve a specific sticker definition",
    description="Returns metadata for a single sticker by its stable catalogue ID.",
)
async def get_sticker(
    sticker_id: str,
    service: StickerService = Depends(get_sticker_service),
):
    """Get single sticker definition."""
    try:
        return service.get_sticker(sticker_id)
    except StickerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
