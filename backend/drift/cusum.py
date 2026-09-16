"""Project TRIDENT — Unanchored Displacement & Recursive CUSUM Drift Engine
Implements the continuous CUSUM accumulation over context-attenuated behavioral displacement:
    D_t = delta_t * ||z_t - z_baseline||_2
    S_t = max(0, S_{t-1} + D_t - mu_cohort - k)
Outputs trajectory states and dimension-level forensic attribution.
"""

import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import numpy as np
from backend.drift.baselines import BaselineManager
from backend.drift.schemas import (
    BehavioralFeatureVector,
    DriftReport,
    TrajectoryState,
)


class CUSUMDriftEngine:
    """Recursive CUSUM drift accumulator with calibrated trajectory thresholds."""

    def __init__(
        self,
        baseline_manager: Optional[BaselineManager] = None,
        slack_k: float = 0.15,
        tau_stable: float = 0.80,
        tau_high_risk: float = 2.00,
        tau_critical: float = 4.00,
    ):
        self.baseline_manager = baseline_manager or BaselineManager()
        self.slack_k = slack_k
        self.tau_stable = tau_stable
        self.tau_high_risk = tau_high_risk
        self.tau_critical = tau_critical
        
        # Internal state store: actor_token -> S_{t-1}
        self.cusum_states: Dict[str, float] = {}

    def reset_actor_state(self, actor_token: str) -> None:
        """Resets CUSUM accumulator state S_t for an actor to 0.0."""
        self.cusum_states[actor_token] = 0.0

    def compute_displacement(
        self,
        current_vector: BehavioralFeatureVector,
        baseline_vector: BehavioralFeatureVector,
        discount_factor: float,
    ) -> float:
        """Computes unanchored displacement D_t = delta_t * ||z_t - z_baseline||_2.
        discount_factor delta_t must be in [0.15, 1.0].
        """
        # Hard cap invariant: delta_t >= 0.15
        clamped_delta = max(0.15, min(1.0, discount_factor))
        raw_dist = current_vector.euclidean_distance(baseline_vector)
        return float(clamped_delta * raw_dist)

    def _generate_forensic_attribution(
        self,
        current: BehavioralFeatureVector,
        baseline: BehavioralFeatureVector,
        variance_map: Dict[str, float],
    ) -> Tuple[Dict[str, float], List[str]]:
        """Computes dimension-level z-deviations and human-readable forensic insights."""
        feature_names = [
            "event_volume_rate",
            "resource_sensitivity_mean",
            "new_resource_discovery_ratio",
            "off_hours_ratio",
            "action_privilege_intensity",
            "cross_boundary_entropy",
        ]
        curr_arr = current.to_numpy()
        base_arr = baseline.to_numpy()

        attribution: Dict[str, float] = {}
        insights: List[str] = []

        labels = {
            "event_volume_rate": "Event Volume",
            "resource_sensitivity_mean": "Resource Sensitivity",
            "new_resource_discovery_ratio": "New Resource Discovery",
            "off_hours_ratio": "Off-Hours Activity",
            "action_privilege_intensity": "Privileged Action Intensity",
            "cross_boundary_entropy": "Cross-Boundary Movement",
        }

        for i, name in enumerate(feature_names):
            diff = curr_arr[i] - base_arr[i]
            std = variance_map.get(name, 0.15)
            z_score = diff / (std + 1e-6)
            attribution[name] = round(float(z_score), 2)

            if z_score >= 2.0:
                pct = int((diff / max(1e-4, base_arr[i])) * 100) if base_arr[i] > 0 else int(diff * 100)
                insights.append(f"CRITICAL: {labels[name]} elevated (+{pct}% vs baseline, z={z_score:.1f}σ)")
            elif z_score >= 1.2:
                insights.append(f"HIGH: {labels[name]} abnormal deviation (z={z_score:.1f}σ)")

        return attribution, insights

    def update(
        self,
        actor_token: str,
        current_vector: BehavioralFeatureVector,
        discount_factor: float = 1.0,
        timestamp: Optional[datetime] = None,
    ) -> DriftReport:
        """Processes a new behavioral feature vector z_t, calculates displacement,
        updates recursive CUSUM S_t, and emits a comprehensive DriftReport.
        """
        now = timestamp or datetime.now(timezone.utc)
        profile = self.baseline_manager.get_or_create_profile(actor_token)
        effective_base = self.baseline_manager.compute_effective_baseline(actor_token)

        # 1. Compute raw displacement and unanchored displacement
        raw_dist = current_vector.euclidean_distance(effective_base)
        clamped_delta = max(0.15, min(1.0, discount_factor))
        unanchored_disp = clamped_delta * raw_dist

        # 2. Retrieve previous S_{t-1}
        prev_s = self.cusum_states.get(actor_token, 0.0)

        # 3. Recursive CUSUM: S_t = max(0, S_{t-1} + D_t - mu_cohort - k)
        mu_cohort = profile.cohort_drift_rate
        increment = unanchored_disp - mu_cohort - self.slack_k
        current_s = max(0.0, prev_s + increment)

        # Update internal state
        self.cusum_states[actor_token] = current_s
        drift_velocity = current_s - prev_s

        # 4. Saturated normalized drift score in [0.0, 1.0)
        # S_norm = 1 - exp(-S_t / tau_high_risk)
        normalized_s = 1.0 - math.exp(-current_s / self.tau_high_risk) if self.tau_high_risk > 0 else 0.0
        normalized_s = max(0.0, min(1.0, normalized_s))

        # 5. Trajectory state classification
        if current_s < self.tau_stable:
            state = TrajectoryState.STABLE
        elif current_s < self.tau_high_risk:
            # If discount_factor is low (strong context), it's contextual drift
            if clamped_delta <= 0.35:
                state = TrajectoryState.CONTEXTUAL_DRIFT
            else:
                state = TrajectoryState.UNANCHORED_EXPLORATION
        elif current_s < self.tau_critical:
            state = TrajectoryState.HIGH_RISK_TRAJECTORY
        else:
            state = TrajectoryState.CRITICAL

        # 6. Forensic attribution
        attribution, insights = self._generate_forensic_attribution(
            current_vector, effective_base, profile.cohort_variance
        )

        return DriftReport(
            actor_token=actor_token,
            timestamp=now,
            displacement_raw=round(raw_dist, 4),
            discount_factor=round(clamped_delta, 4),
            unanchored_displacement=round(unanchored_disp, 4),
            cusum_drift_score=round(current_s, 4),
            normalized_drift_score=round(normalized_s, 4),
            drift_velocity=round(drift_velocity, 4),
            trajectory_state=state,
            dimension_attribution=attribution,
            forensic_insights=insights,
            claim_label="Measured Today",
        )
