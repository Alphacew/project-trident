"""Project TRIDENT — Privacy Vault API Routes (Screen 3).

Endpoints:
- GET /api/privacy/vault/status: Returns privacy vault status and custodian shares
- POST /api/privacy/vault/recombine: Executes Shamir 2-of-3 reveal ceremony
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from backend.api.manager import demo_manager
from backend.crypto.shamir_vault import RevealReceipt

router = APIRouter(prefix="/api/privacy", tags=["Privacy"])


class UnmaskRequest(BaseModel):
    share_indices: List[int] = Field(..., description="Indices of participating custodian shares (e.g. [1, 2])")
    subject_token: str = Field(..., description="Pseudonymized token to unmask, e.g. Subject-Theta-482")
    justification: str = Field(..., description="Audited legal/compliance justification")
    auditor_token: str = Field(default="DPO-Audit-Session-101")


@router.get("/vault/status")
def get_vault_status() -> Dict[str, Any]:
    """Returns privacy vault status and custodian shares for Screen 3."""
    return demo_manager.get_privacy_vault_status()


@router.post("/vault/recombine", response_model=RevealReceipt)
def recombine_shares(req: UnmaskRequest):
    """Executes Shamir 2-of-3 threshold unmasking ceremony."""
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
