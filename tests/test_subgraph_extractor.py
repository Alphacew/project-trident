"""Unit tests for DevA: Time-Window and Ego-Network Subgraph Extractor."""

from datetime import datetime, timezone, timedelta
import pytest

from backend.graph.schemas import EdgeType, NodeType
from backend.graph.subgraph_extractor import TimeWindowExtractor
from backend.graph.temporal_graph import TemporalGraphBuilder


@pytest.fixture
def populated_graph():
    builder = TemporalGraphBuilder()
    t0 = datetime(2026, 9, 10, 0, 0, 0, tzinfo=timezone.utc)

    # Actor nodes
    builder.add_node("Subject-Theta-482", NodeType.HUMAN)
    builder.add_node("Subject-Beta-102", NodeType.HUMAN)

    # Resource nodes
    builder.add_node("db:customers", NodeType.DATABASE, sensitivity=0.8)
    builder.add_node("repo:auth", NodeType.REPOSITORY, sensitivity=0.5)
    builder.add_node("arn:s3:staging", NodeType.BUCKET, sensitivity=0.6)
    builder.add_node("bucket:canary-decoy", NodeType.CANARY_DECOY, is_canary=True, sensitivity=1.0)

    # Day 1: Subject-Theta touches repo
    builder.add_edge("Subject-Theta-482", "repo:auth", EdgeType.ACCESSED, t0 + timedelta(days=1))

    # Day 5: Subject-Theta touches db
    builder.add_edge("Subject-Theta-482", "db:customers", EdgeType.QUERIED, t0 + timedelta(days=5))

    # Day 8: Subject-Beta touches db
    builder.add_edge("Subject-Beta-102", "db:customers", EdgeType.QUERIED, t0 + timedelta(days=8))

    # Day 10: Subject-Theta touches staging
    builder.add_edge("Subject-Theta-482", "arn:s3:staging", EdgeType.STAGED, t0 + timedelta(days=10))

    # Day 13: Subject-Theta touches canary decoy
    builder.add_edge("Subject-Theta-482", "bucket:canary-decoy", EdgeType.CANARY_TRIP, t0 + timedelta(days=13))

    return builder, t0


def test_sliding_window_extraction(populated_graph):
    """Verify time window extraction includes only events within [t_start, t_end]."""
    builder, t0 = populated_graph
    extractor = TimeWindowExtractor(builder)

    # Extract Days 4 to 9 (should capture Day 5 and Day 8 edges only)
    w_start = t0 + timedelta(days=4)
    w_end = t0 + timedelta(days=9)
    sub = extractor.extract_window(w_start, w_end)

    assert sub.edge_count == 2
    # Verify nodes present are only those involved in the window
    node_ids = set(n.node_id for n in sub.get_all_nodes())
    assert "Subject-Theta-482" in node_ids
    assert "Subject-Beta-102" in node_ids
    assert "db:customers" in node_ids
    assert "bucket:canary-decoy" not in node_ids  # Day 13 outside window


def test_ego_subgraph_extraction(populated_graph):
    """Verify ego-network extraction captures causal neighborhood around seed actor."""
    builder, t0 = populated_graph
    extractor = TimeWindowExtractor(builder)

    # Extract 1-hop ego network for Subject-Theta-482
    ego = extractor.extract_ego_subgraph("Subject-Theta-482", hops=1)
    ego_nodes = set(n.node_id for n in ego.get_all_nodes())

    assert "Subject-Theta-482" in ego_nodes
    assert "repo:auth" in ego_nodes
    assert "db:customers" in ego_nodes
    assert "arn:s3:staging" in ego_nodes
    assert "bucket:canary-decoy" in ego_nodes
    assert "Subject-Beta-102" not in ego_nodes  # Beta is not directly connected to Theta in 1 hop


def test_react_flow_serialization(populated_graph):
    """Verify serialization into React Flow schema with styled nodes and edges."""
    builder, t0 = populated_graph
    extractor = TimeWindowExtractor(builder)

    rf_graph = extractor.to_react_flow()

    assert rf_graph.total_nodes == 6
    assert rf_graph.total_edges == 5

    # Check node structure
    sample_node = next(n for n in rf_graph.nodes if n.id == "bucket:canary-decoy")
    assert sample_node.type == "customEntityNode"
    assert sample_node.data["is_canary"] is True
    assert "x" in sample_node.position and "y" in sample_node.position

    # Check edge structure & canary animation
    canary_edge = next(e for e in rf_graph.edges if e.target == "bucket:canary-decoy")
    assert canary_edge.label == "CANARY_TRIP"
    assert canary_edge.animated is True
