from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.correlation_engine import CorrelationEngine
from app.schemas.campaign import CampaignResponse

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_campaigns():
    """Lists all active correlated threat campaigns and infrastructure clusters."""
    return CorrelationEngine.list_campaigns()

@router.get("/{campaign_id}", response_model=Dict[str, Any])
async def get_campaign(campaign_id: str):
    """Retrieves specific campaign profile, actor sophistication, and attribution evidence."""
    campaign = CorrelationEngine.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign identifier not found.")
    return campaign

@router.get("/graph/all")
async def get_global_network_graph():
    """Returns the full multi-entity knowledge graph for campaign visualization."""
    return CorrelationEngine.get_graph_data()
