"""Project TRIDENT — Scenario Management API Routes.

Endpoints:
- GET /api/scenarios: Lists metadata for all available synthetic scenarios
- POST /api/scenarios/{scenario_id}/execute: Activates and computes the requested scenario
- POST /api/scenarios/scrub/{day}: Sets the active timeline scrub day
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException, Path

from backend.api.manager import demo_manager
from backend.scenarios.schemas import ScenarioExecutionResult, ScenarioMetadata

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])


@router.get("", response_model=List[ScenarioMetadata])
def list_scenarios():
    """Lists all available synthetic scenarios."""
    return demo_manager.list_scenarios()


@router.post("/{scenario_id}/execute", response_model=ScenarioExecutionResult)
def execute_scenario(scenario_id: str = Path(...)):
    """Switches active scenario and precomputes timeline states."""
    result = demo_manager.set_active_scenario(scenario_id)
    return result


@router.post("/scrub/{day}")
def set_timeline_scrub_day(day: int = Path(..., ge=1, le=14)):
    """Sets active scrub day for multi-day timeline analysis."""
    demo_manager.set_day(day)
    return {"status": "success", "selected_day": demo_manager.selected_day}
