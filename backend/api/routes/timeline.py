"""Project TRIDENT — Timeline API Routes (Screen 1 Dual Timeline).

Endpoints:
- GET /api/timeline: Returns daily timeline series for Recharts
- GET /api/timeline/events: Returns canonical events for a specific day
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.api.manager import demo_manager
from backend.common.schemas import CanonicalEvent
from backend.scenarios.schemas import ScenarioDaySnapshot

router = APIRouter(prefix="/api/timeline", tags=["Timeline"])


@router.get("", response_model=List[ScenarioDaySnapshot])
def get_timeline_series():
    """Returns the full daily timeline dataset for Screen 1."""
    return demo_manager.get_timeline()


@router.get("/events", response_model=List[CanonicalEvent])
def get_events_for_day(day: int = Query(default=14, ge=1, le=14)):
    """Returns canonical events occurring on a specified day."""
    return demo_manager.get_events_for_day(day)
