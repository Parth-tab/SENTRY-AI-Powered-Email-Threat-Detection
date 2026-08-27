from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import EvidenceVault
from app.services.reporting import ReportingService

router = APIRouter(prefix="/evidence", tags=["Evidence"])

@router.get("/{email_id}", response_model=Dict[str, Any])
async def get_evidence(email_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves immutable evidence record and RFC 3227 chain of custody log."""
    stmt = select(EvidenceVault).where(EvidenceVault.email_id == email_id)
    res = await db.execute(stmt)
    evidence = res.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence vault record not found.")

    return {
        "id": evidence.id,
        "email_id": evidence.email_id,
        "sha256_hash": evidence.sha256_hash,
        "stored_path": evidence.stored_path,
        "chain_of_custody_id": evidence.chain_of_custody_id,
        "chain_entries": evidence.chain_entries,
        "last_entry_hash": evidence.last_entry_hash,
        "is_sealed": evidence.is_sealed,
        "created_at": evidence.created_at
    }

@router.post("/verify/{email_id}", response_model=Dict[str, Any])
async def verify_chain(email_id: str, db: AsyncSession = Depends(get_db)):
    """
    Cryptographically verifies the RFC 3227 hash chain for an email to guarantee
    evidentiary integrity and detect any tampering.
    """
    stmt = select(EvidenceVault).where(EvidenceVault.email_id == email_id)
    res = await db.execute(stmt)
    evidence = res.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence vault record not found.")

    is_valid, verification_msg = ReportingService.verify_chain_integrity(evidence.chain_entries)

    return {
        "email_id": email_id,
        "chain_of_custody_id": evidence.chain_of_custody_id,
        "is_valid": is_valid,
        "verification_message": verification_msg,
        "total_steps_verified": len(evidence.chain_entries),
        "root_genesis_hash": evidence.chain_entries[0]["entry_hash"] if evidence.chain_entries else None,
        "sealed_head_hash": evidence.last_entry_hash
    }
