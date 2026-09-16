"""Unit tests for DevA: NetworkX Temporal Graph Builder."""

from datetime import datetime, timezone, timedelta
import pytest

from backend.common.schemas import (
    ActorContext,
    CanonicalEvent,
    EventType,
    IdentityType,
    ResourceContext,
)
from backend.graph.schemas import EdgeType, NodeType
from backend.graph.temporal_graph import (
    ProtectedEndpointIngestionViolation,
    TemporalGraphBuilder,
)


@pytest.fixture
def graph_builder():
    return TemporalGraphBuilder()


@pytest.fixture
def base_time():
    return datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc)


def test_node_types_creation(graph_builder, base_time):
    """Verify builder creates Human, ServiceAccount, CICDRunner, DB, Bucket, Repo, and Canary nodes."""
    n_human = graph_builder.add_node("Subject-Theta-482", NodeType.HUMAN, timestamp=base_time)
    n_sa = graph_builder.add_node("ServiceAccount-Echo-101", NodeType.SERVICE_ACCOUNT, timestamp=base_time)
    n_runner = graph_builder.add_node("Runner-Zeta-99", NodeType.CICD_RUNNER, timestamp=base_time)
    n_db = graph_builder.add_node("db:prod-customers", NodeType.DATABASE, sensitivity=0.9, timestamp=base_time)
    n_bucket = graph_builder.add_node("arn:aws:s3:::corp-raw-data", NodeType.BUCKET, sensitivity=0.6, timestamp=base_time)
    n_repo = graph_builder.add_node("repo:github.com/corp/auth-service", NodeType.REPOSITORY, sensitivity=0.7, timestamp=base_time)
    n_canary = graph_builder.add_node("bucket:canary-payroll-decoy", NodeType.CANARY_DECOY, is_canary=True, timestamp=base_time)

    assert graph_builder.node_count == 7
    assert n_human.node_type == NodeType.HUMAN
    assert n_sa.node_type == NodeType.SERVICE_ACCOUNT
    assert n_runner.node_type == NodeType.CICD_RUNNER
    assert n_db.node_type == NodeType.DATABASE
    assert n_bucket.node_type == NodeType.BUCKET
    assert n_repo.node_type == NodeType.REPOSITORY
    assert n_canary.is_canary is True


def test_edge_persistence_with_metadata(graph_builder, base_time):
    """Verify temporal edges retain timestamp, type, confidence, and sensitivity."""
    edge1 = graph_builder.add_edge(
        source_id="Subject-Theta-482",
        target_id="db:prod-customers",
        edge_type=EdgeType.QUERIED,
        timestamp=base_time,
        sensitivity=0.9,
        confidence=0.95,
        event_id="EVT-001"
    )

    edge2 = graph_builder.add_edge(
        source_id="Subject-Theta-482",
        target_id="arn:aws:s3:::corp-raw-data",
        edge_type=EdgeType.ACCESSED,
        timestamp=base_time + timedelta(minutes=15),
        sensitivity=0.6,
        confidence=1.0,
        event_id="EVT-002"
    )

    assert graph_builder.edge_count == 2
    assert edge1.edge_type == EdgeType.QUERIED
    assert edge1.sensitivity == 0.9
    assert edge1.confidence == 0.95
    assert edge1.event_id == "EVT-001"

    # Verify edge retrieval from NetworkX graph
    nx_edge = graph_builder.graph.get_edge_data("Subject-Theta-482", "db:prod-customers", key=edge1.edge_id)
    assert nx_edge["edge_type"] == EdgeType.QUERIED.value
    assert nx_edge["event_id"] == "EVT-001"


def test_canonical_event_ingestion(graph_builder, base_time):
    """Verify ingesting a DevA CanonicalEvent resolves nodes and edge automatically."""
    event = CanonicalEvent(
        event_id="EVT-S3-INGEST",
        timestamp=base_time,
        event_type=EventType.DATA_ACCESS,
        action="s3:GetObject",
        actor=ActorContext(
            actor_token="Subject-Foxtrot-707",
            identity_type=IdentityType.HUMAN,
            role="DataScientist",
            department="Analytics"
        ),
        resource=ResourceContext(
            resource_id="arn:aws:s3:::analytics-lake/raw.parquet",
            resource_type="Bucket",
            sensitivity=0.75
        ),
        raw_payload_hash="testhash777",
        source_system="aws_cloudtrail"
    )

    edge = graph_builder.add_canonical_event(event)

    assert edge.source_id == "Subject-Foxtrot-707"
    assert edge.target_id == "arn:aws:s3:::analytics-lake/raw.parquet"
    assert edge.sensitivity == 0.75
    assert edge.event_id == "EVT-S3-INGEST"

    actor_node = graph_builder.get_node("Subject-Foxtrot-707")
    res_node = graph_builder.get_node("arn:aws:s3:::analytics-lake/raw.parquet")

    assert actor_node is not None
    assert actor_node.node_type == NodeType.HUMAN
    assert actor_node.attributes["role"] == "DataScientist"
    assert res_node is not None
    assert res_node.node_type == NodeType.BUCKET


def test_protected_endpoint_defense_in_depth_invariant(graph_builder, base_time):
    """INVARIANT 1: Graph builder must forbid nodes or edges touching protected endpoints."""
    # Attempt to insert whistleblower URL as node
    with pytest.raises(ProtectedEndpointIngestionViolation) as excinfo:
        graph_builder.add_node("https://whistleblower.internal.corp/case/1", NodeType.GENERIC)
    assert "Protected whistleblower/ethics endpoints must never enter the temporal graph" in str(excinfo.value)

    # Attempt to insert ombudsman email as edge target
    with pytest.raises(ProtectedEndpointIngestionViolation) as excinfo2:
        graph_builder.add_edge(
            source_id="Subject-Theta-482",
            target_id="mailto:ombudsman@corp.internal",
            edge_type=EdgeType.CONNECTED_TO,
            timestamp=base_time
        )
    assert "ombuds" in str(excinfo2.value).lower()
