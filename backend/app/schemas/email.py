from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class EmailBase(BaseModel):
    subject: str = "(No Subject)"
    sender: str
    sender_domain: Optional[str] = None
    recipient: Optional[str] = None
    date: Optional[datetime] = None
    source: str = "eml_upload"

class EmailCreate(EmailBase):
    raw_content: str
    message_id: Optional[str] = None

class EmailResponse(EmailBase):
    id: str
    message_id: Optional[str] = None
    sha256_hash: str
    ingested_at: datetime
    status: str
    raw_headers: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class EmailDetailResponse(EmailResponse):
    raw_content: Optional[str] = None
    analysis: Optional[Any] = None
    evidence: Optional[Any] = None
