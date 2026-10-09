"""TRACE Sticker Garden Catalogue — Single Source of Truth.

Contains typed definitions for starter stickers and reward packs.
Adheres strictly to the TRACE aesthetic:
Cute is the aesthetic. Exploration is the purpose. Stickers are the reward.
"""
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Optional

from app.models.sticker import StickerDefinition, StickerPackDefinition

# Helper to verify whether transparent PNG asset currently exists on disk
def _is_asset_present(asset_rel_path: str) -> bool:
    """Check if the PNG asset file exists in frontend or backend public directory."""
    # Check possible asset locations without failing
    base_paths = [
        Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "public",
        Path(__file__).resolve().parent.parent.parent / "storage" / "stickers",
    ]
    for base in base_paths:
        candidate = base / asset_rel_path
        if candidate.exists() and candidate.is_file():
            return True
    return False


STARTER_STICKERS: List[StickerDefinition] = [
    # --- Theme: Botanical & Nature ---
    StickerDefinition(
        id="sticker-sprout-alive",
        name="Tiny Sprout",
        description="Look at me, being alive and stuff.",
        theme="botanical",
        rarity="common",
        asset_path="assets/stickers/botanical-sprout-alive.png",
        unlock_type="starter",
        tags=["sprout", "botanical", "seedling", "alive", "spring", "growth"],
        is_asset_available=_is_asset_present("assets/stickers/botanical-sprout-alive.png"),
    ),
    StickerDefinition(
        id="sticker-rock-lichen",
        name="Rock Lichen",
        description="Taking things slow on a warm rock.",
        theme="botanical",
        rarity="common",
        asset_path="assets/stickers/botanical-rock-lichen.png",
        unlock_type="starter",
        tags=["lichen", "rock", "stone", "slow", "botanical", "nature"],
        is_asset_available=_is_asset_present("assets/stickers/botanical-rock-lichen.png"),
    ),
    StickerDefinition(
        id="sticker-pinecone-archive",
        name="Architectural Pinecone",
        description="Nature's geometric masterpiece resting quietly on the path.",
        theme="botanical",
        rarity="rare",
        asset_path="assets/stickers/botanical-pinecone-archive.png",
        unlock_type="starter",
        tags=["pinecone", "conifer", "geometry", "forest", "nature", "botanical"],
        is_asset_available=_is_asset_present("assets/stickers/botanical-pinecone-archive.png"),
    ),

    # --- Theme: Cute Little Creatures ---
    StickerDefinition(
        id="sticker-snail-schedule",
        name="Unscheduled Snail",
        description="Outside. Against my usual schedule.",
        theme="creatures",
        rarity="common",
        asset_path="assets/stickers/creature-unscheduled-snail.png",
        unlock_type="starter",
        tags=["snail", "shell", "slow", "schedule", "outside", "creature"],
        is_asset_available=_is_asset_present("assets/stickers/creature-unscheduled-snail.png"),
    ),
    StickerDefinition(
        id="sticker-leaf-watching-frog",
        name="Leaf-Watching Frog",
        description="Observing this particular leaf with utmost seriousness.",
        theme="creatures",
        rarity="uncommon",
        asset_path="assets/stickers/creature-leaf-watching-frog.png",
        unlock_type="starter",
        tags=["frog", "amphibian", "leaf", "curious", "pond", "creature"],
        is_asset_available=_is_asset_present("assets/stickers/creature-leaf-watching-frog.png"),
    ),
    StickerDefinition(
        id="sticker-crosswalk-caterpillar",
        name="Crosswalk Caterpillar",
        description="Crossing the pavement on high-priority insect business.",
        theme="creatures",
        rarity="uncommon",
        asset_path="assets/stickers/creature-crosswalk-caterpillar.png",
        unlock_type="starter",
        tags=["caterpillar", "bug", "transit", "crossing", "critter", "creature"],
        is_asset_available=_is_asset_present("assets/stickers/creature-crosswalk-caterpillar.png"),
    ),

    # --- Theme: Vintage Journaling & Postage ---
    StickerDefinition(
        id="sticker-field-stamp",
        name="Field Note Stamp",
        description="Certified observation noted with slow curiosity and dark ink.",
        theme="vintage",
        rarity="common",
        asset_path="assets/stickers/vintage-field-stamp.png",
        unlock_type="starter",
        tags=["stamp", "postal", "vintage", "journal", "ink", "field-note"],
        is_asset_available=_is_asset_present("assets/stickers/vintage-field-stamp.png"),
    ),
    StickerDefinition(
        id="sticker-pressed-fern",
        name="Pressed Botanical Specimen",
        description="A delicate frond preserved between the pages of an old field journal.",
        theme="vintage",
        rarity="uncommon",
        asset_path="assets/stickers/vintage-pressed-fern.png",
        unlock_type="starter",
        tags=["fern", "herbarium", "botany", "paper", "vintage", "specimen"],
        is_asset_available=_is_asset_present("assets/stickers/vintage-pressed-fern.png"),
    ),

    # --- Theme: Funny & Sarcastic ---
    StickerDefinition(
        id="sticker-touched-grass",
        name="Grass Toucher",
        description="I touched grass. Literally. It was slightly damp.",
        theme="humor",
        rarity="common",
        asset_path="assets/stickers/humor-touched-grass.png",
        unlock_type="starter",
        tags=["grass", "outside", "sarcastic", "walk", "verified", "humor"],
        is_asset_available=_is_asset_present("assets/stickers/humor-touched-grass.png"),
    ),
    StickerDefinition(
        id="sticker-indoorsy-explorer",
        name="Indoorsy Explorer",
        description="I stepped out into the weather today. Remember my sacrifice.",
        theme="humor",
        rarity="uncommon",
        asset_path="assets/stickers/humor-indoorsy-explorer.png",
        unlock_type="starter",
        tags=["humor", "indoorsy", "fresh-air", "brave", "walk", "weather"],
        is_asset_available=_is_asset_present("assets/stickers/humor-indoorsy-explorer.png"),
    ),

    # --- Theme: Cozy & Wholesome ---
    StickerDefinition(
        id="sticker-napping-cloud",
        name="Napping Cloud",
        description="A sleepy cloud taking a low drift for a brief recharge.",
        theme="cozy",
        rarity="common",
        asset_path="assets/stickers/cozy-napping-cloud.png",
        unlock_type="starter",
        tags=["cloud", "sky", "nap", "cozy", "soft", "rest"],
        is_asset_available=_is_asset_present("assets/stickers/cozy-napping-cloud.png"),
    ),
    StickerDefinition(
        id="sticker-trail-thermos",
        name="Trail Thermos",
        description="Warm steam in cool morning air makes any road friendlier.",
        theme="cozy",
        rarity="common",
        asset_path="assets/stickers/cozy-trail-thermos.png",
        unlock_type="starter",
        tags=["tea", "thermos", "walk", "warm", "cozy", "morning"],
        is_asset_available=_is_asset_present("assets/stickers/cozy-trail-thermos.png"),
    ),
    StickerDefinition(
        id="sticker-pocket-pebble",
        name="Lucky Pocket Pebble",
        description="Smooth river stone pocketed for no particular reason.",
        theme="cozy",
        rarity="common",
        asset_path="assets/stickers/cozy-pocket-pebble.png",
        unlock_type="starter",
        tags=["pebble", "stone", "treasure", "pocket", "keepsake", "cozy"],
        is_asset_available=_is_asset_present("assets/stickers/cozy-pocket-pebble.png"),
    ),

    # --- Theme: Functional Planner Stickers ---
    StickerDefinition(
        id="sticker-found-flag",
        name="Found Something Flag",
        description="Little ribbon flag marking an unrepeatable micro-discovery.",
        theme="planner",
        rarity="common",
        asset_path="assets/stickers/planner-found-flag.png",
        unlock_type="starter",
        tags=["flag", "pin", "planner", "spot", "bookmark", "landmark"],
        is_asset_available=_is_asset_present("assets/stickers/planner-found-flag.png"),
    ),
    StickerDefinition(
        id="sticker-wanderer-tab",
        name="Wanderer Index Tab",
        description="Off course, having a lovely time, completely on schedule.",
        theme="planner",
        rarity="uncommon",
        asset_path="assets/stickers/planner-wanderer-tab.png",
        unlock_type="starter",
        tags=["compass", "tab", "planner", "direction", "wander", "index"],
        is_asset_available=_is_asset_present("assets/stickers/planner-wanderer-tab.png"),
    ),
]

_STICKER_MAP: Dict[str, StickerDefinition] = {s.id: s for s in STARTER_STICKERS}


REWARD_PACKS: List[StickerPackDefinition] = [
    StickerPackDefinition(
        id="pack-little-things-7d",
        name="The Little Things Club",
        description="For noticing the small, humble moments hiding in plain sight.",
        milestone_requirement={"type": "streak_days", "threshold": 7},
        sticker_ids=[
            "sticker-sprout-alive",
            "sticker-pocket-pebble",
            "sticker-found-flag",
        ],
    ),
    StickerPackDefinition(
        id="pack-field-journal-30d",
        name="The Field Journal Collection",
        description="A celebration of keeping slow, attentive field notes through four whole weeks.",
        milestone_requirement={"type": "streak_days", "threshold": 30},
        sticker_ids=[
            "sticker-field-stamp",
            "sticker-pressed-fern",
            "sticker-wanderer-tab",
        ],
    ),
    StickerPackDefinition(
        id="pack-outside-ish-50d",
        name="The Outside-ish Personality Pack",
        description="Proof that stepping into the open air is becoming a distinct personal trait.",
        milestone_requirement={"type": "streak_days", "threshold": 50},
        sticker_ids=[
            "sticker-snail-schedule",
            "sticker-touched-grass",
            "sticker-indoorsy-explorer",
        ],
    ),
    StickerPackDefinition(
        id="pack-world-noticed-100d",
        name="The World Noticed Collection",
        description="One hundred days of walking with an open eye for the living world.",
        milestone_requirement={"type": "streak_days", "threshold": 100},
        sticker_ids=[
            "sticker-leaf-watching-frog",
            "sticker-crosswalk-caterpillar",
            "sticker-pinecone-archive",
            "sticker-napping-cloud",
        ],
    ),
]

_PACK_MAP: Dict[str, StickerPackDefinition] = {p.id: p for p in REWARD_PACKS}


def get_all_stickers() -> List[StickerDefinition]:
    """Retrieve all stickers defined in the catalogue, dynamically verifying on-disk asset presence."""
    return [
        replace(s, is_asset_available=_is_asset_present(s.asset_path))
        for s in STARTER_STICKERS
    ]


def get_sticker_by_id(sticker_id: str) -> Optional[StickerDefinition]:
    """Retrieve a single sticker definition by its unique stable ID, dynamically verifying asset presence."""
    s = _STICKER_MAP.get(sticker_id)
    if s:
        return replace(s, is_asset_available=_is_asset_present(s.asset_path))
    return None


def get_all_packs() -> List[StickerPackDefinition]:
    """Retrieve all reward pack definitions."""
    return list(REWARD_PACKS)


def get_pack_by_id(pack_id: str) -> Optional[StickerPackDefinition]:
    """Retrieve a single pack definition by its unique stable ID."""
    return _PACK_MAP.get(pack_id)
