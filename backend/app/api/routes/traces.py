"""TRACE Traces API Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.schemas import TraceCategory
from app.schemas.trace import (
    TraceCreate,
    TraceDeleteResponse,
    TraceResponse,
)
from app.services.trace_service import TraceService, get_trace_service

logger = logging.getLogger("trace.api.traces")

router = APIRouter()


@router.post(
    "",
    response_model=TraceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new physical trace observation",
    description="Persists a new trace, invokes local AI for interpretation, and stores categorized discovery.",
)
async def create_trace(
    data: TraceCreate,
    service: TraceService = Depends(get_trace_service),
):
    """Create a new trace observation."""
    return await service.create_trace(data)


@router.get(
    "",
    response_model=List[TraceResponse],
    summary="Retrieve recorded traces",
    description="Returns all recorded traces ordered by creation time descending.",
)
async def list_traces(
    limit: int = Query(default=100, ge=1, le=500, description="Max traces to return"),
    offset: int = Query(default=0, ge=0, description="Number of traces to skip"),
    category: Optional[TraceCategory] = Query(default=None, description="Filter by category"),
    service: TraceService = Depends(get_trace_service),
):
    """List traces with optional category filtering."""
    return service.list_traces(limit=limit, offset=offset, category=category)


@router.get(
    "/{trace_id}",
    response_model=TraceResponse,
    summary="Retrieve a single trace by ID",
    description="Returns details of a single trace.",
)
async def get_trace(
    trace_id: str,
    service: TraceService = Depends(get_trace_service),
):
    """Get a trace by ID."""
    trace = service.get_trace(trace_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace '{trace_id}' not found",
        )
    return trace


@router.delete(
    "/{trace_id}",
    response_model=TraceDeleteResponse,
    summary="Delete a trace by ID",
    description="Permanently removes a trace from the local database.",
)
async def delete_trace(
    trace_id: str,
    service: TraceService = Depends(get_trace_service),
):
    """Delete a trace by ID."""
    deleted = service.delete_trace(trace_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace '{trace_id}' not found",
        )
    return TraceDeleteResponse(
        message="Trace deleted successfully",
        id=trace_id,
    )
