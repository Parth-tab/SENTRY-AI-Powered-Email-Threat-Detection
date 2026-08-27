from fastapi import APIRouter
from app.api.v1.emails import router as emails_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.stats import router as stats_router
from app.api.v1.websocket import router as ws_router
from app.api.v1.model import router as model_router

api_router = APIRouter()

api_router.include_router(emails_router)
api_router.include_router(campaigns_router)
api_router.include_router(evidence_router)
api_router.include_router(stats_router)
api_router.include_router(ws_router)
api_router.include_router(model_router)
