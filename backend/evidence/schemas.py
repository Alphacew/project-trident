"""Project TRIDENT — Evidence Engine Schemas.

Defines Pydantic models for:
1. ProgressionStage and ProgressionStep (Chain from credential anomaly to exfiltration)
2. EvidenceConfirmationState and CanaryDecoy (Simulated Deception Layer)
3. CausalSubgraphPayload (React Flow DAG for Screen 2)
4. ForensicDossier (Investigative incident report)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.graph.schemas import ReactFlowEdge, ReactFlowNode
from backend.risk.schemas import RiskTier
from backend.drift.schemas import TrajectoryState


class ProgressionStage(str, Enum):
    CREDENTIAL_ANOMALY = "CREDENTIAL_ANOMALY"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    DISCOVERY = "DISCOVERY"
    SENSITIVE_ACCESS = "SENSITIVE_ACCESS"
    STAGING = "STAGING"
    CANARY_TRIP = "CANARY_TRIP"
    EXFILTRATION = "EXFILTRATION"


class ProgressionStep(BaseModel):
    """An individual link in the minimal causal progression chain."""
    step_number: int
    timestamp: datetime
    stage: ProgressionStage
    source_node: str
    target_node: str
    action: str
    edge_type: str
    mitre_tactic: str
    mitre_technique: str
    description: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    sensitivity: float = Field(default=0.5, ge=0.0, le=1.0)
    event_id: Optional[str] = None


class EvidenceConfirmationState(str, Enum):
    UNCONFIRMED = "UNCONFIRMED"
    PREDICTED = "PREDICTED"
    CONFIRMED = "CONFIRMED"


class CanaryDecoy(BaseModel):
    """Simulated canary asset tracking deployment and trigger status."""
    canary_id: str
    resource_id: str
    resource_type: str
    created_at: datetime
    is_tripped: bool = False
    trip_timestamp: Optional[datetime] = None
    tripped_by_actor: Optional[str] = None
    predicted_threat_actor: Optional[str] = None
    confirmation_state: EvidenceConfirmationState = EvidenceConfirmationState.UNCONFIRMED
    claim_label: str = Field(default="Simulated Canary")


class CausalSubgraphPayload(BaseModel):
    """Serialized React Flow graph for Screen 2 highlighting the minimal attack path."""
    actor_token: str
    nodes: List[ReactFlowNode]
    edges: List[ReactFlowEdge]
    progression_steps: List[ProgressionStep]
    attack_path_length: int
    confirmation_state: EvidenceConfirmationState
    claim_label: str = Field(default="Measured Today")


class ForensicDossier(BaseModel):
    """Complete forensic incident investigation dossier."""
    subject_token: str
    incident_id: str
    timestamp: datetime
    risk_tier: RiskTier
    composite_risk: float
    trajectory_state: TrajectoryState
    cusum_drift_score: float
    context_justification_claimed: bool
    context_authenticity_score: float
    anchor_discount_factor: float
    context_failure_reasons: List[str]
    progression_chain: List[ProgressionStep]
    mitre_attack_matrix: List[Dict[str, str]]
    executive_summary: str
    recommended_response: str
    canary_status: CanaryDecoy
    claim_label: str = Field(default="Measured Today")
