"""Project TRIDENT — Test Suite for Drift Engine & CUSUM Accumulator
Validates dual fast/slow baselines, anti-poisoning, unanchored displacement,
recursive CUSUM accumulation, and Scenario B (Low-and-Slow Insider).
"""

from datetime import datetime, timedelta, timezone
import pytest
from backend.drift.schemas import (
    BehavioralFeatureVector,
    TrajectoryState,
)
from backend.drift.baselines import BaselineManager
from backend.drift.cusum import CUSUMDriftEngine


@pytest.fixture
def base_time():
    return datetime(2026, 9, 17, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def baseline_manager():
    return BaselineManager(anti_poisoning_alpha=0.35)


@pytest.fixture
def drift_engine(baseline_manager):
    return CUSUMDriftEngine(baseline_manager=baseline_manager, slack_k=0.10)


def test_feature_vector_distance_and_roundtrip():
    """Verify Euclidean distance and NumPy roundtrip conversions."""
    v1 = BehavioralFeatureVector(
        event_volume_rate=1.0,
        resource_sensitivity_mean=0.2,
        new_resource_discovery_ratio=0.0,
        off_hours_ratio=0.0,
        action_privilege_intensity=0.1,
        cross_boundary_entropy=0.0,
    )
    v2 = BehavioralFeatureVector(
        event_volume_rate=4.0,
        resource_sensitivity_mean=0.8,
        new_resource_discovery_ratio=0.5,
        off_hours_ratio=0.8,
        action_privilege_intensity=0.7,
        cross_boundary_entropy=0.4,
    )
    dist = v1.euclidean_distance(v2)
    assert dist > 3.0

    # Roundtrip through NumPy array
    arr = v1.to_numpy()
    v1_reconstructed = BehavioralFeatureVector.from_numpy(arr)
    assert v1.euclidean_distance(v1_reconstructed) == pytest.approx(0.0, abs=1e-6)


def test_anti_poisoning_dual_baseline_resistance(baseline_manager):
    """Verify that slow 90d baseline prevents fast 7d baseline from poisoning effective baseline."""
    actor = "Subject-Theta-482"
    profile = baseline_manager.get_or_create_profile(actor, cohort_name="Engineering-Backend")

    initial_base = baseline_manager.compute_effective_baseline(actor)

    # Attacker performs elevated activity for 7 days attempting to shift the baseline
    poisoned_obs = [
        BehavioralFeatureVector(
            event_volume_rate=4.0,
            resource_sensitivity_mean=0.9,
            new_resource_discovery_ratio=0.8,
            off_hours_ratio=0.7,
            action_privilege_intensity=0.8,
            cross_boundary_entropy=0.6,
        )
        for _ in range(7)
    ]
    baseline_manager.update_fast_baseline(actor, poisoned_obs)

    effective_after = baseline_manager.compute_effective_baseline(actor)

    # Fast baseline adapted completely to 4.0
    assert profile.fast_baseline_7d.event_volume_rate == pytest.approx(4.0, abs=0.01)

    # But effective baseline is anchored by slow 90d baseline (weighted alpha=0.35 fast + 0.65 slow)
    # Slow is 1.0, fast is 4.0 -> effective is 0.35 * 4.0 + 0.65 * 1.0 = 2.05
    assert effective_after.event_volume_rate == pytest.approx(2.05, abs=0.05)
    assert effective_after.event_volume_rate < 3.0


def test_unanchored_displacement_attenuation(drift_engine):
    """Verify displacement is attenuated by up to 85% under valid context (delta=0.15),
    and reaches 100% under unanchored/fabricated context (delta=1.0).
    """
    v_base = BehavioralFeatureVector(event_volume_rate=1.0, resource_sensitivity_mean=0.2)
    v_curr = BehavioralFeatureVector(event_volume_rate=3.0, resource_sensitivity_mean=0.8)

    # Full displacement with no anchor (delta = 1.0)
    d_unanchored = drift_engine.compute_displacement(v_curr, v_base, discount_factor=1.0)

    # Suppressed displacement with authentic anchor (delta = 0.15)
    d_attenuated = drift_engine.compute_displacement(v_curr, v_base, discount_factor=0.15)

    assert d_attenuated == pytest.approx(d_unanchored * 0.15, abs=1e-3)
    assert d_attenuated < d_unanchored


def test_scenario_b_low_and_slow_cumulative_drift(drift_engine, base_time):
    """CANONICAL TEST: Scenario B (Low-and-Slow Insider).
    An insider accesses 5 sensitive resources daily over 14 days without an anchor.
    Individual daily displacement is small, but CUSUM accumulates steadily into HIGH_RISK_TRAJECTORY.
    """
    actor = "Subject-Kappa-789"
    drift_engine.reset_actor_state(actor)

    # Slight daily deviation: querying sensitive files without ticket (delta = 1.0)
    subtle_daily_activity = BehavioralFeatureVector(
        event_volume_rate=1.3,
        resource_sensitivity_mean=0.75,  # Higher sensitivity
        new_resource_discovery_ratio=0.15,
        off_hours_ratio=0.05,
        action_privilege_intensity=0.25,
        cross_boundary_entropy=0.15,
    )

    states = []
    scores = []

    for day in range(1, 15):
        t = base_time + timedelta(days=day)
        report = drift_engine.update(
            actor_token=actor,
            current_vector=subtle_daily_activity,
            discount_factor=1.0,  # Unanchored!
            timestamp=t,
        )
        states.append(report.trajectory_state)
        scores.append(report.cusum_drift_score)

    # Day 1: Single day deviation is modest, state is STABLE
    assert scores[0] < 1.0
    assert states[0] == TrajectoryState.STABLE

    # Scores must monotonically increase because daily displacement exceeds slack
    assert scores[-1] > scores[0]

    # By Day 14, CUSUM has accumulated past the High-Risk Trajectory threshold
    assert scores[-1] >= drift_engine.tau_high_risk
    assert states[-1] in [TrajectoryState.HIGH_RISK_TRAJECTORY, TrajectoryState.CRITICAL]


def test_benign_recovery_cusum_decays_significantly(drift_engine, base_time):
    """Verify that when an actor returns to normal baseline activity, CUSUM decays significantly."""
    actor = "Subject-Lambda-101"
    drift_engine.reset_actor_state(actor)

    # Acute spike on Day 1
    spike = BehavioralFeatureVector(event_volume_rate=4.0, resource_sensitivity_mean=0.9)
    report_spike = drift_engine.update(actor, spike, discount_factor=1.0, timestamp=base_time)
    assert report_spike.cusum_drift_score > 0.5
    peak_score = report_spike.cusum_drift_score

    # 15 days of completely normal baseline activity with strong context (delta=0.15)
    normal = BehavioralFeatureVector(event_volume_rate=1.0, resource_sensitivity_mean=0.25)
    final_score = peak_score
    for day in range(1, 16):
        r = drift_engine.update(actor, normal, discount_factor=0.15, timestamp=base_time + timedelta(days=day))
        final_score = r.cusum_drift_score

    # CUSUM must have decayed significantly from peak (floor is 0.0)
    assert final_score < peak_score * 0.5, f"Expected significant decay from {peak_score}, got {final_score}"
    assert r.trajectory_state == TrajectoryState.STABLE


def test_dimension_attribution_forensic_insights(drift_engine, base_time):
    """Verify forensic attribution highlights specifically which dimensions triggered the anomaly."""
    actor = "Subject-Mu-202"
    drift_engine.reset_actor_state(actor)

    off_hours_burst = BehavioralFeatureVector(
        event_volume_rate=1.0,
        resource_sensitivity_mean=0.25,
        new_resource_discovery_ratio=0.0,
        off_hours_ratio=0.95,  # 95% off-hours activity spike!
        action_privilege_intensity=0.10,
        cross_boundary_entropy=0.0,
    )

    report = drift_engine.update(actor, off_hours_burst, discount_factor=1.0, timestamp=base_time)
    assert report.dimension_attribution["off_hours_ratio"] >= 2.0
    assert any("Off-Hours Activity" in insight for insight in report.forensic_insights)
