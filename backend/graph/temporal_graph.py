"""Project TRIDENT — Temporal Graph Builder.

Implements the continuous-time heterogeneous graph model using NetworkX MultiDiGraph:
- Manages Human, Service Account, and CI/CD Runner nodes alongside Repositories, Databases, and Buckets.
- Preserves multi-edges with timestamps, relationship types, confidence scores, and resource sensitivity tags.
- Enforces chronological temporal indexing.
- Enforces defense-in-depth Invariant 1 (dropping any attempt to ingest protected endpoints).
"""

from __future__ import annotations

import bisect
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Set
import networkx as nx

from backend.common.schemas import CanonicalEvent, IdentityType, EventType
from backend.graph.schemas import (
    EdgeType,
    GraphEdgeData,
    GraphNodeData,
    NodeType,
)


class ProtectedEndpointIngestionViolation(Exception):
    """Raised when an attempt is made to ingest a protected endpoint into the graph."""
    pass


class TemporalGraphBuilder:
    """Continuous-time heterogeneous graph builder using NetworkX MultiDiGraph."""

    # Defense-in-depth blacklist enforcing Invariant 1 at the graph core
    PROTECTED_KEYWORDS: Set[str] = {
        "whistleblower", "ombuds", "ethics", "speakup", "hotline"
    }

    def __init__(self) -> None:
        self._graph = nx.MultiDiGraph()
        # Fast lookup stores
        self._nodes_by_id: Dict[str, GraphNodeData] = {}
        self._edges_by_id: Dict[str, GraphEdgeData] = {}
        # Chronological bisection index: sorted list of (timestamp_epoch, edge_id)
        self._edge_chronological_index: List[Tuple[float, str]] = []

    @property
    def graph(self) -> nx.MultiDiGraph:
        """Returns internal NetworkX MultiDiGraph instance."""
        return self._graph

    @property
    def node_count(self) -> int:
        return len(self._nodes_by_id)

    @property
    def edge_count(self) -> int:
        return len(self._edges_by_id)

    def _validate_not_protected(self, identifier: str) -> None:
        """Defense-in-depth invariant check ensuring protected endpoints never enter the graph."""
        norm = identifier.lower()
        for kw in self.PROTECTED_KEYWORDS:
            if kw in norm:
                raise ProtectedEndpointIngestionViolation(
                    f"INVARIANT VIOLATION: Protected endpoint pattern '{kw}' detected in identifier '{identifier}'. "
                    "Protected whistleblower/ethics endpoints must never enter the temporal graph."
                )

    def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        label: Optional[str] = None,
        sensitivity: float = 0.0,
        is_canary: bool = False,
        timestamp: Optional[datetime] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> GraphNodeData:
        """Adds or updates an entity node in the temporal graph."""
        self._validate_not_protected(node_id)
        ts = timestamp or datetime.now(timezone.utc)
        attrs = attributes or {}

        if node_id in self._nodes_by_id:
            node = self._nodes_by_id[node_id]
            # Update temporal activity and attributes
            if ts < node.first_seen:
                node.first_seen = ts
            if ts > node.last_seen:
                node.last_seen = ts
            node.sensitivity = max(node.sensitivity, sensitivity)
            node.is_canary = node.is_canary or is_canary
            node.attributes.update(attrs)
            # Update NetworkX node attributes
            self._graph.nodes[node_id].update(node.model_dump())
            return node

        node = GraphNodeData(
            node_id=node_id,
            node_type=node_type,
            label=label or node_id,
            sensitivity=sensitivity,
            is_canary=is_canary,
            first_seen=ts,
            last_seen=ts,
            attributes=attrs
        )
        self._nodes_by_id[node_id] = node
        self._graph.add_node(node_id, **node.model_dump())
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        timestamp: datetime,
        sensitivity: float = 0.0,
        confidence: float = 1.0,
        event_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> GraphEdgeData:
        """Persists a directed temporal edge with full metadata."""
        self._validate_not_protected(source_id)
        self._validate_not_protected(target_id)

        # Ensure source and target nodes exist (defaulting to GENERIC if not already registered)
        if source_id not in self._nodes_by_id:
            self.add_node(source_id, NodeType.GENERIC, timestamp=timestamp)
        if target_id not in self._nodes_by_id:
            self.add_node(target_id, NodeType.GENERIC, timestamp=timestamp, sensitivity=sensitivity)

        edge_id = f"EDGE-{uuid.uuid4().hex[:12].upper()}"
        edge_data = GraphEdgeData(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            timestamp=timestamp,
            confidence=confidence,
            sensitivity=sensitivity,
            event_id=event_id,
            attributes=attributes or {}
        )

        self._edges_by_id[edge_id] = edge_data

        # Add edge to NetworkX graph with key=edge_id
        self._graph.add_edge(
            source_id,
            target_id,
            key=edge_id,
            **edge_data.model_dump()
        )

        # Maintain chronological bisection index
        ts_epoch = timestamp.timestamp()
        bisect.insort(self._edge_chronological_index, (ts_epoch, edge_id))

        # Update node activity windows
        self.add_node(source_id, self._nodes_by_id[source_id].node_type, timestamp=timestamp)
        self.add_node(target_id, self._nodes_by_id[target_id].node_type, timestamp=timestamp, sensitivity=sensitivity)

        return edge_data

    def add_canonical_event(self, event: CanonicalEvent) -> GraphEdgeData:
        """Ingests a normalized CanonicalEvent directly from DevA's ingestion pipeline."""
        # 1. Resolve Actor Node Type
        actor_node_type = NodeType.HUMAN
        if event.actor.identity_type == IdentityType.SERVICE_ACCOUNT:
            actor_node_type = NodeType.SERVICE_ACCOUNT
        elif event.actor.identity_type == IdentityType.CICD_RUNNER:
            actor_node_type = NodeType.CICD_RUNNER

        self.add_node(
            node_id=event.actor.actor_token,
            node_type=actor_node_type,
            label=event.actor.actor_token,
            timestamp=event.timestamp,
            attributes={
                "role": event.actor.role,
                "department": event.actor.department,
                "peer_group": event.actor.peer_group
            }
        )

        # 2. Resolve Resource Node Type
        res_type_str = event.resource.resource_type.lower()
        res_id_lower = event.resource.resource_id.lower()
        res_node_type = NodeType.GENERIC

        if event.resource.is_canary or "canary" in res_id_lower:
            res_node_type = NodeType.CANARY_DECOY
        elif "database" in res_type_str or res_id_lower.startswith("db:"):
            res_node_type = NodeType.DATABASE
        elif "bucket" in res_type_str or "s3" in res_type_str or res_id_lower.startswith("arn:aws:s3:"):
            res_node_type = NodeType.BUCKET
        elif "repository" in res_type_str or "repo" in res_type_str or res_id_lower.startswith("repo:"):
            res_node_type = NodeType.REPOSITORY

        self.add_node(
            node_id=event.resource.resource_id,
            node_type=res_node_type,
            label=event.resource.resource_id,
            sensitivity=event.resource.sensitivity,
            is_canary=event.resource.is_canary or res_node_type == NodeType.CANARY_DECOY,
            timestamp=event.timestamp,
            attributes={"department_owner": event.resource.department_owner}
        )

        # 3. Resolve Edge Type
        action_lower = event.action.lower()
        edge_type = EdgeType.ACCESSED

        if event.resource.is_canary or "canary" in res_id_lower:
            edge_type = EdgeType.CANARY_TRIP
        elif "query" in action_lower or "select" in action_lower:
            edge_type = EdgeType.QUERIED
        elif "login" in action_lower or "session" in action_lower or "auth" in action_lower:
            edge_type = EdgeType.AUTHENTICATED
        elif "assumerole" in action_lower:
            edge_type = EdgeType.ASSUMED_ROLE
        elif "stage" in action_lower:
            edge_type = EdgeType.STAGED
        elif "exfil" in action_lower or "upload" in action_lower:
            edge_type = EdgeType.EXFILTRATED
        elif "modify" in action_lower or "update" in action_lower or "write" in action_lower or "put" in action_lower:
            edge_type = EdgeType.MODIFIED

        return self.add_edge(
            source_id=event.actor.actor_token,
            target_id=event.resource.resource_id,
            edge_type=edge_type,
            timestamp=event.timestamp,
            sensitivity=event.resource.sensitivity,
            confidence=1.0,
            event_id=event.event_id,
            attributes={
                "action": event.action,
                "source_system": event.source_system,
                "network": event.network.model_dump() if event.network else {}
            }
        )

    def get_node(self, node_id: str) -> Optional[GraphNodeData]:
        return self._nodes_by_id.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[GraphEdgeData]:
        return self._edges_by_id.get(edge_id)

    def get_all_nodes(self) -> List[GraphNodeData]:
        return list(self._nodes_by_id.values())

    def get_all_edges(self) -> List[GraphEdgeData]:
        return list(self._edges_by_id.values())

    def get_edge_ids_in_window(self, t_start: datetime, t_end: datetime) -> List[str]:
        """Uses binary bisection search for O(log E + k) windowed edge lookups."""
        start_epoch = t_start.timestamp()
        end_epoch = t_end.timestamp()

        # Find slice indices in sorted chronological list
        start_idx = bisect.bisect_left(self._edge_chronological_index, (start_epoch, ""))
        end_idx = bisect.bisect_right(self._edge_chronological_index, (end_epoch, "~"))

        return [edge_id for _, edge_id in self._edge_chronological_index[start_idx:end_idx]]
