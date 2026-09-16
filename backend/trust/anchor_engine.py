"""Project TRIDENT — Trust Anchor Engine
Implements the Anchor Score calculation combining organizational authority weight,
Context Authenticity Score (CAS), semantic scope match, and temporal decay.
Strictly enforces the context discount factor cap: delta >= 0.15 (attenuation <= 85%).
"""

import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from backend.trust.authenticity import ContextAuthenticityEngine
from backend.trust.schemas import (
    AnchorEvaluationResult,
    CASReport,
    ContextAnchor,
    EventContextStub,
)
from backend.trust.scope_matcher import compute_scope_match


class TrustAnchorEngine:
    """Organizational Trust Anchor Engine.
    Evaluates candidate anchors and computes capped context attenuation.
    """

    def __init__(
        self,
        cas_engine: Optional[ContextAuthenticityEngine] = None,
        decay_lambda: float = 0.05,  # ~14-day half-life (decay per day)
        discount_kappa: float = 1.0,  # Scaling coefficient
        max_attenuation_cap: float = 0.85,  # Invariant: max 85% discount
    ):
        self.cas_engine = cas_engine or ContextAuthenticityEngine()
        self.decay_lambda = decay_lambda
        self.discount_kappa = discount_kappa
        self.max_attenuation_cap = min(0.85, max_attenuation_cap)  # Hard bound: <= 0.85

    def _compute_temporal_decay(self, anchor: ContextAnchor, event: EventContextStub) -> Tuple[float, float]:
        """Computes exponential temporal decay e^(-lambda * delta_t_days).
        Returns: (decay_factor in [0.0, 1.0], delta_t_minutes).
        """
        delta_seconds = (event.timestamp - anchor.created_at).total_seconds()
        delta_minutes = delta_seconds / 60.0
        delta_days = max(0.0, delta_seconds / 86400.0)

        # If ticket was created after event (future ticket)
        if delta_seconds < 0:
            return 0.05, delta_minutes

        decay = math.exp(-self.decay_lambda * delta_days)
        return round(decay, 4), round(delta_minutes, 2)

    def evaluate(
        self,
        event: Any,
        candidate_anchors: List[ContextAnchor],
    ) -> AnchorEvaluationResult:
        """Evaluates an event against candidate organizational anchors.
        Selects best anchor by maximizing AnchorScore and enforces discount cap.
        Accepts either an EventContextStub or a DevA CanonicalEvent directly.
        """
        if hasattr(event, "actor") and hasattr(event, "resource"):
            event_stub = EventContextStub.from_canonical_event(event)
        else:
            event_stub = event

        # Edge Case: Zero candidate anchors
        if not candidate_anchors:
            return AnchorEvaluationResult(
                event_id=event_stub.event_id,
                selected_anchor_id=None,
                selected_anchor_type=None,
                anchor_score=0.0,
                discount_factor=1.0,  # 0% discount, 100% residual risk
                residual_risk_ratio=1.0,
                authority_weight=0.0,
                cas_report=None,
                scope_match_score=0.0,
                temporal_decay=1.0,
                delta_t_minutes=0.0,
                candidate_count=0,
                claim_label="Measured Today",
            )

        best_score = -1.0
        best_anchor: Optional[ContextAnchor] = None
        best_cas_report: Optional[CASReport] = None
        best_scope_match: float = 0.0
        best_decay: float = 1.0
        best_delta_minutes: float = 0.0

        for anchor in candidate_anchors:
            # 1. Authority weight of anchor
            auth_weight = max(0.0, min(1.0, anchor.authority_weight))

            # 2. Scope match
            scope_match = compute_scope_match(anchor, event_stub)

            # 3. Context Authenticity Score (CAS)
            cas_report = self.cas_engine.evaluate_anchor(
                anchor=anchor,
                event=event_stub,
                precomputed_scope_score=scope_match,
            )

            # 4. Temporal decay
            decay, delta_mins = self._compute_temporal_decay(anchor, event_stub)

            # 5. Candidate Anchor Score = Auth * CAS * ScopeMatch * TemporalDecay
            candidate_anchor_score = auth_weight * cas_report.cas_score * scope_match * decay

            if candidate_anchor_score > best_score:
                best_score = candidate_anchor_score
                best_anchor = anchor
                best_cas_report = cas_report
                best_scope_match = scope_match
                best_decay = decay
                best_delta_minutes = delta_mins

        # Bound anchor score to [0.0, 1.0]
        final_anchor_score = max(0.0, min(1.0, best_score if best_score >= 0 else 0.0))

        # 6. Calculate context discount factor (delta)
        # delta = 1 - min(0.85, kappa * AnchorScore)
        attenuation = min(self.max_attenuation_cap, self.discount_kappa * final_anchor_score)
        discount_factor = 1.0 - attenuation

        # Enforce non-negotiable invariant: delta >= 0.15
        discount_factor = max(0.15, min(1.0, discount_factor))

        return AnchorEvaluationResult(
            event_id=event_stub.event_id,
            selected_anchor_id=best_anchor.anchor_id if best_anchor else None,
            selected_anchor_type=best_anchor.anchor_type if best_anchor else None,
            anchor_score=round(final_anchor_score, 4),
            discount_factor=round(discount_factor, 4),
            residual_risk_ratio=round(discount_factor, 4),
            authority_weight=best_anchor.authority_weight if best_anchor else 0.0,
            cas_report=best_cas_report,
            scope_match_score=round(best_scope_match, 4),
            temporal_decay=round(best_decay, 4),
            delta_t_minutes=best_delta_minutes,
            candidate_count=len(candidate_anchors),
            claim_label="Measured Today",
        )
