"""TRACE AI Pydantic Schemas and Domain Models."""
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator

# Exactly the five fundamental TRACE categories
TraceCategory = Literal[
    "Nature",
    "Sound",
    "Structure",
    "Mystery",
    "Personal",
]

# Controlled sensory modalities
SensoryType = Literal[
    "visual",
    "auditory",
    "environmental",
    "textual",
    "personal",
    "mixed",
]


class TraceInterpretRequest(BaseModel):
    """Input payload for interpreting a real-world observation."""

    observation: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Raw observation text describing what the user noticed outside.",
        examples=["Green moss is growing between old bricks beside a drain."],
    )

    @field_validator("observation")
    @classmethod
    def clean_observation(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Observation cannot be empty or whitespace only.")
        return trimmed


class TraceAIResult(BaseModel):
    """Structured AI interpretation of a user observation."""

    category: TraceCategory = Field(
        ...,
        description="Exactly one of the five TRACE categories: Nature, Sound, Structure, Mystery, Personal.",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Concise human-friendly title for the trace discovery.",
        examples=["Moss between the old bricks"],
    )
    summary: str = Field(
        ...,
        min_length=1,
        max_length=400,
        description="One or two concise sentences summarizing the observation.",
        examples=["Green moss is growing in the damp gap between the bricks beside the drain."],
    )
    tags: List[str] = Field(
        default_factory=list,
        description="List of concise, relevant lowercase tags.",
        examples=[["moss", "bricks", "drain"]],
    )
    sensory_type: SensoryType = Field(
        ...,
        description="Dominant sensory modality: visual, auditory, environmental, textual, personal, mixed.",
        examples=["visual"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score between 0.0 and 1.0.",
        examples=[0.95],
    )

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, tags: List[str]) -> List[str]:
        cleaned = []
        for t in tags:
            s = t.strip().lstrip("#").lower()
            if s and s not in cleaned:
                cleaned.append(s)
        return cleaned


class AIStatusResponse(BaseModel):
    """Status probe response for the configured LM Studio local service."""

    available: bool = Field(..., description="Whether LM Studio endpoint is reachable.")
    provider: str = Field(default="lm-studio", description="Provider identifier.")
    model: str = Field(..., description="Configured local model identifier.")
