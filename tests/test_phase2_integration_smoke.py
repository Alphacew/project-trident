"""Project TRIDENT — Git Sync Checkpoint 2: Phase 2 Integration Smoke Test.

Validates:
DevB runs CUSUM drift and composite risk calculations directly against
DevA's temporal NetworkX graph state using simulated multi-day activity,
confirming low-and-slow drift triggers Tier 3 escalation.
"""

from datetime import datetime, timedelta, timezone
import pytest

from backend.drift.cusum import CUSUMDriftEngine
from backend.drift.schemas import TrajectoryState
from backend.graph.schemas import EdgeType, NodeType
from backend.graph.subgraph_extractor import TimeWindowExtractor
from backend.graph.temporal_graph import TemporalGraphBuilder
from backend.risk.composite import CompositeRiskCalculator
from backend.risk.schemas import RiskTier


@pytest.fixture
def graph_builder():
    return TemporalGraphBuilder()


@pytest.fixture
def drift_engine():
    engine = CUSUMDriftEngine()
    return engine


@pytest.fixture
def risk_calculator():
    return CompositeRiskCalculator()


@pytest.fixture
def start_timestamp():
    return datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc)


def test_phase2_integration_smoke_low_and_slow_tier3_escalation(
    graph_builder,
    drift_engine,
    risk_calculator,
    start_timestamp,
):
    """Git Sync Checkpoint 2 Integration Smoke Test:
    Simulates 14 days of enterprise activity in DevA's NetworkX temporal graph.
    DevB evaluates CUSUM drift and Composite Risk directly from graph state.
    Proves that 14 days of low-and-slow unanchored activity triggers Tier 3 escalation.
    """
    actor_token = "Subject-Theta-482"
    drift_engine.reset_actor_state(actor_token)

    # 1. Register Subject in Graph
    graph_builder.add_node(
        node_id=actor_token,
        node_type=NodeType.HUMAN,
        label="Engineering Lead",
        timestamp=start_timestamp,
        attributes={"department": "Engineering", "peer_group": "Engineering-Backend"}
    )

    # Set of known historical baseline resources
    historical_resources = {
        "repo:corp/frontend-app",
        "repo:corp/backend-api",
        "repo:corp/shared-components",
        "repo:corp/docs"
    }

    for res in historical_resources:
        graph_builder.add_node(res, NodeType.REPOSITORY, sensitivity=0.25, timestamp=start_timestamp)

    # -------------------------------------------------------------------------
    # Days 1–3: Benign Baseline Activity in Graph
    # -------------------------------------------------------------------------
    for day in range(1, 4):
        day_date = start_timestamp + timedelta(days=day)
        # Normal queries to baseline repos during business hours
        for i, res in enumerate(historical_resources):
            graph_builder.add_edge(
                source_id=actor_token,
                target_id=res,
                edge_type=EdgeType.ACCESSED,
                timestamp=day_date.replace(hour=10 + i, minute=15),
                sensitivity=0.25,
                confidence=1.0,
                event_id=f"EVT-BASELINE-D{day}-{i}"
            )

    # -------------------------------------------------------------------------
    # Days 4–14: Low-and-Slow Insider Activity (Scenario B)
    # Each day, queries sensitive unassigned databases without any ticket anchor
    # -------------------------------------------------------------------------
    sensitive_targets = [
        ("db:customer-pii-shard-01", 0.85),
        ("db:customer-pii-shard-02", 0.85),
        ("db:eu-payroll-records", 0.95),
        ("arn:aws:s3:::internal-financial-forecasts", 0.80),
        ("arn:aws:s3:::corp-m-and-a-deal-docs", 0.90),
        ("db:executive-compensation-ledger", 0.95),
        ("arn:aws:s3:::cryptographic-keys-backup", 0.95),
        ("db:customer-passwords-hashed", 0.95),
        ("arn:aws:s3:::prod-customer-contracts", 0.85),
        ("db:legal-dispute-settlements", 0.90),
        ("bucket:corp-staging-mount", 0.85),
    ]

    for day_idx, (target_res, sens) in enumerate(sensitive_targets, start=4):
        day_date = start_timestamp + timedelta(days=day_idx)
        # Add target node
        graph_builder.add_node(
            target_res,
            NodeType.DATABASE if "db:" in target_res else NodeType.BUCKET,
            sensitivity=sens,
            timestamp=day_date
        )
        # 3 to 4 low-and-slow queries on sensitive resource
        for q in range(3):
            graph_builder.add_edge(
                source_id=actor_token,
                target_id=target_res,
                edge_type=EdgeType.QUERIED if "db:" in target_res else EdgeType.ACCESSED,
                timestamp=day_date.replace(hour=19 + q, minute=20),  # Off-hours!
                sensitivity=sens,
                confidence=1.0,
                event_id=f"EVT-SLOW-D{day_idx}-{q}"
            )

    # -------------------------------------------------------------------------
    # DevB Evaluates Graph State across the 14-Day Timeline
    # -------------------------------------------------------------------------
    extractor = TimeWindowExtractor(graph_builder)

    daily_reports = []
    daily_risks = []

    for day in range(1, 15):
        day_start = start_timestamp + timedelta(days=day, hours=0, minutes=0)
        day_end = start_timestamp + timedelta(days=day, hours=23, minutes=59)

        # DevA extracts BehavioralFeatureVector directly from NetworkX graph
        b_vec = extractor.extract_behavioral_vector(
            actor_token=actor_token,
            window_start=day_start,
            window_end=day_end,
            historical_resources=historical_resources,
            expected_daily_volume=4.0
        )

        # Unanchored activity (no ticket anchor): delta = 1.0 (zero discount, 100% risk)
        discount_factor = 1.0
        anchor_score = 0.0

        # DevB updates CUSUM drift accumulator
        drift_rep = drift_engine.update(
            actor_token=actor_token,
            current_vector=b_vec,
            discount_factor=discount_factor,
            timestamp=day_end
        )
        daily_reports.append(drift_rep)

        # DevB computes Composite Risk
        # Anomaly score correlates with displacement from baseline
        anomaly_score = min(1.0, max(0.1, drift_rep.displacement_raw / 1.5))
        risk_res = risk_calculator.evaluate(
            actor_token=actor_token,
            anomaly_score=anomaly_score,
            anchor_score=anchor_score,
            discount_factor=discount_factor,
            cumulative_drift_score=drift_rep.normalized_drift_score,
            resource_criticality=b_vec.resource_sensitivity_mean or 0.25,
            identity_type="Human",
            timestamp=day_end
        )
        daily_risks.append(risk_res)

    # -------------------------------------------------------------------------
    # Verification of Core Behavioral Invariants & Escalation
    # -------------------------------------------------------------------------
    # 1. Day 1: Baseline activity must be STABLE and TIER 1
    assert daily_reports[0].trajectory_state == TrajectoryState.STABLE
    assert daily_reports[0].cusum_drift_score < 0.5
    assert daily_risks[0].risk_tier == RiskTier.TIER_1_CONTEXTUAL_DRIFT

    # 2. Cumulative drift must monotonically increase during unanchored exploration
    assert daily_reports[-1].cusum_drift_score > daily_reports[3].cusum_drift_score

    # 3. Final Day (Day 14): CUSUM drift exceeds High-Risk threshold (tau >= 2.0)
    final_drift = daily_reports[-1]
    final_risk = daily_risks[-1]

    print(f"\n[Smoke Test Results]")
    print(f"  Day 1:  CUSUM={daily_reports[0].cusum_drift_score:.2f}, State={daily_reports[0].trajectory_state.value}, Risk={daily_risks[0].composite_risk} ({daily_risks[0].risk_tier.value})")
    print(f"  Day 7:  CUSUM={daily_reports[6].cusum_drift_score:.2f}, State={daily_reports[6].trajectory_state.value}, Risk={daily_risks[6].composite_risk} ({daily_risks[6].risk_tier.value})")
    print(f"  Day 14: CUSUM={final_drift.cusum_drift_score:.2f}, State={final_drift.trajectory_state.value}, Risk={final_risk.composite_risk} ({final_risk.risk_tier.value})")

    assert final_drift.cusum_drift_score >= drift_engine.tau_high_risk, (
        f"Expected CUSUM >= {drift_engine.tau_high_risk}, got {final_drift.cusum_drift_score}"
    )
    assert final_drift.trajectory_state in [
        TrajectoryState.HIGH_RISK_TRAJECTORY,
        TrajectoryState.CRITICAL,
    ]

    # 4. Proves low-and-slow drift triggers Tier 3 escalation
    assert final_risk.risk_tier in [
        RiskTier.TIER_3_HIGH_RISK_TRAJECTORY,
        RiskTier.TIER_4_CRITICAL,
    ], f"Expected Tier 3 or Tier 4 escalation, got {final_risk.risk_tier}"

    # Confirm action directives and MITRE mappings
    assert "High-Risk Trajectory" in final_risk.recommended_action or "CRITICAL THREAT" in final_risk.recommended_action
    assert any("T1078" in t for t in final_risk.mitre_tactics)
    assert any("T1005" in t for t in final_risk.mitre_tactics)
