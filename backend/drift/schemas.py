"""Project TRIDENT — Drift Detection & CUSUM Schemas
Defines Pydantic models for BehavioralFeatureVector, BaselineProfile,
TrajectoryState, and DriftReport.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field


class TrajectoryState(str, Enum):
    STABLE = "STABLE"
    CONTEXTUAL_DRIFT = "CONTEXTUAL_DRIFT"
    UNANCHORED_EXPLORATION = "UNANCHORED_EXPLORATION"
    HIGH_RISK_TRAJECTORY = "HIGH_RISK_TRAJECTORY"
    CRITICAL = "CRITICAL"


class BehavioralFeatureVector(BaseModel):
    """6-Dimensional standardized behavioral feature vector z_t."""
    event_volume_rate: float = Field(default=1.0, ge=0.0, description="Normalized event frequency")
    resource_sensitivity_mean: float = Field(default=0.2, ge=0.0, le=1.0, description="Mean sensitivity of accessed assets")
    new_resource_discovery_ratio: float = Field(default=0.0, ge=0.0, le=1.0, description="Fraction of previously unseen resources")
    off_hours_ratio: float = Field(default=0.0, ge=0.0, le=1.0, description="Fraction of operations outside standard shift")
    action_privilege_intensity: float = Field(default=0.1, ge=0.0, le=1.0, description="Ratio of administrative/export/modify actions")
    cross_boundary_entropy: float = Field(default=0.0, ge=0.0, description="Cross-service/cross-domain boundary dispersion")

    def to_numpy(self) -> np.ndarray:
        """Converts feature vector to 1D NumPy float array."""
        return np.array([
            self.event_volume_rate,
            self.resource_sensitivity_mean,
            self.new_resource_discovery_ratio,
            self.off_hours_ratio,
            self.action_privilege_intensity,
            self.cross_boundary_entropy,
        ], dtype=float)

    def euclidean_distance(self, other: "BehavioralFeatureVector") -> float:
        """Computes Euclidean distance ||z_t - z_baseline||_2."""
        vec_a = self.to_numpy()
        vec_b = other.to_numpy()
        return float(np.linalg.norm(vec_a - vec_b))

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> "BehavioralFeatureVector":
        """Reconstructs BehavioralFeatureVector from 6-element array."""
        clipped = np.clip(arr, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [np.inf, 1.0, 1.0, 1.0, 1.0, np.inf])
        return cls(
            event_volume_rate=float(clipped[0]),
            resource_sensitivity_mean=float(clipped[1]),
            new_resource_discovery_ratio=float(clipped[2]),
            off_hours_ratio=float(clipped[3]),
            action_privilege_intensity=float(clipped[4]),
            cross_boundary_entropy=float(clipped[5]),
        )


class BaselineProfile(BaseModel):
    """Dual baseline profile (fast 7d and slow 90d) plus peer cohort."""
    actor_token: str
    fast_baseline_7d: BehavioralFeatureVector
    slow_baseline_90d: BehavioralFeatureVector
    cohort_name: str = "Engineering-Backend"
    cohort_baseline: BehavioralFeatureVector
    cohort_drift_rate: float = Field(default=0.10, ge=0.0, description="Expected peer cohort baseline drift mu")
    cohort_variance: Dict[str, float] = Field(default_factory=lambda: {
        "event_volume_rate": 0.2,
        "resource_sensitivity_mean": 0.15,
        "new_resource_discovery_ratio": 0.1,
        "off_hours_ratio": 0.1,
        "action_privilege_intensity": 0.15,
        "cross_boundary_entropy": 0.2,
    })


class DriftReport(BaseModel):
    """Complete forensic drift report emitted by CUSUMAccumulator."""
    actor_token: str
    timestamp: datetime
    displacement_raw: float = Field(ge=0.0, description="Raw distance ||z_t - z_baseline||")
    discount_factor: float = Field(ge=0.15, le=1.0, description="Context discount factor delta in [0.15, 1.0]")
    unanchored_displacement: float = Field(ge=0.0, description="D_t = delta_t * displacement_raw")
    cusum_drift_score: float = Field(ge=0.0, description="Cumulative CUSUM score S_t")
    normalized_drift_score: float = Field(ge=0.0, le=1.0, description="Saturated S_t in [0.0, 1.0]")
    drift_velocity: float = Field(description="V_t = S_t - S_{t-1}")
    trajectory_state: TrajectoryState
    dimension_attribution: Dict[str, float] = Field(default_factory=dict, description="Z-score deviation per feature")
    forensic_insights: List[str] = Field(default_factory=list, description="Human-readable forensic bullets for SOC")
    claim_label: str = "Measured Today"
