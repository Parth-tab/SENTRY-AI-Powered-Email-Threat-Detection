from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

class CampaignBase(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    threat_level: str = "HIGH"
    actor_sophistication: str = "medium"

class CampaignResponse(CampaignBase):
    infrastructure_cluster: Optional[Dict[str, Any]] = None
    first_seen: datetime
    last_seen: datetime
    total_emails: int
    iocs: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class ChainEntry(BaseModel):
    step_number: int
    action: str
    actor: str
    timestamp: str
    details: str
    code_version: str
    prev_hash: str
    entry_hash: str

class EvidenceResponse(BaseModel):
    id: str
    email_id: str
    sha256_hash: str
    stored_path: str
    chain_of_custody_id: str
    chain_entries: List[Dict[str, Any]]
    last_entry_hash: str
    is_sealed: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardStatsResponse(BaseModel):
    total_emails_analyzed: int
    threat_distribution: Dict[str, int]
    classification_breakdown: Dict[str, int]
    active_campaigns_count: int
    top_origin_countries: List[Dict[str, Any]]
    avg_threat_score: float
    recent_alerts: List[Dict[str, Any]]
