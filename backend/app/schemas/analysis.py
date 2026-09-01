from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class SPFResult(BaseModel):
    result: str # pass, fail, softfail, neutral, none
    detail: str
    sender_ip: Optional[str] = None
    domain: Optional[str] = None

class DKIMResult(BaseModel):
    result: str # pass, fail, none, invalid
    detail: str
    selector: Optional[str] = None
    domain: Optional[str] = None

class DMARCResult(BaseModel):
    result: str # pass, fail, none
    policy: str # none, quarantine, reject
    alignment: str # pass, fail
    detail: str

class EarliestHop(BaseModel):
    ip: str
    hostname: Optional[str] = None
    by_host: Optional[str] = None
    protocol: Optional[str] = None
    timestamp: Optional[str] = None
    is_private: bool = False

class GeolocationInfo(BaseModel):
    ip: str
    country: str
    country_code: str
    city: str
    latitude: float
    longitude: float
    isp: str
    asn: str
    connection_type: str = "Corporate/Broadband"

class AnonymizationFlags(BaseModel):
    tor_exit_node: bool = False
    vpn_detected: bool = False
    hosting_provider: bool = False
    open_relay: bool = False
    risk_summary: str = "Clean"

class OriginAssessment(BaseModel):
    probable_origin_ip: str
    geolocation: GeolocationInfo
    anonymization: AnonymizationFlags
    confidence: float
    confidence_factors: List[str] = []

class InfrastructureCluster(BaseModel):
    name: str
    provider: str
    first_seen: str
    email_count: int = 1

class AttributionAssessment(BaseModel):
    campaign_id: Optional[str] = None
    campaign_confidence: float = 0.0
    related_emails: int = 0
    infrastructure_cluster: Optional[InfrastructureCluster] = None
    actor_sophistication: str = "low"
    assessment: str

class AnalysisResultResponse(BaseModel):
    id: str
    email_id: str
    overall_threat_score: float
    threat_level: str # LOW, MEDIUM, HIGH, CRITICAL
    primary_classification: str
    classification_subtype: Optional[str] = None
    classification_confidence: float
    model_contributions: Dict[str, float]
    
    auth_spf: Optional[Dict[str, Any]] = None
    auth_dkim: Optional[Dict[str, Any]] = None
    auth_dmarc: Optional[Dict[str, Any]] = None
    header_anomalies: List[str] = []
    relay_hops_count: int = 0
    relay_path: List[Dict[str, Any]] = []
    earliest_reliable_hop: Optional[Dict[str, Any]] = None
    
    content_analysis: Optional[Dict[str, Any]] = None
    domain_intel: Optional[Dict[str, Any]] = None
    origin_assessment: Optional[Dict[str, Any]] = None
    attribution_assessment: Optional[Dict[str, Any]] = None
    threat_intel_matches: Optional[Dict[str, Any]] = None
    recommendations: List[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
