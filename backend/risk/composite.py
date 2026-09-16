"""Project TRIDENT — Deterministic Composite Risk Engine
Calculates Composite Risk strictly from mathematical models without LLM dependencies:
    CompositeRisk = Anomaly * ContextUncertainty * CumulativeDrift * Criticality * IdentityRisk
Maps continuous risk in [0, 100] into calibrated Tiers 1 through 4 with automated response directives.
"""

from datetime import datetime, timezone
from typing import List, Optional
from backend.risk.schemas import RiskBreakdown, RiskScoreResult, RiskTier


class CompositeRiskCalculator:
    """Strictly deterministic, mathematical composite risk scoring engine."""

    IDENTITY_RISK_MAP = {
        "Human": 1.0,
        "Human-Standard": 1.0,
        "Human-Privileged": 1.15,
        "CICDRunner": 1.25,
        "NonHuman-CICDRunner": 1.25,
        "ServiceAccount": 1.35,
        "NonHuman-ServiceAccount": 1.35,
    }

    def __init__(
        self,
        tier1_threshold: float = 25.0,
        tier2_threshold: float = 55.0,
        tier3_threshold: float = 80.0,
    ):
        self.tier1_threshold = tier1_threshold
        self.tier2_threshold = tier2_threshold
        self.tier3_threshold = tier3_threshold

    def calculate_context_uncertainty(
        self,
        anchor_score: float,
        discount_factor: float,
    ) -> float:
        """Calculates contextual uncertainty U_t = 1 - min(0.85, AnchorScore * (1 - delta_t)).
        Invariant: U_t in [0.15, 1.0].
        """
        # (1 - delta_t) is the actual attenuation applied
        effective_attenuation = max(0.0, 1.0 - discount_factor)
        mitigation = min(0.85, anchor_score * effective_attenuation)
        uncertainty = 1.0 - mitigation
        return round(max(0.15, min(1.0, uncertainty)), 4)

    def evaluate(
        self,
        actor_token: str,
        anomaly_score: float,
        anchor_score: float,
        discount_factor: float,
        cumulative_drift_score: float,
        resource_criticality: float = 0.5,
        identity_type: str = "Human",
        timestamp: Optional[datetime] = None,
    ) -> RiskScoreResult:
        """Evaluates composite risk from the 5 deterministic factors:
            A_t: Behavioral Anomaly Score in [0.1, 1.0]
            U_t: Contextual Uncertainty in [0.15, 1.0]
            S_t: Cumulative Drift Factor in [0.0, 1.0]
            C_t: Resource Criticality in [0.1, 1.0]
            I_t: Identity Risk Multiplier in [1.0, 1.5]
        """
        now = timestamp or datetime.now(timezone.utc)

        # 1. Clamp and normalize inputs
        a_norm = max(0.05, min(1.0, anomaly_score))
        u_norm = self.calculate_context_uncertainty(anchor_score, discount_factor)
        s_norm = max(0.0, min(1.0, cumulative_drift_score))
        c_norm = max(0.10, min(1.0, resource_criticality))
        i_mult = self.IDENTITY_RISK_MAP.get(identity_type, 1.0)

        # 2. Raw Product of the 5 factors
        raw_product = a_norm * u_norm * s_norm * c_norm * i_mult

        # 3. Scaling to [0.0, 100.0] with nonlinear sensitivity calibration
        # Power scaling (sqrt of product) ensures proportional response across low-and-slow trajectories
        calibrated_score = (raw_product ** 0.65) * 100.0
        composite_risk = round(max(0.0, min(100.0, calibrated_score)), 2)

        # 4. Map into calibrated Risk Tiers
        if composite_risk < self.tier1_threshold:
            tier = RiskTier.TIER_1_CONTEXTUAL_DRIFT
            action = "Automated baseline update. Context verified; suppressed from SOC queue."
            mitre: List[str] = []
        elif composite_risk < self.tier2_threshold:
            tier = RiskTier.TIER_2_UNANCHORED_EXPLORATION
            action = "Queue for Tier-2 SOC review. Recommend step-up MFA challenge."
            mitre = ["T1078 (Valid Accounts)", "T1087 (Account Discovery)"]
        elif composite_risk < self.tier3_threshold:
            tier = RiskTier.TIER_3_HIGH_RISK_TRAJECTORY
            action = "High-Risk Trajectory: Revoke temporary access credentials, capture forensic snapshot, trigger canary decoy verification."
            mitre = ["T1078 (Valid Accounts)", "T1068 (Privilege Escalation)", "T1005 (Data from Local System)"]
        else:
            tier = RiskTier.TIER_4_CRITICAL
            action = "CRITICAL THREAT: Isolate endpoint, revoke all active credentials, freeze egress network path, initiate Shamir dual-custody unmasking protocol."
            mitre = ["T1078 (Valid Accounts)", "T1068 (Privilege Escalation)", "T1005 (Data from Local System)", "T1567 (Exfiltration Over Web Service)"]

        breakdown = RiskBreakdown(
            anomaly_score=round(a_norm, 4),
            context_uncertainty=round(u_norm, 4),
            cumulative_drift=round(s_norm, 4),
            resource_criticality=round(c_norm, 4),
            identity_risk=round(i_mult, 4),
            raw_product=round(raw_product, 6),
        )

        return RiskScoreResult(
            actor_token=actor_token,
            timestamp=now,
            composite_risk=composite_risk,
            risk_tier=tier,
            breakdown=breakdown,
            recommended_action=action,
            mitre_tactics=mitre,
            claim_label="Measured Today",
        )
