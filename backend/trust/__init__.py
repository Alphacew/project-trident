"""Project TRIDENT — Trust & Context Authenticity Module."""

from backend.trust.schemas import (
    AnchorType,
    ContextAnchor,
    EventContextStub,
    SignalEvaluation,
    CASReport,
    AnchorEvaluationResult,
)
from backend.trust.signals import DEFAULT_SIGNAL_WEIGHTS
from backend.trust.scope_matcher import compute_scope_match
from backend.trust.authenticity import ContextAuthenticityEngine, sigmoid
from backend.trust.anchor_engine import TrustAnchorEngine

__all__ = [
    "AnchorType",
    "ContextAnchor",
    "EventContextStub",
    "SignalEvaluation",
    "CASReport",
    "AnchorEvaluationResult",
    "DEFAULT_SIGNAL_WEIGHTS",
    "compute_scope_match",
    "ContextAuthenticityEngine",
    "sigmoid",
    "TrustAnchorEngine",
]
