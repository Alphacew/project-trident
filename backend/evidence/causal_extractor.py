"""Project TRIDENT — Minimal Causal Evidence Subgraph Extractor.

Extracts the minimal directed acyclic causal chain from the enterprise graph:
Credential Anomaly -> Privilege Escalation -> Discovery -> Sensitive Access -> Staging -> Canary Trip / Exfiltration

Prunes background noise and formats the minimal causal subgraph for React Flow (Screen 2).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from backend.evidence.mitre_mapper import DeterministicMitreMapper
from backend.evidence.schemas import (
    CausalSubgraphPayload,
    EvidenceConfirmationState,
    ProgressionStage,
    ProgressionStep,
)
from backend.graph.schemas import (
    EdgeType,
    NodeType,
    ReactFlowEdge,
    ReactFlowNode,
)
from backend.graph.temporal_graph import TemporalGraphBuilder


class MinimalCausalExtractor:
    """Extracts pruned causal evidence subgraphs isolating attack chains."""

    def __init__(self, builder: TemporalGraphBuilder):
        self.builder = builder
        self.mitre_mapper = DeterministicMitreMapper()

    def _classify_stage(self, edge_type: EdgeType, target_id: str, sensitivity: float, is_canary: bool) -> ProgressionStage:
        if is_canary or edge_type == EdgeType.CANARY_TRIP:
            return ProgressionStage.CANARY_TRIP
        if edge_type == EdgeType.EXFILTRATED or "exfil" in target_id.lower():
            return ProgressionStage.EXFILTRATION
        if edge_type == EdgeType.STAGED or "staging" in target_id.lower() or "tmpfs" in target_id.lower():
            return ProgressionStage.STAGING
        if edge_type == EdgeType.ASSUMED_ROLE or "role" in target_id.lower() or "iam" in target_id.lower():
            return ProgressionStage.PRIVILEGE_ESCALATION
        if edge_type == EdgeType.QUERIED or ("db:" in target_id and sensitivity >= 0.7):
            return ProgressionStage.SENSITIVE_ACCESS
        if edge_type == EdgeType.ACCESSED and sensitivity >= 0.5:
            return ProgressionStage.DISCOVERY
        if edge_type == EdgeType.AUTHENTICATED:
            return ProgressionStage.CREDENTIAL_ANOMALY
        return ProgressionStage.DISCOVERY

    def extract_causal_chain(
        self,
        actor_token: str,
        t_start: Optional[datetime] = None,
        t_end: Optional[datetime] = None,
        min_sensitivity: float = 0.40,
    ) -> CausalSubgraphPayload:
        """Extracts the ordered progression chain and serialized React Flow graph."""
        # 1. Collect all edges involving the actor
        g = self.builder.graph
        if actor_token not in self.builder._nodes_by_id:
            return CausalSubgraphPayload(
                actor_token=actor_token,
                nodes=[],
                edges=[],
                progression_steps=[],
                attack_path_length=0,
                confirmation_state=EvidenceConfirmationState.UNCONFIRMED,
            )

        edge_keys = self.builder.get_edge_ids_in_window(t_start, t_end)
        candidate_edges = [
            self.builder.get_edge(eid)
            for eid in edge_keys
            if self.builder.get_edge(eid) and self.builder.get_edge(eid).source_id == actor_token
        ]

        # 2. Filter for anomalous / sensitive edges (prune routine low-sensitivity noise)
        anomalous_edges = [
            e for e in candidate_edges
            if e.sensitivity >= min_sensitivity
            or e.edge_type in [EdgeType.ASSUMED_ROLE, EdgeType.QUERIED, EdgeType.STAGED, EdgeType.CANARY_TRIP, EdgeType.EXFILTRATED]
            or (self.builder.get_node(e.target_id) and self.builder.get_node(e.target_id).is_canary)
        ]

        # Sort chronologically
        anomalous_edges.sort(key=lambda x: x.timestamp)

        # 3. Build ProgressionSteps
        progression_steps: List[ProgressionStep] = []
        nodes_in_chain: Set[str] = {actor_token}
        has_canary_trip = False

        for idx, edge in enumerate(anomalous_edges, start=1):
            target_node = self.builder.get_node(edge.target_id)
            is_canary = target_node.is_canary if target_node else False
            if is_canary or edge.edge_type == EdgeType.CANARY_TRIP:
                has_canary_trip = True

            stage = self._classify_stage(edge.edge_type, edge.target_id, edge.sensitivity, is_canary)
            tactic, technique = self.mitre_mapper.map_edge_to_mitre(
                edge.edge_type, edge.target_id, edge.sensitivity, is_canary
            )

            desc = f"Step {idx}: {edge.edge_type.value} on {edge.target_id} (sensitivity {edge.sensitivity:.2f})"
            if is_canary:
                desc = f"Step {idx}: [TRIPPED] Decoy Canary Resource Accessed: {edge.target_id}"

            step = ProgressionStep(
                step_number=idx,
                timestamp=edge.timestamp,
                stage=stage,
                source_node=edge.source_id,
                target_node=edge.target_id,
                action=edge.attributes.get("action", edge.edge_type.value),
                edge_type=edge.edge_type.value,
                mitre_tactic=tactic,
                mitre_technique=technique,
                description=desc,
                confidence=edge.confidence,
                sensitivity=edge.sensitivity,
                event_id=edge.event_id,
            )
            progression_steps.append(step)
            nodes_in_chain.add(edge.target_id)

        # 4. Generate layered React Flow visualization
        rf_nodes: List[ReactFlowNode] = []
        rf_edges: List[ReactFlowEdge] = []

        # Position mapping by node type/role in chain
        def get_col_x(node_id: str) -> float:
            nd = self.builder.get_node(node_id)
            if not nd:
                return 500.0
            if nd.node_type in [NodeType.HUMAN, NodeType.SERVICE_ACCOUNT, NodeType.CICD_RUNNER]:
                return 50.0
            if nd.node_type == NodeType.ROLE:
                return 280.0
            if "repo:" in node_id:
                return 520.0
            if "db:" in node_id:
                return 760.0
            if "staging" in node_id or "tmpfs" in node_id:
                return 1000.0
            if nd.is_canary or "canary" in node_id:
                return 1240.0
            return 1480.0  # Outbound exfil sink

        # Place nodes with vertical offsets per column
        col_counts: Dict[float, int] = {}
        for nid in sorted(nodes_in_chain):
            nd = self.builder.get_node(nid)
            ntype = nd.node_type if nd else NodeType.REPOSITORY
            lbl = nd.label if nd else nid
            sens = nd.sensitivity if nd else 0.5
            is_canary = nd.is_canary if nd else False

            col_x = get_col_x(nid)
            row_idx = col_counts.get(col_x, 0)
            col_counts[col_x] = row_idx + 1
            pos_y = 100.0 + (row_idx * 110.0)

            rf_nodes.append(
                ReactFlowNode(
                    id=nid,
                    node_type=ntype,
                    label=lbl,
                    position={"x": col_x, "y": pos_y},
                    sensitivity=sens,
                    is_canary=is_canary,
                    data={
                        "node_id": nid,
                        "node_type": ntype.value,
                        "sensitivity": sens,
                        "is_canary": is_canary,
                        "badge": "CANARY DECOY" if is_canary else ("ACTOR" if nid == actor_token else f"SENS: {sens:.2f}"),
                    },
                )
            )

        # Connect React Flow edges with progression metadata
        for step in progression_steps:
            edge_id = f"rf-edge-{step.source_node}->{step.target_node}-{step.step_number}"
            is_high_threat = step.sensitivity >= 0.8 or step.stage in [
                ProgressionStage.STAGING,
                ProgressionStage.CANARY_TRIP,
                ProgressionStage.EXFILTRATION,
            ]
            rf_edges.append(
                ReactFlowEdge(
                    id=edge_id,
                    source=step.source_node,
                    target=step.target_node,
                    edge_type=EdgeType(step.edge_type) if step.edge_type in [e.value for e in EdgeType] else EdgeType.ACCESSED,
                    label=f"[{step.step_number}] {step.mitre_technique.split()[0]}",
                    timestamp=step.timestamp,
                    animated=is_high_threat,
                    sensitivity=step.sensitivity,
                    style={"stroke": "#dc2626" if is_high_threat else "#3b82f6", "strokeWidth": 2.5},
                    data={
                        "step_number": step.step_number,
                        "stage": step.stage.value,
                        "mitre_tactic": step.mitre_tactic,
                        "mitre_technique": step.mitre_technique,
                        "timestamp": step.timestamp.isoformat(),
                    },
                )
            )

        conf_state = EvidenceConfirmationState.CONFIRMED if has_canary_trip else (
            EvidenceConfirmationState.PREDICTED if len(progression_steps) >= 3 else EvidenceConfirmationState.UNCONFIRMED
        )

        return CausalSubgraphPayload(
            actor_token=actor_token,
            nodes=rf_nodes,
            edges=rf_edges,
            progression_steps=progression_steps,
            attack_path_length=len(progression_steps),
            confirmation_state=conf_state,
            claim_label="Measured Today",
        )
