"""Project TRIDENT — Canary Deception API Routes.

Endpoints:
- GET /api/canary/status: Returns simulated canary decoy assets and confirmation state
- POST /api/canary/trip: Manually trips simulated canary, confirming breach evidence
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter

from backend.api.manager import demo_manager
from backend.evidence.schemas import CanaryDecoy

router = APIRouter(prefix="/api/canary", tags=["Canary"])


class CanaryTripRequest(BaseModel):
    resource_id: Optional[str] = "arn:aws:s3:::canary-decoy-payroll-backup"


@router.get("/status", response_model=CanaryDecoy)
def get_canary_status():
    """Returns primary simulated canary decoy status and confirmation state."""
    return demo_manager.get_canary_status()


@router.post("/trip", response_model=CanaryDecoy)
def trigger_canary_trip(req: CanaryTripRequest):
    """Triggers simulated canary trip, transitioning confirmation state to CONFIRMED."""
    return demo_manager.trigger_canary_trip(req.resource_id)
