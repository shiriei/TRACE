from datetime import datetime, timezone
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Structured health response for TRACE backend."""

    status: str = Field(default="healthy", description="Operational health status")
    project: str = Field(default="TRACE", description="Project identity")
    version: str = Field(default="0.1.0", description="Semantic service version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the probe",
    )
    environment: str = Field(default="development", description="Current execution environment")
