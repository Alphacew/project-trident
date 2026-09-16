"""Project TRIDENT — Risk API Routes.

Endpoints:
- GET /api/risk/trajectory: Returns current trajectory metrics, velocity, CUSUM drift score, risk tier
- GET /api/risk/history: Returns historical risk trend series
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Query

from backend.api.manager import demo_manager
from backend.scenarios.schemas import ScenarioDaySnapshot

router = APIRouter(prefix="/api/risk", tags=["Risk"])


@router.get("/trajectory", response_model=ScenarioDaySnapshot)
def get_risk_trajectory(day: Optional[int] = Query(default=None, ge=1, le=14)):
    """Returns risk trajectory metrics for the active or requested day."""
    return demo_manager.get_risk_trajectory(day)


@router.get("/history", response_model=List[ScenarioDaySnapshot])
def get_risk_history():
    """Returns historical risk snapshots across the entire active scenario timeline."""
    return demo_manager.get_timeline()
