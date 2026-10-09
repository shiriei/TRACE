"""TRACE API Root Router Package."""
from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.ai import router as ai_router
from app.api.routes.traces import router as traces_router
from app.api.routes.attachments import router as attachments_router
from app.api.routes.stickers import router as stickers_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(traces_router, prefix="/traces", tags=["traces"])
api_router.include_router(attachments_router, prefix="/traces", tags=["attachments"])
api_router.include_router(stickers_router, prefix="/stickers", tags=["stickers"])

__all__ = ["api_router"]

