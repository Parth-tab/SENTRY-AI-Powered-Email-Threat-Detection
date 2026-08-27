from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

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
