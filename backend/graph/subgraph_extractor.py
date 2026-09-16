"""Project TRIDENT — Time-Window & Causal Subgraph Extractor.

Provides:
1. Sliding time-window subgraph slicing across [t_start, t_end].
2. Ego-network causal subgraph extraction around specific actor tokens.
3. React Flow visualization serialization for Frontend Screen 2.
4. Behavioral feature vector extraction (ActorFeatureVector) for DevB drift analysis.
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
import networkx as nx

from backend.graph.schemas import (
    ActorFeatureVector,
    EdgeType,
    GraphEdgeData,
    GraphNodeData,
    NodeType,
    ReactFlowEdge,
    ReactFlowGraph,
    ReactFlowNode,
)
from backend.graph.temporal_graph import TemporalGraphBuilder


class TimeWindowExtractor:
    """Extracts windowed subgraphs, causal ego-networks, and behavioral features."""

    def __init__(self, builder: TemporalGraphBuilder) -> None:
        self.builder = builder

    def extract_window(
        self,
        t_start: datetime,
        t_end: datetime
    ) -> TemporalGraphBuilder:
        """Returns a new TemporalGraphBuilder instance containing only edges and nodes within [t_start, t_end]."""
        sub_builder = TemporalGraphBuilder()
        edge_ids = self.builder.get_edge_ids_in_window(t_start, t_end)

        for eid in edge_ids:
            edge = self.builder.get_edge(eid)
            if not edge:
                continue

            # Ensure endpoints are added
            src_node = self.builder.get_node(edge.source_id)
            tgt_node = self.builder.get_node(edge.target_id)

            if src_node:
                sub_builder.add_node(
                    node_id=src_node.node_id,
                    node_type=src_node.node_type,
                    label=src_node.label,
                    sensitivity=src_node.sensitivity,
                    is_canary=src_node.is_canary,
                    timestamp=edge.timestamp,
                    attributes=src_node.attributes
                )
            if tgt_node:
                sub_builder.add_node(
                    node_id=tgt_node.node_id,
                    node_type=tgt_node.node_type,
                    label=tgt_node.label,
                    sensitivity=tgt_node.sensitivity,
                    is_canary=tgt_node.is_canary,
                    timestamp=edge.timestamp,
                    attributes=tgt_node.attributes
                )

            # Add edge
            sub_builder.add_edge(
                source_id=edge.source_id,
                target_id=edge.target_id,
                edge_type=edge.edge_type,
                timestamp=edge.timestamp,
                sensitivity=edge.sensitivity,
                confidence=edge.confidence,
                event_id=edge.event_id,
                attributes=edge.attributes
            )

        return sub_builder

    def extract_ego_subgraph(
        self,
        seed_actor_token: str,
        t_start: Optional[datetime] = None,
        t_end: Optional[datetime] = None,
        hops: int = 2
    ) -> TemporalGraphBuilder:
        """Extracts a causal k-hop ego subgraph centered on an actor within an optional time window."""
        window_builder = self.builder
        if t_start is not None and t_end is not None:
            window_builder = self.extract_window(t_start, t_end)

        if seed_actor_token not in window_builder._nodes_by_id:
            return TemporalGraphBuilder()

        # Perform BFS up to `hops` on underlying undirected projection to capture causal flow
        g = window_builder.graph
        nodes_in_ego: Set[str] = {seed_actor_token}
        current_frontier: Set[str] = {seed_actor_token}

        for _ in range(hops):
            next_frontier: Set[str] = set()
            for node in current_frontier:
                if g.has_node(node):
                    neighbors = set(g.successors(node)).union(set(g.predecessors(node)))
                    new_neighbors = neighbors - nodes_in_ego
                    next_frontier.update(new_neighbors)
                    nodes_in_ego.update(new_neighbors)
            current_frontier = next_frontier
            if not current_frontier:
                break

        ego_builder = TemporalGraphBuilder()
        for node_id in nodes_in_ego:
            nd = window_builder.get_node(node_id)
            if nd:
                ego_builder.add_node(
                    node_id=nd.node_id,
                    node_type=nd.node_type,
                    label=nd.label,
                    sensitivity=nd.sensitivity,
                    is_canary=nd.is_canary,
                    attributes=nd.attributes
                )

        # Include all edges connecting nodes within the ego set
        for u, v, key, data in g.edges(keys=True, data=True):
            if u in nodes_in_ego and v in nodes_in_ego:
                ego_builder.add_edge(
                    source_id=u,
                    target_id=v,
                    edge_type=EdgeType(data.get("edge_type", EdgeType.ACCESSED)),
                    timestamp=data.get("timestamp", datetime.now(timezone.utc)),
                    sensitivity=data.get("sensitivity", 0.0),
                    confidence=data.get("confidence", 1.0),
                    event_id=data.get("event_id"),
                    attributes=data.get("attributes", {})
                )

        return ego_builder

    def to_react_flow(self, target_builder: Optional[TemporalGraphBuilder] = None) -> ReactFlowGraph:
        """Serializes a graph into standard React Flow schema with structured visual layout."""
        b = target_builder or self.builder
        nodes: List[ReactFlowNode] = []
        edges: List[ReactFlowEdge] = []

        node_list = b.get_all_nodes()
        edge_list = b.get_all_edges()

        # Categorize node columns for layered left-to-right DAG layout:
        # Col 0: Identities (Human, ServiceAccount, Runner)
        # Col 1: Roles & Auth credentials
        # Col 2: Internal resources (Repositories, Databases, Buckets)
        # Col 3: Critical staging / Canary Decoys
        column_map: Dict[NodeType, int] = {
            NodeType.HUMAN: 0,
            NodeType.SERVICE_ACCOUNT: 0,
            NodeType.CICD_RUNNER: 0,
            NodeType.ROLE: 1,
            NodeType.DEVICE: 1,
            NodeType.REPOSITORY: 2,
            NodeType.DATABASE: 2,
            NodeType.BUCKET: 2,
            NodeType.TICKET: 1,
            NodeType.INCIDENT: 1,
            NodeType.CANARY_DECOY: 3,
            NodeType.GENERIC: 2,
        }

        col_y_counters: Dict[int, float] = {0: 100.0, 1: 100.0, 2: 100.0, 3: 100.0}
        col_x_offsets: Dict[int, float] = {0: 80.0, 1: 340.0, 2: 620.0, 3: 900.0}

        for nd in node_list:
            col = column_map.get(nd.node_type, 2)
            pos_x = col_x_offsets[col]
            pos_y = col_y_counters[col]
            col_y_counters[col] += 120.0

            nodes.append(
                ReactFlowNode(
                    id=nd.node_id,
                    type="customEntityNode",
                    position={"x": pos_x, "y": pos_y},
                    data={
                        "label": nd.label,
                        "node_type": nd.node_type.value,
                        "sensitivity": nd.sensitivity,
                        "is_canary": nd.is_canary,
                        "first_seen": nd.first_seen.isoformat(),
                        "last_seen": nd.last_seen.isoformat(),
                        "attributes": nd.attributes,
                    }
                )
            )

        for ed in edge_list:
            is_canary_trip = ed.edge_type == EdgeType.CANARY_TRIP
            is_high_risk = ed.sensitivity >= 0.8 or is_canary_trip
            
            edges.append(
                ReactFlowEdge(
                    id=ed.edge_id,
                    source=ed.source_id,
                    target=ed.target_id,
                    label=ed.edge_type.value,
                    animated=is_canary_trip or is_high_risk,
                    data={
                        "edge_type": ed.edge_type.value,
                        "timestamp": ed.timestamp.isoformat(),
                        "sensitivity": ed.sensitivity,
                        "confidence": ed.confidence,
                        "event_id": ed.event_id,
                        "attributes": ed.attributes,
                    }
                )
            )

        return ReactFlowGraph(
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges)
        )

    def extract_actor_features(
        self,
        actor_token: str,
        window_start: datetime,
        window_end: datetime
    ) -> ActorFeatureVector:
        """Extracts normalized behavioral feature vector z_t(u) for DevB baseline and drift analysis.
        
        Features:
        1. event_count: Activity volume
        2. unique_resources_count: Breadth of assets accessed
        3. avg_resource_sensitivity: Average sensitivity of targets
        4. max_resource_sensitivity: Peak sensitivity touched
        5. off_hours_ratio: Events outside 08:00 - 18:00 UTC or weekend
        6. action_diversity_entropy: Shannon entropy of action types
        7. nhi_interaction_count: Non-human identity interactions
        """
        edge_ids = self.builder.get_edge_ids_in_window(window_start, window_end)
        actor_edges = [
            self.builder.get_edge(eid)
            for eid in edge_ids
            if self.builder.get_edge(eid) and self.builder.get_edge(eid).source_id == actor_token
        ]

        if not actor_edges:
            return ActorFeatureVector(
                actor_token=actor_token,
                window_start=window_start,
                window_end=window_end,
                event_count=0,
                features=[0.0] * 7
            )

        event_count = len(actor_edges)
        unique_resources = set(e.target_id for e in actor_edges)
        sensitivities = [e.sensitivity for e in actor_edges]
        avg_sens = sum(sensitivities) / event_count
        max_sens = max(sensitivities)

        # Off-hours calculation (outside 08:00 - 18:00 or weekday >= 5)
        off_hours_count = 0
        actions = []
        nhi_interactions = 0

        for e in actor_edges:
            # Check off-hours
            hour = e.timestamp.hour
            weekday = e.timestamp.weekday()
            if hour < 8 or hour >= 18 or weekday >= 5:
                off_hours_count += 1

            actions.append(e.edge_type.value)

            # Check if target is NHI (service account or runner)
            target_node = self.builder.get_node(e.target_id)
            if target_node and target_node.node_type in [NodeType.SERVICE_ACCOUNT, NodeType.CICD_RUNNER]:
                nhi_interactions += 1

        off_hours_ratio = off_hours_count / event_count

        # Action diversity (Shannon entropy)
        action_counts = Counter(actions)
        entropy = 0.0
        for cnt in action_counts.values():
            p = cnt / event_count
            entropy -= p * math.log2(p)

        # Normalized feature array z_t(u) for DevB
        feature_array = [
            round(min(1.0, event_count / 100.0), 4),             # Volume (capped at 100/window)
            round(min(1.0, len(unique_resources) / 20.0), 4),   # Resource breadth (capped at 20)
            round(avg_sens, 4),                                 # Mean sensitivity [0, 1]
            round(max_sens, 4),                                 # Peak sensitivity [0, 1]
            round(off_hours_ratio, 4),                          # Off-hours ratio [0, 1]
            round(min(1.0, entropy / 3.0), 4),                  # Action entropy [0, 1]
            round(min(1.0, nhi_interactions / 10.0), 4)         # NHI ratio [0, 1]
        ]

        return ActorFeatureVector(
            actor_token=actor_token,
            window_start=window_start,
            window_end=window_end,
            event_count=event_count,
            unique_resources_count=len(unique_resources),
            avg_resource_sensitivity=round(avg_sens, 4),
            max_resource_sensitivity=round(max_sens, 4),
            off_hours_ratio=round(off_hours_ratio, 4),
            action_diversity_entropy=round(entropy, 4),
            nhi_interaction_count=nhi_interactions,
            data_volume_score=round(min(1.0, event_count / 50.0), 4),
            features=feature_array
        )

    def extract_behavioral_vector(
        self,
        actor_token: str,
        window_start: datetime,
        window_end: datetime,
        historical_resources: Optional[Set[str]] = None,
        expected_daily_volume: float = 5.0,
    ) -> Any:
        """Extracts DevB's 6-dimensional BehavioralFeatureVector directly from graph state.
        
        Maps graph activity into:
        1. event_volume_rate: normalized frequency relative to expected baseline
        2. resource_sensitivity_mean: average sensitivity of accessed resources in window
        3. new_resource_discovery_ratio: fraction of resources not seen in historical baseline
        4. off_hours_ratio: fraction of operations outside 08:00-18:00 or weekends
        5. action_privilege_intensity: ratio of privileged/sensitive actions (queries, staging, admin)
        6. cross_boundary_entropy: dispersion across distinct service/resource domains
        """
        from backend.drift.schemas import BehavioralFeatureVector

        edge_ids = self.builder.get_edge_ids_in_window(window_start, window_end)
        actor_edges = [
            self.builder.get_edge(eid)
            for eid in edge_ids
            if self.builder.get_edge(eid) and self.builder.get_edge(eid).source_id == actor_token
        ]

        if not actor_edges:
            return BehavioralFeatureVector(
                event_volume_rate=0.0,
                resource_sensitivity_mean=0.0,
                new_resource_discovery_ratio=0.0,
                off_hours_ratio=0.0,
                action_privilege_intensity=0.0,
                cross_boundary_entropy=0.0,
            )

        event_count = len(actor_edges)
        volume_rate = round(event_count / expected_daily_volume, 4)

        sensitivities = [e.sensitivity for e in actor_edges]
        avg_sens = round(sum(sensitivities) / event_count, 4)

        current_resources = set(e.target_id for e in actor_edges)
        if historical_resources is not None and current_resources:
            new_res = current_resources - historical_resources
            new_res_ratio = round(len(new_res) / len(current_resources), 4)
        else:
            new_res_ratio = 0.0

        off_hours_count = sum(
            1 for e in actor_edges
            if e.timestamp.hour < 8 or e.timestamp.hour >= 18 or e.timestamp.weekday() >= 5
        )
        off_hours_ratio = round(off_hours_count / event_count, 4)

        # Privileged actions: queries on sensitive data, staging, role assumptions, modifications
        privileged_types = {EdgeType.QUERIED, EdgeType.STAGED, EdgeType.EXFILTRATED, EdgeType.ASSUMED_ROLE, EdgeType.MODIFIED, EdgeType.CANARY_TRIP}
        privileged_count = sum(
            1 for e in actor_edges
            if e.edge_type in privileged_types or e.sensitivity >= 0.7
        )
        privilege_intensity = round(privileged_count / event_count, 4)

        # Cross-boundary entropy: distinct resource prefixes/types
        domains = [e.target_id.split(":")[0] if ":" in e.target_id else "generic" for e in actor_edges]
        domain_counts = Counter(domains)
        entropy = 0.0
        for cnt in domain_counts.values():
            p = cnt / event_count
            entropy -= p * math.log2(p)

        return BehavioralFeatureVector(
            event_volume_rate=volume_rate,
            resource_sensitivity_mean=avg_sens,
            new_resource_discovery_ratio=new_res_ratio,
            off_hours_ratio=off_hours_ratio,
            action_privilege_intensity=privilege_intensity,
            cross_boundary_entropy=round(entropy, 4),
        )

