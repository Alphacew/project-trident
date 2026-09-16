"""Project TRIDENT — Composite Risk Scoring Schemas
Defines Pydantic models for Risk Tiers, Risk Breakdown, and Risk Score Results.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RiskTier(str, Enum):
    TIER_1_CONTEXTUAL_DRIFT = "TIER_1_CONTEXTUAL_DRIFT"
    TIER_2_UNANCHORED_EXPLORATION = "TIER_2_UNANCHORED_EXPLORATION"
    TIER_3_HIGH_RISK_TRAJECTORY = "TIER_3_HIGH_RISK_TRAJECTORY"
    TIER_4_CRITICAL = "TIER_4_CRITICAL"


class RiskBreakdown(BaseModel):
    """Component-by-component decomposition of the deterministic risk formula:
    CompositeRisk = Anomaly * ContextUncertainty * CumulativeDrift * Criticality * IdentityRisk
    """
    anomaly_score: float = Field(ge=0.0, le=1.0, description="Behavioral anomaly score A_t")
    context_uncertainty: float = Field(ge=0.15, le=1.0, description="Contextual uncertainty U_t = 1 - (delta_t * AnchorScore)")
    cumulative_drift: float = Field(ge=0.0, le=1.0, description="Normalized cumulative drift S_norm in [0, 1]")
    resource_criticality: float = Field(ge=0.1, le=1.0, description="Resource criticality C_t in [0.1, 1.0]")
    identity_risk: float = Field(ge=1.0, le=2.0, description="Identity risk multiplier I_t (Human=1.0, ServiceAccount=1.35)")
    raw_product: float = Field(description="Direct product of the 5 factors")


class RiskScoreResult(BaseModel):
    """Deterministic composite risk evaluation result."""
    actor_token: str
    timestamp: datetime
    composite_risk: float = Field(ge=0.0, le=100.0, description="Composite Risk Score in [0.0, 100.0]")
    risk_tier: RiskTier
    breakdown: RiskBreakdown
    recommended_action: str
    mitre_tactics: List[str] = Field(default_factory=list)
    claim_label: str = "Measured Today"
