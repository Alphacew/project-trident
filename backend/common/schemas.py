"""Canonical schemas and contracts for Project TRIDENT.

Defines Pydantic models for:
1. CanonicalEvent (OCSF-aligned normalized event representation)
2. Ingestion & Privacy boundary data models
3. AnchorCandidate & organizational context
4. 10-signal CAS results & AnchorEvaluationResult
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class IdentityType(str, Enum):
    HUMAN = "Human"
    SERVICE_ACCOUNT = "ServiceAccount"
    CICD_RUNNER = "CICDRunner"
    API_KEY = "APIKey"


class EventType(str, Enum):
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    CLOUD_API = "CLOUD_API"
    CODE_REPOSITORY = "CODE_REPOSITORY"
    DATA_ACCESS = "DATA_ACCESS"
    DATABASE_QUERY = "DATABASE_QUERY"
    DATA_STAGING = "DATA_STAGING"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    TICKET = "TICKET"
    INCIDENT = "INCIDENT"
    SYSTEM = "SYSTEM"


class ActorContext(BaseModel):
    actor_token: str = Field(
        ...,
        description="Pseudonymized identifier, e.g. Subject-Theta-482"
    )
    identity_type: IdentityType = Field(default=IdentityType.HUMAN)
    raw_id: Optional[str] = Field(
        default=None,
        description="Original raw identifier, populated only at ingestion before hashing; never saved to graph"
    )
    role: Optional[str] = None
    department: Optional[str] = None
    peer_group: Optional[str] = None


class ResourceContext(BaseModel):
    resource_id: str = Field(..., description="Unique resource identifier (e.g. ARN, DB table, repo)")
    resource_type: str = Field(default="GenericResource")
    sensitivity: float = Field(default=0.5, ge=0.0, le=1.0)
    department_owner: Optional[str] = None
    is_canary: bool = Field(default=False, description="Whether this resource is a simulated/active decoy canary")


class NetworkContext(BaseModel):
    source_ip: Optional[str] = None
    destination_endpoint: Optional[str] = None
    destination_ip: Optional[str] = None
    user_agent: Optional[str] = None
    is_vpn: Optional[bool] = None


class BusinessContext(BaseModel):
    ticket_ids: List[str] = Field(default_factory=list)
    incident_ids: List[str] = Field(default_factory=list)
    project_id: Optional[str] = None
    change_request_id: Optional[str] = None


class CanonicalEvent(BaseModel):
    """Canonical OCSF-aligned representation of a telemetry event."""
    event_id: str = Field(..., description="Globally unique UUID for the event")
    timestamp: datetime = Field(..., description="Chronologically verified timestamp")
    event_type: EventType = Field(default=EventType.SYSTEM)
    action: str = Field(..., description="Action performed, e.g. s3:GetObject, okta:login")
    actor: ActorContext
    resource: ResourceContext
    network: Optional[NetworkContext] = None
    business_context: Optional[BusinessContext] = None
    raw_payload_hash: str = Field(..., description="SHA-256 hash of original raw log payload")
    source_system: str = Field(..., description="Origin source: okta, aws_cloudtrail, github_audit, jira, etc.")
    attributes: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


class ProtectedFilterResult(BaseModel):
    """Result of evaluating an event against the Protected Endpoint Filter."""
    is_protected: bool
    matched_rule: Optional[str] = None
    audit_receipt_id: Optional[str] = None
    timestamp: datetime
    action: str = Field(default="DROP_FROM_GRAPH")


class AnchorCandidate(BaseModel):
    """Candidate organizational anchor claimed to justify activity."""
    anchor_id: str = Field(..., description="Unique anchor ID, e.g. JIRA-841, INC-4921")
    anchor_type: str = Field(default="JiraTicket", description="JiraTicket, PagerDutyIncident, ServiceNowChange, RoleChange")
    title: str
    description: str = ""
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    requester_id: str
    approver_id: Optional[str] = None
    status: str = Field(default="OPEN")
    is_emergency: bool = False
    target_resources: List[str] = Field(default_factory=list)
    downstream_artifacts: List[str] = Field(
        default_factory=list,
        description="Downstream commits, PRs, deploy hashes linked to this ticket"
    )
    corroborating_signals: List[str] = Field(
        default_factory=list,
        description="Slack message IDs, calendar meeting IDs, PR reviews"
    )
    authority_weight: float = Field(default=1.0, ge=0.0, le=1.0)


class CASSignalResult(BaseModel):
    """Result of an individual signal evaluation within the Context Authenticity Score."""
    signal_name: str
    raw_value: float
    normalized_score: float = Field(..., ge=-1.0, le=1.0, description="Normalized indicator in [-1, 1]")
    weight: float = Field(..., gt=0.0)
    weighted_contribution: float
    description: str


class CASResult(BaseModel):
    """Context Authenticity Score (CAS) combining the 10 signal indicators."""
    cas_score: float = Field(..., ge=0.0, le=1.0, description="Sigmoidal CAS score in [0, 1]")
    signal_results: Dict[str, CASSignalResult]
    is_authentic: bool
    summary: str


class AnchorEvaluationResult(BaseModel):
    """Comprehensive anchor score and context discount evaluation."""
    event_id: str
    selected_anchor_id: Optional[str] = None
    anchor_score: float = Field(default=0.0, ge=0.0, le=1.0)
    cas_score: float = Field(default=0.0, ge=0.0, le=1.0)
    discount_factor: float = Field(
        default=1.0,
        ge=0.15,
        le=1.0,
        description="Bounded attenuation factor delta in [0.15, 1.0]. Residual risk is at least 15%."
    )
    temporal_decay: float = Field(default=1.0, ge=0.0, le=1.0)
    scope_match: float = Field(default=0.0, ge=0.0, le=1.0)
    authority_weight: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("discount_factor")
    @classmethod
    def validate_discount_cap(cls, v: float) -> float:
        if v < 0.15 - 1e-6:
            raise ValueError(f"Discount factor {v} violates hard invariant: minimum residual risk is 15% (delta >= 0.15)")
        return v
