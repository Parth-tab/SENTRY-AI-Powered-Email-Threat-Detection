import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.db.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class EmailRecord(Base):
    __tablename__ = "email_records"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    message_id = Column(String(255), index=True, nullable=True)
    subject = Column(String(500), index=True, nullable=False, default="(No Subject)")
    sender = Column(String(255), index=True, nullable=False)
    sender_domain = Column(String(255), index=True, nullable=True)
    recipient = Column(String(255), index=True, nullable=True)
    date = Column(DateTime, nullable=True)
    raw_content = Column(Text, nullable=True)
    raw_content_path = Column(String(500), nullable=True)
    raw_headers = Column(JSON, nullable=True)
    sha256_hash = Column(String(64), index=True, nullable=False)
    source = Column(String(50), default="eml_upload") # eml_upload, imap, api, webhook
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="processed") # pending, processing, processed, error

    # Relationships
    analysis = relationship("AnalysisResult", back_populates="email", uselist=False, cascade="all, delete-orphan")
    evidence = relationship("EvidenceVault", back_populates="email", uselist=False, cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="email", cascade="all, delete-orphan")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    email_id = Column(String(36), ForeignKey("email_records.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    overall_threat_score = Column(Float, nullable=False, default=0.0)
    threat_level = Column(String(20), nullable=False, default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    
    # Classification
    primary_classification = Column(String(50), nullable=False, default="legitimate") # phishing, bec, impersonation, legitimate, suspicious
    classification_confidence = Column(Float, nullable=False, default=0.0)
    model_contributions = Column(JSON, nullable=True)
    
    # Authentication & Forensics
    auth_spf = Column(JSON, nullable=True)
    auth_dkim = Column(JSON, nullable=True)
    auth_dmarc = Column(JSON, nullable=True)
    header_anomalies = Column(JSON, nullable=True)
    relay_hops_count = Column(Integer, default=0)
    relay_path = Column(JSON, nullable=True)
    earliest_reliable_hop = Column(JSON, nullable=True)
    
    # Content & Domain & Geo Intel
    content_analysis = Column(JSON, nullable=True)
    domain_intel = Column(JSON, nullable=True)
    origin_assessment = Column(JSON, nullable=True)
    attribution_assessment = Column(JSON, nullable=True)
    threat_intel_matches = Column(JSON, nullable=True)
    
    # Actionable guidance
    recommendations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    email = relationship("EmailRecord", back_populates="analysis")

class EvidenceVault(Base):
    __tablename__ = "evidence_vault"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    email_id = Column(String(36), ForeignKey("email_records.id", ondelete="CASCADE"), unique=True, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    stored_path = Column(String(500), nullable=False)
    chain_of_custody_id = Column(String(50), nullable=False, index=True)
    chain_entries = Column(JSON, nullable=False) # List of RFC 3227 compliant audit steps
    last_entry_hash = Column(String(64), nullable=False)
    is_sealed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    email = relationship("EmailRecord", back_populates="evidence")

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String(50), primary_key=True, index=True) # e.g. CMP-2024-0034
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    threat_level = Column(String(20), default="HIGH")
    actor_sophistication = Column(String(50), default="medium")
    infrastructure_cluster = Column(JSON, nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    total_emails = Column(Integer, default=1)
    iocs = Column(JSON, nullable=True)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    email_id = Column(String(36), ForeignKey("email_records.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    threat_score = Column(Float, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    email = relationship("EmailRecord", back_populates="alerts")

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="analyst") # admin, analyst, investigator
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
