from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(from_attributes=True)
