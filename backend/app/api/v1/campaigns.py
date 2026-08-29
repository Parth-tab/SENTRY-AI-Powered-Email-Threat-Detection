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
async def get_global_network_graph(db: AsyncSession = Depends(get_db)):
    """Returns the full multi-entity knowledge graph for campaign visualization."""
    if CorrelationEngine._graph.number_of_nodes() <= 30:
        from sqlalchemy import select
        from app.db.models import EmailRecord, AnalysisResult
        stmt = select(EmailRecord, AnalysisResult).outerjoin(AnalysisResult, EmailRecord.id == AnalysisResult.email_id).limit(1000)
        res = await db.execute(stmt)
        rows = res.all()
        if len(rows) > 30:
            for email_rec, analysis_rec in rows:
                CorrelationEngine.add_email_to_graph(
                    email_id=email_rec.id,
                    email_data={
                        "subject": email_rec.subject,
                        "sender": email_rec.sender,
                        "sender_domain": email_rec.sender_domain
                    },
                    analysis_data={
                        "overall_threat_score": analysis_rec.overall_threat_score if analysis_rec else 0.0,
                        "threat_level": analysis_rec.threat_level if analysis_rec else "LOW",
                        "origin_assessment": analysis_rec.origin_assessment if analysis_rec else {},
                        "attribution_assessment": analysis_rec.attribution_assessment if analysis_rec else {},
                        "domain_intel": analysis_rec.domain_intel if analysis_rec else {}
                    }
                )
    return CorrelationEngine.get_graph_data()
