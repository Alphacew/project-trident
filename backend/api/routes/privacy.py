"""Project TRIDENT — Privacy Vault & Anti-Harassment API Routes (Screen 3).

Endpoints:
- GET /api/privacy/vault/status: Returns privacy vault status and custodian shares
- POST /api/privacy/vault/recombine: Executes Shamir 2-of-3 reveal ceremony
- GET /api/privacy/vault/audit-log: Returns complete hash-chained audit log
- POST /api/privacy/vault/verify-log: Mathematically verifies cryptographic hash chain
- POST /api/privacy/query/validate: Validates analyst search against anti-harassment safeguards
- GET /api/privacy/harassment/alerts: Returns active DPO repeat-subject compliance alerts
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from backend.api.manager import demo_manager
from backend.crypto.harassment_audit import HarassmentAlert, QueryValidationResult
from backend.crypto.shamir_vault import RevealReceipt

router = APIRouter(prefix="/api/privacy", tags=["Privacy"])


class UnmaskRequest(BaseModel):
    share_indices: List[int] = Field(..., description="Indices of participating custodian shares (e.g. [1, 2])")
    subject_token: str = Field(..., description="Pseudonymized token to unmask, e.g. Subject-Theta-482")
    justification: str = Field(..., description="Audited legal/compliance justification")
    auditor_token: str = Field(default="DPO-Audit-Session-101")


class QueryValidationRequest(BaseModel):
    query: str = Field(..., description="Target search query (e.g. Subject-Theta-482 or ANOM-841)")
    analyst_id: str = Field(default="SOC-Analyst-1", description="Identifier of investigating analyst")


@router.get("/vault/status")
def get_vault_status() -> Dict[str, Any]:
    """Returns privacy vault status, custodian shares, and hash-chain status for Screen 3."""
    return demo_manager.get_privacy_vault_status()


@router.post("/vault/recombine", response_model=RevealReceipt)
def recombine_shares(req: UnmaskRequest):
    """Executes Shamir 2-of-3 threshold unmasking ceremony and appends to hash-chained ledger."""
    try:
        receipt = demo_manager.reveal_identity(
            share_indices=req.share_indices,
            subject_token=req.subject_token,
            justification=req.justification,
            auditor_token=req.auditor_token,
        )
        return receipt
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/vault/audit-log", response_model=List[RevealReceipt])
def get_audit_log():
    """Returns complete hash-chained audit log of all identity reveal ceremonies."""
    return demo_manager.get_audit_log()


@router.post("/vault/verify-log")
def verify_audit_log_integrity() -> Dict[str, Any]:
    """Mathematically verifies cryptographic hash chain integrity of the reveal log."""
    return demo_manager.verify_audit_log()


@router.post("/query/validate", response_model=QueryValidationResult)
def validate_investigation_query(req: QueryValidationRequest):
    """Evaluates an analyst query against anti-harassment policies (blocking direct employee names/emails)."""
    return demo_manager.validate_query(req.query, req.analyst_id)


@router.get("/harassment/alerts", response_model=List[HarassmentAlert])
def get_harassment_alerts():
    """Returns active DPO compliance alerts for subjects with repeat inspections (>3 in 14 days without escalation)."""
    return demo_manager.get_harassment_alerts()
