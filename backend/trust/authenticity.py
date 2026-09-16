"""Project TRIDENT — Context Authenticity Score (CAS) Engine
Evaluates all 10 signals, computes the logistic sigmoid CAS score,
and synthesizes a structured explainable CASReport with forensic deductions.
"""

import math
from typing import Dict, List, Optional
from backend.trust.schemas import ContextAnchor, EventContextStub, SignalEvaluation, CASReport
from backend.trust.scope_matcher import compute_scope_match
from backend.trust.signals import (
    DEFAULT_SIGNAL_WEIGHTS,
    eval_s1_temporal_mismatch,
    eval_s2_approver_conflict,
    eval_s3_emergency_abuse,
    eval_s4_sod_violation,
    eval_s5_stale_hr_metadata,
    eval_s6_scope_mismatch,
    eval_s7_cross_signal_inconsistency,
    eval_s8_ticket_velocity_anomaly,
    eval_s9_ghost_ticket,
    eval_s10_post_hoc_modification,
)


def sigmoid(z: float) -> float:
    """Standard logistic sigmoid function with numerical overflow protection."""
    if z < -40.0:
        return 0.0
    elif z > 40.0:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


class ContextAuthenticityEngine:
    """Computes the 10-signal Context Authenticity Score (CAS) for organizational anchors."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or DEFAULT_SIGNAL_WEIGHTS.copy()

    def evaluate_anchor(
        self,
        anchor: ContextAnchor,
        event: EventContextStub,
        precomputed_scope_score: Optional[float] = None,
    ) -> CASReport:
        """Evaluates all 10 signals for an anchor against an event and returns a CASReport."""
        # 1. Compute scope match if not precomputed
        scope_score = (
            precomputed_scope_score
            if precomputed_scope_score is not None
            else compute_scope_match(anchor, event)
        )

        # 2. Evaluate each of the 10 signals
        evaluations: Dict[str, SignalEvaluation] = {
            "s1_temporal_mismatch": eval_s1_temporal_mismatch(
                anchor, event, self.weights.get("s1_temporal_mismatch", 1.5)
            ),
            "s2_approver_conflict": eval_s2_approver_conflict(
                anchor, event, self.weights.get("s2_approver_conflict", 1.2)
            ),
            "s3_emergency_abuse": eval_s3_emergency_abuse(
                anchor, event, self.weights.get("s3_emergency_abuse", 1.0)
            ),
            "s4_sod_violation": eval_s4_sod_violation(
                anchor, event, self.weights.get("s4_sod_violation", 1.5)
            ),
            "s5_stale_hr_metadata": eval_s5_stale_hr_metadata(
                anchor, event, self.weights.get("s5_stale_hr_metadata", 0.8)
            ),
            "s6_scope_mismatch": eval_s6_scope_mismatch(
                anchor, event, scope_score, self.weights.get("s6_scope_mismatch", 1.4)
            ),
            "s7_cross_signal_inconsistency": eval_s7_cross_signal_inconsistency(
                anchor, event, self.weights.get("s7_cross_signal_inconsistency", 0.9)
            ),
            "s8_ticket_velocity_anomaly": eval_s8_ticket_velocity_anomaly(
                anchor, event, self.weights.get("s8_ticket_velocity_anomaly", 0.8)
            ),
            "s9_ghost_ticket": eval_s9_ghost_ticket(
                anchor, event, self.weights.get("s9_ghost_ticket", 1.3)
            ),
            "s10_post_hoc_modification": eval_s10_post_hoc_modification(
                anchor, event, self.weights.get("s10_post_hoc_modification", 1.4)
            ),
        }

        # 3. Compute weighted sum: sum(w_i * s_i)
        weighted_sum = sum(sig.weight * sig.score for sig in evaluations.values())

        # 4. Logistic sigmoid over weighted sum
        cas_score = sigmoid(weighted_sum)

        # 5. Extract structured forensic deductions for SOC analyst review
        deductions: List[str] = []
        for sig in evaluations.values():
            if sig.is_flagged or sig.score < 0:
                deductions.append(f"[{sig.name}] {sig.rationale} (score: {sig.score:+.2f})")

        return CASReport(
            cas_score=round(cas_score, 4),
            weighted_sum=round(weighted_sum, 4),
            signal_evaluations=evaluations,
            deductions=deductions,
            is_authentic=(cas_score >= 0.60),
            claim_label="Measured Today",
        )
