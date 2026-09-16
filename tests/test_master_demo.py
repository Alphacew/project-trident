"""Project TRIDENT — Test Suite for Master 14-Day Demo Dataset.

Verifies the six hackathon demo beats:
- Days 1–4: Baseline activity
- Day 5 (Beat 2): Benign anomaly suppressed via valid Jira ticket
- Day 9 (Beat 2): Silent unanchored drift begins to accumulate
- Day 10 (Beat 3): Fabricated Jira ticket (CAS low, unsuppressed)
- Day 12 (Beat 4): Sensitive staging to temporary memory mount
- Day 13 (Beat 4): Simulated canary trip transitions state to CONFIRMED
- Day 14 (Beat 5): Tier 4 escalation with full MITRE progression chain
"""

import pytest
from backend.drift.schemas import TrajectoryState
from backend.risk.schemas import RiskTier
from backend.scenarios.generator import EnterpriseScenarioGenerator
from backend.scenarios.master_demo import MasterDemoDatasetBuilder


@pytest.fixture
def master_dataset():
    return MasterDemoDatasetBuilder().build()


@pytest.fixture
def scenario_runner():
    return EnterpriseScenarioGenerator()


def test_master_demo_14_day_beats(master_dataset, scenario_runner):
    """Verifies all six demo beats execute cleanly across the 14-day timeline."""
    result = scenario_runner.run_scenario(master_dataset)

    assert result.metadata.scenario_id == "MASTER_DEMO"
    assert len(result.daily_snapshots) == 14

    snaps = result.daily_snapshots

    # 1. Day 1: Baseline is STABLE and TIER 1
    assert snaps[0].trajectory_state == TrajectoryState.STABLE
    assert snaps[0].risk_tier == RiskTier.TIER_1_CONTEXTUAL_DRIFT

    # 2. Day 5 (Beat 2): Benign Anomaly Suppressed
    # Legitimate project ticket JIRA-PROJ-841
    day5 = snaps[4]
    assert day5.context_authenticity_score >= 0.70
    assert day5.discount_factor <= 0.40
    assert day5.risk_tier in [RiskTier.TIER_1_CONTEXTUAL_DRIFT, RiskTier.TIER_2_UNANCHORED_EXPLORATION]

    # 3. Day 9 (Beat 2): Silent Drift Begins
    day9 = snaps[8]
    assert day9.discount_factor == 1.0  # No anchor ticket
    assert day9.cusum_drift_score > snaps[3].cusum_drift_score

    # 4. Day 10 (Beat 3): Fabricated Jira Context Detection
    # JIRA-FAB-841 created 4 mins prior, self-approved, ghost ticket
    day10 = snaps[9]
    assert day10.context_authenticity_score <= 0.30
    assert day10.discount_factor >= 0.75  # Suppression denied!
    assert day10.risk_tier in [RiskTier.TIER_3_HIGH_RISK_TRAJECTORY, RiskTier.TIER_4_CRITICAL]

    # 5. Day 13 (Beat 4): Canary trip
    day13 = snaps[12]
    assert day13.canary_state == "CONFIRMED"

    # 6. Day 14 (Beat 5): Escalation
    day14 = snaps[13]
    assert day14.risk_tier == RiskTier.TIER_4_CRITICAL
    assert day14.cusum_drift_score >= 2.0
    assert any("T1078" in t for t in day14.active_mitre_tactics)
    assert any("T1005" in t for t in day14.active_mitre_tactics)
    assert any("T1567" in t for t in day14.active_mitre_tactics)
