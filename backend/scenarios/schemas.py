"""Project TRIDENT — Scenario Schemas.

Defines Pydantic models for:
1. ScenarioType and ScenarioMetadata
2. ScenarioDataset (Canonical events, candidate anchors, baseline resources)
3. ScenarioDaySnapshot (Per-day metrics: drift, risk, vectors)
4. ScenarioExecutionResult (End-to-end scenario evaluation outcome)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from backend.common.schemas import AnchorCandidate, CanonicalEvent
from backend.drift.schemas import DriftReport, TrajectoryState
from backend.risk.schemas import RiskScoreResult, RiskTier


class ScenarioType(str, Enum):
    SCENARIO_A_ROLE_CHANGE = "scenario_a_role_change"
    SCENARIO_B_LOW_AND_SLOW = "scenario_b_low_and_slow"
    SCENARIO_C_FABRICATED_CONTEXT = "scenario_c_fabricated_context"
    SCENARIO_D_EMERGENCY_INCIDENT = "scenario_d_emergency_incident"
    SCENARIO_E_COMPROMISED_SERVICE_ACCOUNT = "scenario_e_compromised_service_account"
    MASTER_14_DAY_DEMO = "master_14_day_demo"


class ScenarioMetadata(BaseModel):
    """Metadata describing an enterprise scenario."""
    scenario_id: str
    scenario_type: ScenarioType
    name: str
    description: str
    primary_actor_token: str
    duration_days: int
    expected_trajectory_state: TrajectoryState
    expected_risk_tier: RiskTier
    key_signals: List[str] = Field(default_factory=list)
    claim_label: str = Field(default="Measured Today")


class ScenarioDataset(BaseModel):
    """Encapsulates telemetry and anchor records comprising a scenario."""
    metadata: ScenarioMetadata
    events: List[CanonicalEvent]
    anchors: List[AnchorCandidate] = Field(default_factory=list)
    historical_resources: List[str] = Field(default_factory=list)


class ScenarioDaySnapshot(BaseModel):
    """Captures daily evaluation state along a scenario timeline."""
    day: int
    timestamp: datetime
    events_count: int
    raw_anomaly_score: float
    context_authenticity_score: float
    discount_factor: float
    attenuated_anomaly_score: float
    cusum_drift_score: float
    drift_velocity: float
    trajectory_state: TrajectoryState
    composite_risk: float
    risk_tier: RiskTier
    canary_state: str = Field(default="UNCONFIRMED")
    active_mitre_tactics: List[str] = Field(default_factory=list)


class ScenarioExecutionResult(BaseModel):
    """Full execution summary of a scenario run."""
    metadata: ScenarioMetadata
    daily_snapshots: List[ScenarioDaySnapshot]
    final_drift_score: float
    final_trajectory_state: TrajectoryState
    final_risk_score: float
    final_risk_tier: RiskTier
    evaluation_passed: bool
    evaluation_notes: str
    claim_label: str = Field(default="Measured Today")
