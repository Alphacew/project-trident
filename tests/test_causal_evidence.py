"""Project TRIDENT — Test Suite for Causal Evidence Engine & Canary Deception.

Verifies:
1. Minimal causal evidence subgraph extraction from temporal graph
2. Causal attack chain sequencing (Credential/Discovery -> Sensitive Access -> Staging -> Canary -> Exfil)
3. React Flow node positioning and animated edge attributes for Screen 2
4. Simulated canary state machine (UNCONFIRMED -> PREDICTED -> CONFIRMED)
"""

from datetime import datetime, timezone
import pytest

from backend.evidence.canary import SimulatedCanaryEngine
from backend.evidence.causal_extractor import MinimalCausalExtractor
from backend.evidence.schemas import EvidenceConfirmationState, ProgressionStage
from backend.graph.schemas import EdgeType, NodeType
from backend.graph.temporal_graph import TemporalGraphBuilder
from backend.scenarios.master_demo import MasterDemoDatasetBuilder


@pytest.fixture
def master_dataset():
    return MasterDemoDatasetBuilder().build()


@pytest.fixture
def populated_graph(master_dataset):
    builder = TemporalGraphBuilder()
    for res in master_dataset.historical_resources:
        builder.add_node(res, NodeType.REPOSITORY, sensitivity=0.25)
    for evt in master_dataset.events:
        builder.add_canonical_event(evt)
    return builder


def test_minimal_causal_chain_extraction(populated_graph):
    """Verifies that causal chain isolates progression steps from credential/discovery to exfil."""
    actor_token = "Subject-Theta-482"
    extractor = MinimalCausalExtractor(populated_graph)
    payload = extractor.extract_causal_chain(actor_token=actor_token, min_sensitivity=0.35)

    assert payload.actor_token == actor_token
    assert payload.attack_path_length >= 5
    assert len(payload.nodes) >= 5
    assert len(payload.edges) >= 5
    assert payload.confirmation_state == EvidenceConfirmationState.CONFIRMED

    # Check that sequence is ordered chronologically
    for i in range(len(payload.progression_steps) - 1):
        assert payload.progression_steps[i].timestamp <= payload.progression_steps[i + 1].timestamp
        assert payload.progression_steps[i].step_number == i + 1

    # Verify stage progression presence
    stages = [s.stage for s in payload.progression_steps]
    assert ProgressionStage.DISCOVERY in stages or ProgressionStage.SENSITIVE_ACCESS in stages
    assert ProgressionStage.STAGING in stages
    assert ProgressionStage.CANARY_TRIP in stages
    assert ProgressionStage.EXFILTRATION in stages

    # Check React Flow serialization formatting
    for node in payload.nodes:
        assert "x" in node.position and "y" in node.position
        assert node.position["x"] > 0
        assert "node_id" in node.data

    # Check that high-risk and canary edges are animated in red
    canary_edges = [e for e in payload.edges if "canary" in e.target.lower()]
    assert len(canary_edges) >= 1
    assert canary_edges[0].animated is True
    assert canary_edges[0].style["stroke"] == "#dc2626"


def test_simulated_canary_state_machine():
    """Verifies canary decoy state transitions: UNCONFIRMED -> PREDICTED -> CONFIRMED."""
    engine = SimulatedCanaryEngine()
    canary_res = "arn:aws:s3:::canary-decoy-payroll-backup"

    # Initial state
    canary = engine.get_canary(canary_res)
    assert canary is not None
    assert canary.confirmation_state == EvidenceConfirmationState.UNCONFIRMED
    assert canary.is_tripped is False
    assert canary.claim_label == "Simulated Canary"

    # Target prediction
    predicted = engine.predict_target("Subject-Theta-482", canary_res)
    assert predicted.confirmation_state == EvidenceConfirmationState.PREDICTED
    assert predicted.predicted_threat_actor == "Subject-Theta-482"

    # Trip confirmation
    now = datetime.now(timezone.utc)
    tripped = engine.trigger_trip(canary_res, "Subject-Theta-482", timestamp=now)
    assert tripped.is_tripped is True
    assert tripped.confirmation_state == EvidenceConfirmationState.CONFIRMED
    assert tripped.trip_timestamp == now
