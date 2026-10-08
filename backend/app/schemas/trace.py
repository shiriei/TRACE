"""TRACE Pydantic Schemas for Trace API Payloads and Responses."""
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.ai.schemas import SensoryType, TraceCategory

LocationMode = Literal["gps", "manual", "unplaced"]


class TraceCreate(BaseModel):
    """Input payload for capturing a new real-world trace."""

    observation: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Raw observation text describing what the user noticed outside.",
        examples=["Wild mint growing beside a broken stone fountain."],
    )
    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Geographic latitude coordinate (-90.0 to 90.0), or None for unplaced.",
        examples=[37.7749],
    )
    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Geographic longitude coordinate (-180.0 to 180.0), or None for unplaced.",
        examples=[-122.4194],
    )
    location_mode: Optional[LocationMode] = Field(
        default=None,
        description="Method used for placement: 'gps', 'manual', or 'unplaced'.",
    )
    category: Optional[TraceCategory] = Field(
        default=None,
        description="Optional explicit category override.",
    )
    title: Optional[str] = Field(
        default=None,
        max_length=120,
        description="Optional explicit title override.",
    )
    summary: Optional[str] = Field(
        default=None,
        max_length=400,
        description="Optional explicit summary override.",
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Optional list of custom tags.",
    )
    sensory_type: Optional[SensoryType] = Field(
        default=None,
        description="Optional explicit sensory modality override.",
    )
    photo_path: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional local filesystem path to associated photo.",
    )
    audio_path: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional local filesystem path to associated audio recording.",
    )

    @field_validator("observation")
    @classmethod
    def clean_observation(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Observation cannot be empty or whitespace only.")
        return trimmed

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, tags: Optional[List[str]]) -> Optional[List[str]]:
        if tags is None:
            return None
        cleaned: List[str] = []
        for t in tags:
            s = t.strip().lstrip("#").lower()
            if s and s not in cleaned:
                cleaned.append(s)
        return cleaned

    @model_validator(mode="after")
    def validate_location_consistency(self) -> "TraceCreate":
        """Enforce strict consistency between coordinates and location_mode."""
        if self.location_mode is None:
            if self.latitude is not None and self.longitude is not None:
                self.location_mode = "manual"
            elif self.latitude is None and self.longitude is None:
                self.location_mode = "unplaced"
            else:
                raise ValueError("Both latitude and longitude must be provided together.")
        elif self.location_mode == "unplaced":
            if self.latitude is not None or self.longitude is not None:
                raise ValueError("Unplaced traces cannot have latitude or longitude coordinates.")
        elif self.location_mode in ("gps", "manual"):
            if self.latitude is None or self.longitude is None:
                raise ValueError(
                    f"Latitude and longitude are required when location_mode is '{self.location_mode}'."
                )
        return self


class TraceResponse(BaseModel):
    """Structured response representation of a persistent trace."""

    id: str = Field(..., description="Unique trace identifier.")
    observation: str = Field(..., description="Original user observation.")
    category: TraceCategory = Field(..., description="Categorized TRACE theme.")
    title: str = Field(..., description="Human-readable title.")
    summary: str = Field(..., description="Structured summary.")
    tags: List[str] = Field(default_factory=list, description="Descriptive tags.")
    sensory_type: SensoryType = Field(..., description="Dominant sensory modality.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score.")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0, description="Latitude coordinate, if placed.")
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0, description="Longitude coordinate, if placed.")
    location_mode: LocationMode = Field(default="unplaced", description="Placement method: gps, manual, or unplaced.")
    created_at: str = Field(..., description="ISO 8601 creation timestamp.")
    photo_path: Optional[str] = Field(default=None, description="Path to local photo, if any.")
    audio_path: Optional[str] = Field(default=None, description="Path to local audio, if any.")

    model_config = ConfigDict(from_attributes=True)


class TraceDeleteResponse(BaseModel):
    """Response returned upon trace deletion."""

    message: str = Field(..., description="Confirmation message.")
    id: str = Field(..., description="Identifier of the deleted trace.")
