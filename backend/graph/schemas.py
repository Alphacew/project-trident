"""Project TRIDENT — Graph Schemas & Data Contracts.

Defines Pydantic models for:
1. Graph Node & Edge representations
2. ActorFeatureVector for DevB behavioral drift analysis
3. React Flow graph export structures for Frontend Screen 2
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    HUMAN = "Human"
    SERVICE_ACCOUNT = "ServiceAccount"
    CICD_RUNNER = "CICDRunner"
    ROLE = "Role"
    DEVICE = "Device"
    REPOSITORY = "Repository"
    DATABASE = "Database"
    BUCKET = "Bucket"
    TICKET = "Ticket"
    INCIDENT = "Incident"
    CANARY_DECOY = "CanaryDecoy"
    GENERIC = "Generic"


class EdgeType(str, Enum):
    AUTHENTICATED = "AUTHENTICATED"
    QUERIED = "QUERIED"
    ACCESSED = "ACCESSED"
    MODIFIED = "MODIFIED"
    ASSUMED_ROLE = "ASSUMED_ROLE"
    STAGED = "STAGED"
    EXFILTRATED = "EXFILTRATED"
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    INVOKED = "INVOKED"
    CONNECTED_TO = "CONNECTED_TO"
    CANARY_TRIP = "CANARY_TRIP"


class GraphNodeData(BaseModel):
    """Metadata schema for nodes within the temporal enterprise graph."""
    node_id: str = Field(..., description="Unique node identifier (e.g. Subject-Theta-482, db:payroll)")
    node_type: NodeType = Field(default=NodeType.GENERIC)
    label: str = Field(..., description="Human-readable display label")
    sensitivity: float = Field(default=0.0, ge=0.0, le=1.0)
    is_canary: bool = Field(default=False)
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attributes: Dict[str, Any] = Field(default_factory=dict)


class GraphEdgeData(BaseModel):
    """Metadata schema for directed temporal edges."""
    edge_id: str = Field(..., description="Unique edge identifier")
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    edge_type: EdgeType = Field(default=EdgeType.ACCESSED)
    timestamp: datetime = Field(..., description="Event timestamp")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    sensitivity: float = Field(default=0.0, ge=0.0, le=1.0)
    event_id: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ActorFeatureVector(BaseModel):
    """Behavioral feature vector extracted from the graph over a sliding time window.
    Directly feeds DevB's fast (7-day) and slow (90-day) baseline aggregations.
    """
    actor_token: str
    window_start: datetime
    window_end: datetime
    event_count: int = 0
    unique_resources_count: int = 0
    avg_resource_sensitivity: float = 0.0
    max_resource_sensitivity: float = 0.0
    off_hours_ratio: float = 0.0
    action_diversity_entropy: float = 0.0
    nhi_interaction_count: int = 0
    data_volume_score: float = 0.0
    # Normalized numeric feature vector z_t(u)
    features: List[float] = Field(default_factory=list)


class ReactFlowNode(BaseModel):
    """Node formatted for frontend Screen 2 React Flow rendering."""
    id: str
    type: str = "customEntityNode"
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    data: Dict[str, Any] = Field(default_factory=dict)


class ReactFlowEdge(BaseModel):
    """Edge formatted for frontend Screen 2 React Flow rendering."""
    id: str
    source: str
    target: str
    label: str = ""
    animated: bool = False
    data: Dict[str, Any] = Field(default_factory=dict)


class ReactFlowGraph(BaseModel):
    """Export container for React Flow visualization."""
    nodes: List[ReactFlowNode] = Field(default_factory=list)
    edges: List[ReactFlowEdge] = Field(default_factory=list)
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None
    total_nodes: int = 0
    total_edges: int = 0
