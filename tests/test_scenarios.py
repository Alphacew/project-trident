"""Project TRIDENT — Test Suite for Enterprise Scenarios A through E.

Verifies:
1. Scenario A (Role Change): Legitimate context suppresses risk to Tier 1/2.
2. Scenario B (Low-and-Slow): Cumulative unanchored drift drives Tier 3/4 escalation.
3. Scenario C (Fabricated Context): Low CAS fails suppression, risk stays elevated in Tier 3/4.
4. Scenario D (Emergency Incident): Sev-1 incident attenuates off-hours intervention to Tier 1/2.
5. Scenario E (Compromised Service Account): Non-Human Identity multiplier triggers rapid Tier 4 breach.
"""

import pytest
from backend.drift.schemas import TrajectoryState
from backend.risk.schemas import RiskTier
from backend.scenarios.generator import EnterpriseScenarioGenerator


@pytest.fixture
def scenario_gen():
    return EnterpriseScenarioGenerator()


def test_scenario_a_role_change(scenario_gen):
    """Scenario A: Legitimate Role Change with valid manager approval and downstream commits."""
    dataset = scenario_gen.generate_scenario_a_role_change()
    result = scenario_gen.run_scenario(dataset)

    assert result.metadata.scenario_id == "SCENARIO_A"
    assert len(result.daily_snapshots) == 7

    # Day 5 snapshot (after promotion and ticket access)
    day5_snap = result.daily_snapshots[4]
    assert day5_snap.context_authenticity_score >= 0.70
    assert day5_snap.discount_factor <= 0.40  # Meaningful attenuation

    # Final risk must remain suppressed to Tier 1 or Tier 2
    assert result.final_risk_tier in [
        RiskTier.TIER_1_CONTEXTUAL_DRIFT,
        RiskTier.TIER_2_UNANCHORED_EXPLORATION,
    ]
    assert result.final_risk_score < 55.0


def test_scenario_b_low_and_slow(scenario_gen):
    """Scenario B: 14-day low-and-slow insider unanchored activity."""
    dataset = scenario_gen.generate_scenario_b_low_and_slow()
    result = scenario_gen.run_scenario(dataset)

    assert result.metadata.scenario_id == "SCENARIO_B"
    assert len(result.daily_snapshots) == 14

    # Monotonic accumulation of CUSUM drift
    assert result.daily_snapshots[-1].cusum_drift_score > result.daily_snapshots[3].cusum_drift_score
    assert result.final_drift_score >= 2.0  # Exceeds tau_high_risk

    # Escalates to Tier 3 or Tier 4
    assert result.final_risk_tier in [
        RiskTier.TIER_3_HIGH_RISK_TRAJECTORY,
        RiskTier.TIER_4_CRITICAL,
    ]


def test_scenario_c_fabricated_context(scenario_gen):
    """Scenario C: Fabricated ticket created 4 mins prior, self-approved, ghost ticket."""
    dataset = scenario_gen.generate_scenario_c_fabricated_context()
    result = scenario_gen.run_scenario(dataset)

    assert result.metadata.scenario_id == "SCENARIO_C"
    # Day 3 exploit attempt
    day3_snap = result.daily_snapshots[2]

    # Context Authenticity Score drops sharply due to temporal mismatch + self-approval + ghost ticket
    assert day3_snap.context_authenticity_score <= 0.35
    # Discount factor must not attenuate significantly (must stay >= 0.75)
    assert day3_snap.discount_factor >= 0.75

    # Risk fails suppression and remains elevated
    assert result.final_risk_tier in [
        RiskTier.TIER_3_HIGH_RISK_TRAJECTORY,
        RiskTier.TIER_4_CRITICAL,
    ]


def test_scenario_d_emergency_incident(scenario_gen):
    """Scenario D: Sev-1 emergency incident attenuates off-hours activity."""
    dataset = scenario_gen.generate_scenario_d_emergency_incident()
    result = scenario_gen.run_scenario(dataset)

    assert result.metadata.scenario_id == "SCENARIO_D"
    day2_snap = result.daily_snapshots[1]

    # Emergency anchor verified
    assert day2_snap.context_authenticity_score >= 0.70
    assert day2_snap.discount_factor <= 0.40  # Risk strongly attenuated

    # Suppressed from SOC queue
    assert result.final_risk_tier in [
        RiskTier.TIER_1_CONTEXTUAL_DRIFT,
        RiskTier.TIER_2_UNANCHORED_EXPLORATION,
    ]


def test_scenario_e_compromised_service_account(scenario_gen):
    """Scenario E: Non-Human Identity compromise drives accelerated escalation."""
    dataset = scenario_gen.generate_scenario_e_compromised_service_account()
    result = scenario_gen.run_scenario(dataset)

    assert result.metadata.scenario_id == "SCENARIO_E"
    day2_snap = result.daily_snapshots[1]

    # Non-human identity with role assumption and DB dump spikes to Tier 4
    assert result.final_risk_tier == RiskTier.TIER_4_CRITICAL
    assert day2_snap.composite_risk >= 75.0
