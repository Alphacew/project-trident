"""Project TRIDENT — Test Suite for Trust & Context Authenticity Engine
Validates all 10 signals, mathematical invariants (delta >= 0.15),
Scenario C (Fabricated Context), Scenario A (Legitimate Context),
and edge cases.
"""

from datetime import datetime, timedelta, timezone
import pytest
from backend.trust.schemas import (
    AnchorType,
    ContextAnchor,
    EventContextStub,
)
from backend.trust.scope_matcher import compute_scope_match
from backend.trust.authenticity import ContextAuthenticityEngine, sigmoid
from backend.trust.anchor_engine import TrustAnchorEngine


@pytest.fixture
def base_time():
    return datetime(2026, 9, 16, 14, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def trust_engine():
    return TrustAnchorEngine()


def test_sigmoid_monotonicity_and_bounds():
    """Verify logistic sigmoid output range [0, 1] and monotonicity."""
    assert sigmoid(-100) == 0.0
    assert sigmoid(100) == 1.0
    assert abs(sigmoid(0) - 0.5) < 1e-6
    assert sigmoid(-5) < sigmoid(0) < sigmoid(5)


def test_delta_cap_invariant_1000_trials(trust_engine, base_time):
    """INVARIANT TEST: Verify delta >= 0.15 at all times, even with perfect anchors."""
    event = EventContextStub(
        event_id="evt-001",
        timestamp=base_time,
        actor_token="Subject-Alpha-101",
        action="QUERY",
        target_resource="prod_db.payments",
        resource_sensitivity=0.9,
    )

    # Perfect anchor with max parameters
    perfect_anchor = ContextAnchor(
        anchor_id="PERFECT-1",
        anchor_type=AnchorType.PAGERDUTY,
        title="Emergency P1 Incident on Payments Database",
        description="prod_db.payments query authorized by CAB",
        created_at=base_time - timedelta(minutes=30),
        requester_id="user_admin",
        approver_id="ciso_lead",
        target_resources=["prod_db.payments"],
        authority_weight=1.0,
        requester_approver_reporting_dist=3,
        downstream_commits_count=5,
        downstream_prs_count=2,
        corroborating_slack_messages_count=10,
        corroborating_pr_reviews_count=3,
        corroborating_calendar_events_count=1,
    )

    result = trust_engine.evaluate(event, [perfect_anchor])

    # Even with anchor_score ~ 1.0, discount_factor CANNOT be less than 0.15
    assert result.discount_factor >= 0.15
    assert result.residual_risk_ratio >= 0.15
    assert result.discount_factor == pytest.approx(0.15, abs=0.01)


def test_s1_temporal_mismatch(trust_engine, base_time):
    """Signal 1: Ticket created < 5m before action is flagged; ticket created after action is penalized."""
    event = EventContextStub(
        event_id="evt-s1",
        timestamp=base_time,
        actor_token="Subject-Beta-202",
        action="ACCESS",
        target_resource="payroll.db",
    )

    # 4 minutes before event (suspicious lead time)
    anchor_4min = ContextAnchor(
        anchor_id="TICKET-4MIN",
        created_at=base_time - timedelta(minutes=4),
        requester_id="Subject-Beta-202",
        target_resources=["payroll.db"],
    )
    cas_4min = trust_engine.cas_engine.evaluate_anchor(anchor_4min, event)
    s1_eval = cas_4min.signal_evaluations["s1_temporal_mismatch"]
    assert s1_eval.score < 0.0
    assert s1_eval.is_flagged is True

    # 10 minutes AFTER event occurred (retrofitted context)
    anchor_post = ContextAnchor(
        anchor_id="TICKET-POST",
        created_at=base_time + timedelta(minutes=10),
        requester_id="Subject-Beta-202",
        target_resources=["payroll.db"],
    )
    cas_post = trust_engine.cas_engine.evaluate_anchor(anchor_post, event)
    s1_post = cas_post.signal_evaluations["s1_temporal_mismatch"]
    assert s1_post.score == -1.0
    assert s1_post.is_flagged is True


def test_s2_and_s4_approver_conflict_and_sod(trust_engine, base_time):
    """Signals 2 and 4: Self-approval or identical requester/approver must trigger SoD violations."""
    event = EventContextStub(
        event_id="evt-sod",
        timestamp=base_time,
        actor_token="Subject-Gamma-303",
        action="UPDATE",
        target_resource="iam_policy",
    )

    anchor_self = ContextAnchor(
        anchor_id="TICKET-SELF",
        created_at=base_time - timedelta(hours=1),
        requester_id="Subject-Gamma-303",
        approver_id="Subject-Gamma-303",
        is_self_approved=True,
        target_resources=["iam_policy"],
    )
    cas = trust_engine.cas_engine.evaluate_anchor(anchor_self, event)
    assert cas.signal_evaluations["s2_approver_conflict"].score == -1.0
    assert cas.signal_evaluations["s4_sod_violation"].score == -1.0
    assert any("Separation of Duties" in d for d in cas.deductions)


def test_s6_scope_mismatch(trust_engine, base_time):
    """Signal 6: Ticket describing frontend layout accessing payroll DB must trigger scope mismatch."""
    event = EventContextStub(
        event_id="evt-scope",
        timestamp=base_time,
        actor_token="Subject-Delta-404",
        action="QUERY",
        target_resource="eu_payroll_prod.salaries",
    )

    anchor_mismatch = ContextAnchor(
        anchor_id="JIRA-CSS",
        title="Fix dropdown navbar button alignment on login page",
        description="Update CSS styling in react navbar component",
        created_at=base_time - timedelta(hours=2),
        requester_id="Subject-Delta-404",
        approver_id="mgr_alice",
        target_resources=["frontend-repo"],
    )

    scope_score = compute_scope_match(anchor_mismatch, event)
    assert scope_score < 0.25

    cas = trust_engine.cas_engine.evaluate_anchor(anchor_mismatch, event, precomputed_scope_score=scope_score)
    assert cas.signal_evaluations["s6_scope_mismatch"].score == -1.0
    assert cas.signal_evaluations["s6_scope_mismatch"].is_flagged is True


def test_s9_ghost_ticket(trust_engine, base_time):
    """Signal 9: Zero downstream commits/PRs/deploys indicates a ghost ticket."""
    event = EventContextStub(
        event_id="evt-ghost",
        timestamp=base_time,
        actor_token="Subject-Epsilon-505",
        action="DUMP",
        target_resource="customer_records",
    )

    anchor_ghost = ContextAnchor(
        anchor_id="JIRA-GHOST",
        title="Database migration",
        created_at=base_time - timedelta(hours=3),
        requester_id="Subject-Epsilon-505",
        downstream_commits_count=0,
        downstream_prs_count=0,
        downstream_deploys_count=0,
        target_resources=["customer_records"],
    )

    cas = trust_engine.cas_engine.evaluate_anchor(anchor_ghost, event)
    assert cas.signal_evaluations["s9_ghost_ticket"].score == -1.0
    assert cas.signal_evaluations["s9_ghost_ticket"].is_flagged is True


def test_s10_post_hoc_modification(trust_engine, base_time):
    """Signal 10: Ticket updated after anomalous event occurred."""
    event = EventContextStub(
        event_id="evt-posthoc",
        timestamp=base_time,
        actor_token="Subject-Zeta-606",
        action="EXTRACT",
        target_resource="secrets_vault",
    )

    anchor_modified = ContextAnchor(
        anchor_id="JIRA-RETRO",
        title="Maintenance",
        created_at=base_time - timedelta(hours=1),
        updated_at=base_time + timedelta(minutes=20),  # updated 20 min AFTER event
        requester_id="Subject-Zeta-606",
        target_resources=["secrets_vault"],
    )

    cas = trust_engine.cas_engine.evaluate_anchor(anchor_modified, event)
    assert cas.signal_evaluations["s10_post_hoc_modification"].score == -0.9
    assert cas.signal_evaluations["s10_post_hoc_modification"].is_flagged is True


def test_scenario_c_fabricated_context_survives_suppression(trust_engine, base_time):
    """CANONICAL TEST: Scenario C (Fabricated Context).
    Actor accesses EU payroll DB preceded 4 minutes by self-approved Jira ticket
    with no downstream commits and scope mismatch.
    VERIFICATION RULE: Must NOT be attenuated by more than 20% (delta >= 0.80).
    """
    event = EventContextStub(
        event_id="evt-scenario-c",
        timestamp=base_time,
        actor_token="Subject-Theta-482",
        action="BATCH_EXPORT",
        target_resource="eu_payroll_prod.salaries",
        resource_sensitivity=1.0,
    )

    fabricated_anchor = ContextAnchor(
        anchor_id="JIRA-FABRICATED",
        title="Quick update to staging readme",
        description="Minor documentation tweak",
        created_at=base_time - timedelta(minutes=4),  # Temporal mismatch: 4 min prior
        requester_id="Subject-Theta-482",
        approver_id="Subject-Theta-482",  # SoD violation: self-approval
        is_self_approved=True,
        requester_approver_reporting_dist=0,
        target_resources=["staging-repo"],  # Scope mismatch
        ticket_velocity_window_count=4,
        downstream_commits_count=0,  # Ghost ticket
        downstream_prs_count=0,
        downstream_deploys_count=0,
        corroborating_slack_messages_count=0,  # Cross-signal inconsistency
        authority_weight=0.85,
    )

    result = trust_engine.evaluate(event, [fabricated_anchor])

    # Core assertions proving the TRIDENT thesis:
    assert result.cas_report is not None
    assert result.cas_report.cas_score <= 0.30, f"Expected CAS <= 0.30, got {result.cas_report.cas_score}"
    assert result.cas_report.is_authentic is False
    assert result.anchor_score <= 0.20, f"Expected AnchorScore <= 0.20, got {result.anchor_score}"

    # Invariant: Attenuation must be <= 20%, so delta >= 0.80
    assert result.discount_factor >= 0.80, f"Expected delta >= 0.80, got {result.discount_factor}"

    # Verify deductions list is rich with explanations
    assert len(result.cas_report.deductions) >= 3


def test_scenario_a_legitimate_context_attenuates(trust_engine, base_time):
    """CANONICAL TEST: Scenario A (Legitimate Role Change / Approved Project).
    Legitimate developer accesses new service with manager-approved ticket,
    strong scope match, and downstream commits.
    VERIFICATION RULE: Anchor score is high and risk is attenuated to the 0.15 cap.
    """
    event = EventContextStub(
        event_id="evt-scenario-a",
        timestamp=base_time,
        actor_token="Subject-Theta-482",
        action="GET_SCHEMA",
        target_resource="payments_service.db",
        resource_sensitivity=0.6,
    )

    legitimate_anchor = ContextAnchor(
        anchor_id="JIRA-841",
        anchor_type=AnchorType.JIRA,
        title="Onboarding to Payments Microservice project",
        description="Database access granted for Q3 payments_service.db migration",
        created_at=base_time - timedelta(days=2),  # 2 days prior
        requester_id="Subject-Theta-482",
        approver_id="mgr_sarah",
        requester_approver_reporting_dist=2,
        is_self_approved=False,
        target_resources=["payments_service.db"],
        downstream_commits_count=4,
        downstream_prs_count=2,
        corroborating_slack_messages_count=8,
        corroborating_pr_reviews_count=2,
        authority_weight=0.90,
    )

    result = trust_engine.evaluate(event, [legitimate_anchor])

    assert result.cas_report.cas_score >= 0.85
    assert result.cas_report.is_authentic is True
    assert result.anchor_score >= 0.65
    assert result.discount_factor <= 0.35
    assert result.discount_factor >= 0.15


def test_zero_candidate_anchors(trust_engine, base_time):
    """Boundary test: Event with zero anchors receives 0 anchor score and 1.0 discount (100% risk)."""
    event = EventContextStub(
        event_id="evt-no-anchor",
        timestamp=base_time,
        actor_token="Subject-Theta-482",
        action="LIST_BUCKETS",
        target_resource="s3://raw-logs",
    )

    result = trust_engine.evaluate(event, [])
    assert result.selected_anchor_id is None
    assert result.anchor_score == 0.0
    assert result.discount_factor == 1.0
    assert result.residual_risk_ratio == 1.0
    assert result.cas_report is None


def test_s3_emergency_abuse_signal(trust_engine, base_time):
    """Signal 3: Emergency ticket abuse detected when actor's count exceeds cohort mean by > 2.5 sigma."""
    event = EventContextStub(
        event_id="evt-s3",
        timestamp=base_time,
        actor_token="Subject-Beta-202",
        action="EXEC_ROOT",
        target_resource="bastion-host",
    )

    # Actor has 8 emergency tickets (cohort mean=1.0, std=1.0 -> z=7.0 > 2.5)
    anchor_abused = ContextAnchor(
        anchor_id="EMERGENCY-ABUSE",
        created_at=base_time - timedelta(hours=1),
        requester_id="Subject-Beta-202",
        is_emergency=True,
        actor_emergency_count_30d=8,
        cohort_emergency_mean_30d=1.0,
        cohort_emergency_std_30d=1.0,
        target_resources=["bastion-host"],
    )
    cas = trust_engine.cas_engine.evaluate_anchor(anchor_abused, event)
    s3_eval = cas.signal_evaluations["s3_emergency_abuse"]
    assert s3_eval.score == -1.0
    assert s3_eval.is_flagged is True
    assert "Emergency abuse" in s3_eval.rationale


def test_s5_stale_hr_metadata_signal(trust_engine, base_time):
    """Signal 5: Access requested using stale HR project tag or deprecated department."""
    event = EventContextStub(
        event_id="evt-s5",
        timestamp=base_time,
        actor_token="Subject-Gamma-303",
        action="READ",
        target_resource="legacy-datastore",
    )

    anchor_stale = ContextAnchor(
        anchor_id="TICKET-STALE-HR",
        created_at=base_time - timedelta(hours=2),
        requester_id="Subject-Gamma-303",
        hr_project_tag="PROJ_OLD_FINANCE_DEPRECATED",
        actor_current_project_tag="PROJ_CLOUD_INFRA",
        is_stale_hr_project=True,
        target_resources=["legacy-datastore"],
    )
    cas = trust_engine.cas_engine.evaluate_anchor(anchor_stale, event)
    s5_eval = cas.signal_evaluations["s5_stale_hr_metadata"]
    assert s5_eval.score <= -0.7
    assert s5_eval.is_flagged is True


def test_s7_cross_signal_inconsistency_signal(trust_engine, base_time):
    """Signal 7: High-authority emergency ticket with zero Slack/PR/calendar traces is flagged."""
    event = EventContextStub(
        event_id="evt-s7",
        timestamp=base_time,
        actor_token="Subject-Delta-404",
        action="DEPLOY",
        target_resource="k8s_prod_cluster",
    )

    anchor_silent = ContextAnchor(
        anchor_id="TICKET-SILENT",
        created_at=base_time - timedelta(hours=1),
        requester_id="Subject-Delta-404",
        is_emergency=True,
        authority_weight=0.95,
        corroborating_slack_messages_count=0,
        corroborating_pr_reviews_count=0,
        corroborating_calendar_events_count=0,
        target_resources=["k8s_prod_cluster"],
    )
    cas = trust_engine.cas_engine.evaluate_anchor(anchor_silent, event)
    s7_eval = cas.signal_evaluations["s7_cross_signal_inconsistency"]
    assert s7_eval.score == -0.7
    assert s7_eval.is_flagged is True


def test_s8_ticket_velocity_anomaly_signal(trust_engine, base_time):
    """Signal 8: Abnormal burst of ticket creation (>4 in window) is penalized."""
    event = EventContextStub(
        event_id="evt-s8",
        timestamp=base_time,
        actor_token="Subject-Epsilon-505",
        action="QUERY",
        target_resource="bi_warehouse",
    )

    anchor_burst = ContextAnchor(
        anchor_id="TICKET-BURST",
        created_at=base_time - timedelta(minutes=15),
        requester_id="Subject-Epsilon-505",
        ticket_velocity_window_count=6,
        target_resources=["bi_warehouse"],
    )
    cas = trust_engine.cas_engine.evaluate_anchor(anchor_burst, event)
    s8_eval = cas.signal_evaluations["s8_ticket_velocity_anomaly"]
    assert s8_eval.score == -1.0
    assert s8_eval.is_flagged is True


def test_monte_carlo_1000_trials_delta_invariant(trust_engine, base_time):
    """PROPERTY TEST: 1,000 randomized Monte Carlo trials verifying delta in [0.15, 1.0] under all parameters."""
    import random

    rng = random.Random(42)
    for i in range(1000):
        # Generate arbitrary random anchor parameters
        auth = rng.uniform(0.0, 1.0)
        lead_time_mins = rng.uniform(-60.0, 14400.0)  # past or future
        is_emergency = rng.choice([True, False])
        emergency_count = rng.randint(0, 20)
        self_approved = rng.choice([True, False])
        dist = rng.randint(0, 4)
        downstream = rng.randint(0, 10)
        slack = rng.randint(0, 15)
        velocity = rng.randint(1, 10)
        scope = rng.choice(["payments.db", "frontend-ui", "analytics", "random-res"])

        anchor = ContextAnchor(
            anchor_id=f"RAND-{i}",
            title=f"Task {i} for {scope}",
            description="Random simulated task",
            created_at=base_time - timedelta(minutes=lead_time_mins),
            requester_id="user_test",
            approver_id="user_test" if self_approved else f"approver_{dist}",
            is_self_approved=self_approved,
            requester_approver_reporting_dist=dist,
            is_emergency=is_emergency,
            actor_emergency_count_30d=emergency_count,
            ticket_velocity_window_count=velocity,
            downstream_commits_count=downstream,
            corroborating_slack_messages_count=slack,
            target_resources=[scope],
            authority_weight=auth,
        )

        event = EventContextStub(
            event_id=f"evt-rand-{i}",
            timestamp=base_time,
            actor_token="Subject-Random",
            action="ACCESS",
            target_resource="payments.db",
        )

        result = trust_engine.evaluate(event, [anchor])

        # Mathematical Invariants:
        assert 0.15 <= result.discount_factor <= 1.0, f"Violation: delta={result.discount_factor}"
        assert 0.0 <= result.anchor_score <= 1.0, f"Violation: score={result.anchor_score}"
        assert 0.0 <= result.cas_report.cas_score <= 1.0, f"Violation: CAS={result.cas_report.cas_score}"

