"""TRACE API Root Router Package."""
from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.ai import router as ai_router
from app.api.routes.traces import router as traces_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(traces_router, prefix="/traces", tags=["traces"])

__all__ = ["api_router"]
