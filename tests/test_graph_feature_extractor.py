"""Unit tests for DevA: Behavioral Feature Extractor (Contract with DevB)."""

from datetime import datetime, timezone, timedelta
import pytest

from backend.graph.schemas import EdgeType, NodeType
from backend.graph.subgraph_extractor import TimeWindowExtractor
from backend.graph.temporal_graph import TemporalGraphBuilder


@pytest.fixture
def behavioral_graph():
    builder = TemporalGraphBuilder()
    # Wednesday 10:00 UTC (business hours)
    t0 = datetime(2026, 9, 16, 10, 0, 0, tzinfo=timezone.utc)

    # Actor: Subject-Theta-482
    builder.add_node("Subject-Theta-482", NodeType.HUMAN)
    builder.add_node("ServiceAccount-Deployer", NodeType.SERVICE_ACCOUNT)
    builder.add_node("db:prod-finance", NodeType.DATABASE, sensitivity=0.9)
    builder.add_node("repo:frontend", NodeType.REPOSITORY, sensitivity=0.3)

    # Event 1: Normal business hours repo access
    builder.add_edge("Subject-Theta-482", "repo:frontend", EdgeType.ACCESSED, t0, sensitivity=0.3)

    # Event 2: Off-hours sensitive DB query (23:30 UTC)
    t_off = t0.replace(hour=23, minute=30)
    builder.add_edge("Subject-Theta-482", "db:prod-finance", EdgeType.QUERIED, t_off, sensitivity=0.9)

    # Event 3: NHI interaction with service account
    builder.add_edge("Subject-Theta-482", "ServiceAccount-Deployer", EdgeType.ASSUMED_ROLE, t0 + timedelta(hours=2), sensitivity=0.8)

    return builder, t0


def test_actor_feature_vector_extraction(behavioral_graph):
    """Verify extraction of normalized feature vector z_t(u) for DevB."""
    builder, t0 = behavioral_graph
    extractor = TimeWindowExtractor(builder)

    w_start = t0 - timedelta(hours=1)
    w_end = t0 + timedelta(days=1)

    features = extractor.extract_actor_features("Subject-Theta-482", w_start, w_end)

    assert features.actor_token == "Subject-Theta-482"
    assert features.event_count == 3
    assert features.unique_resources_count == 3
    assert features.max_resource_sensitivity == 0.9
    assert abs(features.avg_resource_sensitivity - (0.3 + 0.9 + 0.8) / 3.0) < 1e-4

    # Off-hours: 1 out of 3 events occurred at 23:30 UTC (off_hours_ratio = 1/3)
    assert abs(features.off_hours_ratio - 1.0 / 3.0) < 0.01

    # NHI interaction: 1 interaction with ServiceAccount
    assert features.nhi_interaction_count == 1

    # Check numeric feature array for DevB
    assert len(features.features) == 7
    # All features in vector are normalized floats
    for val in features.features:
        assert isinstance(val, float)
        assert 0.0 <= val <= 1.0


def test_empty_window_yields_zero_vector(behavioral_graph):
    """Verify inactive actors receive zero-filled feature vectors."""
    builder, t0 = behavioral_graph
    extractor = TimeWindowExtractor(builder)

    # Query a future window where no activity occurred
    w_start = t0 + timedelta(days=50)
    w_end = t0 + timedelta(days=51)

    features = extractor.extract_actor_features("Subject-Theta-482", w_start, w_end)

    assert features.event_count == 0
    assert features.features == [0.0] * 7
