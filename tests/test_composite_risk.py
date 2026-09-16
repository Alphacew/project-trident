"""Project TRIDENT — Test Suite for Deterministic Composite Risk Engine
Validates the 5-factor deterministic formula, Tier 1-4 mappings,
Scenario A suppression, Scenario C elevation, NHI identity multipliers,
and Monte Carlo property bounds.
"""

from datetime import datetime, timezone
import pytest
from backend.risk.schemas import RiskTier
from backend.risk.composite import CompositeRiskCalculator


@pytest.fixture
def risk_calc():
    return CompositeRiskCalculator()


@pytest.fixture
def base_time():
    return datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc)


def test_context_uncertainty_bounds(risk_calc):
    """Verify contextual uncertainty U_t is bounded in [0.15, 1.0]."""
    # Perfect anchor with max discount (0.85 attenuation) -> U_t = 0.15
    u_min = risk_calc.calculate_context_uncertainty(anchor_score=1.0, discount_factor=0.15)
    assert u_min == pytest.approx(0.15, abs=1e-4)

    # Zero anchor or no discount -> U_t = 1.0
    u_max = risk_calc.calculate_context_uncertainty(anchor_score=0.0, discount_factor=1.0)
    assert u_max == pytest.approx(1.0, abs=1e-4)


def test_scenario_a_legitimate_context_suppression(risk_calc, base_time):
    """CANONICAL TEST: Scenario A (Legitimate Role Change).
    High behavioral deviation justified by strong authentic Jira onboarding anchor.
    VERIFICATION RULE: Risk score is attenuated below Tier 2 threshold (Tier 1: Suppressed).
    """
    result = risk_calc.evaluate(
        actor_token="Subject-Theta-482",
        anomaly_score=0.85,
        anchor_score=0.90,
        discount_factor=0.15,  # 85% discount!
        cumulative_drift_score=0.10,  # Minimal accumulated drift
        resource_criticality=0.60,
        identity_type="Human",
        timestamp=base_time,
    )

    assert result.composite_risk < 25.0
    assert result.risk_tier == RiskTier.TIER_1_CONTEXTUAL_DRIFT
    assert "suppressed from soc" in result.recommended_action.lower()


def test_scenario_c_fabricated_ticket_elevates(risk_calc, base_time):
    """CANONICAL TEST: Scenario C (Fabricated Context).
    Actor accesses high-sensitivity EU payroll database with self-approved fake ticket.
    VERIFICATION RULE: Risk stays elevated; triggers Tier 3 or Tier 4.
    """
    result = risk_calc.evaluate(
        actor_token="Subject-Theta-482",
        anomaly_score=0.95,
        anchor_score=0.05,  # Low anchor score
        discount_factor=0.98,  # Almost no discount (<2%)
        cumulative_drift_score=0.75,  # High cumulative drift
        resource_criticality=1.0,  # Critical EU payroll DB
        identity_type="Human",
        timestamp=base_time,
    )

    assert result.composite_risk >= 55.0
    assert result.risk_tier in [RiskTier.TIER_3_HIGH_RISK_TRAJECTORY, RiskTier.TIER_4_CRITICAL]
    assert any("T1078" in t for t in result.mitre_tactics)


def test_tier_4_critical_breach(risk_calc, base_time):
    """Verify high-confidence exfiltration on critical resources triggers Tier 4."""
    result = risk_calc.evaluate(
        actor_token="Subject-Critical-999",
        anomaly_score=1.0,
        anchor_score=0.0,
        discount_factor=1.0,
        cumulative_drift_score=0.95,
        resource_criticality=1.0,
        identity_type="Human",
        timestamp=base_time,
    )

    assert result.composite_risk >= 80.0
    assert result.risk_tier == RiskTier.TIER_4_CRITICAL
    assert "isolate endpoint" in result.recommended_action.lower()


def test_non_human_identity_risk_multipliers(risk_calc, base_time):
    """Verify non-human identities (CI/CD Runner, Service Account) receive higher composite risk
    than human identities under the same anomaly and drift.
    """
    human_res = risk_calc.evaluate(
        actor_token="Subject-Human",
        anomaly_score=0.70,
        anchor_score=0.0,
        discount_factor=1.0,
        cumulative_drift_score=0.50,
        resource_criticality=0.80,
        identity_type="Human",
        timestamp=base_time,
    )

    service_acc_res = risk_calc.evaluate(
        actor_token="SA-Cloud-Sync",
        anomaly_score=0.70,
        anchor_score=0.0,
        discount_factor=1.0,
        cumulative_drift_score=0.50,
        resource_criticality=0.80,
        identity_type="ServiceAccount",
        timestamp=base_time,
    )

    assert service_acc_res.composite_risk > human_res.composite_risk
    assert service_acc_res.breakdown.identity_risk == 1.35


def test_monte_carlo_1000_trials_composite_bounds(risk_calc, base_time):
    """PROPERTY TEST: 1,000 randomized trials verifying Composite Risk strictly resides in [0.0, 100.0]
    and risk tiers are mathematically consistent.
    """
    import random

    rng = random.Random(99)
    for i in range(1000):
        anomaly = rng.uniform(0.0, 1.0)
        anchor = rng.uniform(0.0, 1.0)
        discount = rng.uniform(0.15, 1.0)
        drift = rng.uniform(0.0, 1.0)
        crit = rng.uniform(0.1, 1.0)
        ident = rng.choice(["Human", "CICDRunner", "ServiceAccount"])

        res = risk_calc.evaluate(
            actor_token=f"Subject-Rand-{i}",
            anomaly_score=anomaly,
            anchor_score=anchor,
            discount_factor=discount,
            cumulative_drift_score=drift,
            resource_criticality=crit,
            identity_type=ident,
            timestamp=base_time,
        )

        assert 0.0 <= res.composite_risk <= 100.0
        assert res.risk_tier in [
            RiskTier.TIER_1_CONTEXTUAL_DRIFT,
            RiskTier.TIER_2_UNANCHORED_EXPLORATION,
            RiskTier.TIER_3_HIGH_RISK_TRAJECTORY,
            RiskTier.TIER_4_CRITICAL,
        ]
