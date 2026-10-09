"""TRACE Domain and Persistence Model for Traces."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TraceModel:
    """Domain model representing a persistent physical Trace entity."""

    id: str
    observation: str
    category: str
    title: str
    summary: str
    tags: List[str] = field(default_factory=list)
    sensory_type: str = "visual"
    confidence: float = 0.0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_mode: str = "unplaced"
    created_at: str = ""
    photo_path: Optional[str] = None
    audio_path: Optional[str] = None
    reward: Optional[object] = None
