"""Project TRIDENT — Evidence & Investigation API Routes.

Endpoints:
- GET /api/evidence/dossier: Returns complete forensic incident dossier
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query

from backend.api.manager import demo_manager
from backend.evidence.schemas import ForensicDossier

router = APIRouter(prefix="/api/evidence", tags=["Evidence"])


@router.get("/dossier", response_model=ForensicDossier)
def get_forensic_dossier(day: Optional[int] = Query(default=None, ge=1, le=14)):
    """Returns complete evidence-backed incident dossier for the selected day."""
    return demo_manager.get_forensic_dossier(day)
