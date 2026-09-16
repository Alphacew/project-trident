"""Project TRIDENT — Context Authenticity & Anchor Schemas
Defines Pydantic models for Context Anchors, Telemetry Context Stubs,
Signal Evaluations, CAS Reports, and Anchor Evaluation Results.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AnchorType(str, Enum):
    JIRA = "JIRA"
    SERVICENOW = "SERVICENOW"
    PAGERDUTY = "PAGERDUTY"
    HR_ROLE_CHANGE = "HR_ROLE_CHANGE"
    GITHUB_PR = "GITHUB_PR"
    CALENDAR_EVENT = "CALENDAR_EVENT"
    ADHOC = "ADHOC"


class ContextAnchor(BaseModel):
    """Represents an organizational business context candidate (ticket, change request, incident)."""
    anchor_id: str
    anchor_type: AnchorType = AnchorType.JIRA
    title: str = ""
    description: str = ""
    created_at: datetime
    updated_at: Optional[datetime] = None
    requester_id: str
    approver_id: Optional[str] = None
    target_resources: List[str] = Field(default_factory=list)
    
    # Authority weight
    authority_weight: float = Field(default=0.85, ge=0.0, le=1.0)
    
    # Signal-specific properties
    is_emergency: bool = False
    actor_emergency_count_30d: int = 0
    cohort_emergency_mean_30d: float = 0.5
    cohort_emergency_std_30d: float = 0.5
    
    # Separation of duties / reporting line
    requester_approver_reporting_dist: int = 2  # 0: same person, 1: direct report/mgr, >=2: independent
    is_self_approved: bool = False
    
    # HR metadata
    hr_project_tag: Optional[str] = None
    actor_current_project_tag: Optional[str] = None
    is_stale_hr_project: bool = False
    
    # Velocity & Downstream artifacts
    ticket_velocity_window_count: int = 1  # count of tickets in actor's recent window
    downstream_commits_count: int = 0
    downstream_prs_count: int = 0
    downstream_deploys_count: int = 0
    
    # Corroborating signals
    corroborating_slack_messages_count: int = 0
    corroborating_pr_reviews_count: int = 0
    corroborating_calendar_events_count: int = 0


class EventContextStub(BaseModel):
    """Stub representing the telemetry event context needed for trust anchoring.
    Compatible with Dev A's CanonicalEvent model.
    """
    event_id: str
    timestamp: datetime
    actor_token: str
    action: str
    target_resource: str
    resource_sensitivity: float = Field(default=0.5, ge=0.0, le=1.0)
    source_type: str = "CloudTrail"


class SignalEvaluation(BaseModel):
    """Score and explanation for a single CAS signal (s_i in [-1.0, 1.0])."""
    signal_id: str
    name: str
    score: float = Field(ge=-1.0, le=1.0)
    weight: float = Field(gt=0.0)
    rationale: str
    is_flagged: bool = False


class CASReport(BaseModel):
    """Comprehensive Context Authenticity Score report with structured explainability."""
    cas_score: float = Field(ge=0.0, le=1.0)
    weighted_sum: float
    signal_evaluations: Dict[str, SignalEvaluation]
    deductions: List[str] = Field(default_factory=list)
    is_authentic: bool
    claim_label: str = "Measured Today"


class AnchorEvaluationResult(BaseModel):
    """Output of the Trust Anchor Engine evaluating an event against candidate anchors."""
    event_id: str
    selected_anchor_id: Optional[str] = None
    selected_anchor_type: Optional[AnchorType] = None
    anchor_score: float = Field(ge=0.0, le=1.0)
    
    # Invariant: context discount factor delta in [0.15, 1.0]
    discount_factor: float = Field(ge=0.15, le=1.0)
    residual_risk_ratio: float = Field(ge=0.15, le=1.0)
    
    authority_weight: float = 0.0
    cas_report: Optional[CASReport] = None
    scope_match_score: float = 0.0
    temporal_decay: float = 1.0
    delta_t_minutes: float = 0.0
    candidate_count: int = 0
    
    claim_label: str = "Measured Today"
