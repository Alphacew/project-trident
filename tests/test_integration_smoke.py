"""Project TRIDENT — Git Sync Checkpoint 1: Integration Smoke Test.

Validates the full DevA -> DevB Phase 1 contract:
1. DevA feeds raw synthetic events into OCSFEventNormalizer & ProtectedFilter.
2. Protected whistleblower events are dropped at the boundary and never persist.
3. Clean events are pseudonymized (Subject-*-***) with raw_id stripped.
4. DevB's TrustAnchorEngine evaluates candidate anchors directly against DevA's
   pseudonymized CanonicalEvent.
5. Verifies that the 0.85 discount cap (minimum 15% residual risk: delta >= 0.15) holds strictly.
6. Verifies that fabricated tickets fail to suppress risk.
"""

from datetime import datetime, timedelta, timezone
import pytest

from backend.common.schemas import CanonicalEvent
from backend.ingestion.normalizer import OCSFEventNormalizer
from backend.trust.anchor_engine import TrustAnchorEngine
from backend.trust.schemas import AnchorType, ContextAnchor, EventContextStub


@pytest.fixture
def normalizer():
    return OCSFEventNormalizer()


@pytest.fixture
def trust_engine():
    return TrustAnchorEngine()


@pytest.fixture
def base_timestamp():
    return datetime(2026, 9, 17, 10, 0, 0, tzinfo=timezone.utc)


def test_smoke_protected_filter_drops_before_trust_engine(normalizer, trust_engine, base_timestamp):
    """Smoke Test Step 1: Protected endpoint filter drops whistleblower activity."""
    raw_event = {
        "event_id": "EVT-SMOKE-WHISTLEBLOWER",
        "action": "http:post",
        "destination_endpoint": "https://whistleblower.internal.corp/reports/anonymous",
        "actor_id": "alice.cooper@corp.internal",
        "timestamp": base_timestamp.isoformat(),
    }

    canonical, filter_res = normalizer.normalize_event(raw_event)

    # Invariant 1: Must be dropped at ingestion
    assert filter_res.is_protected is True
    assert filter_res.action == "DROP_FROM_GRAPH"
    assert canonical is None, "Protected event must never produce a CanonicalEvent"


def test_smoke_deva_pseudonymization_to_devb_anchor_cap(normalizer, trust_engine, base_timestamp):
    """Smoke Test Step 2: DevA feeds synthetic event; DevB evaluates anchor and validates 0.85 discount cap."""
    # DevA feeds synthetic AWS CloudTrail event
    raw_cloudtrail = {
        "event_id": "EVT-SMOKE-S3-001",
        "eventSource": "s3.amazonaws.com",
        "eventName": "GetObject",
        "userIdentity": {
            "type": "IAMUser",
            "userName": "alice.developer@corp.internal",
        },
        "resources": [
            {"ARN": "arn:aws:s3:::corp-cloud-migration/manifest.json", "type": "AWS::S3::Object"}
        ],
        "sourceIPAddress": "10.0.1.25",
        "timestamp": (base_timestamp + timedelta(days=5)).isoformat(),
    }

    canonical_event, filter_res = normalizer.normalize_event(raw_cloudtrail)

    # DevA assertions
    assert canonical_event is not None
    assert filter_res.is_protected is False
    assert canonical_event.actor.actor_token.startswith("Subject-")
    assert canonical_event.actor.raw_id is None, "Raw identity must be stripped at boundary"

    # Candidate ticket for legitimate work (Day 5 beat)
    ticket_legit = ContextAnchor(
        anchor_id="JIRA-841",
        anchor_type=AnchorType.JIRA,
        title="Sprint 14 Cloud Migration",
        description="Migrate assets to arn:aws:s3:::corp-cloud-migration",
        created_at=canonical_event.timestamp - timedelta(days=2),
        requester_id=canonical_event.actor.actor_token,
        approver_id="Subject-Manager-01",
        target_resources=["arn:aws:s3:::corp-cloud-migration/manifest.json"],
        authority_weight=1.0,
        downstream_commits_count=3,
        downstream_prs_count=1,
        corroborating_slack_messages_count=5,
        corroborating_calendar_events_count=2,
        is_self_approved=False,
        requester_approver_reporting_dist=2,
    )

    # DevB evaluates DevA's CanonicalEvent directly
    eval_result = trust_engine.evaluate(canonical_event, [ticket_legit])

    # Core Validation: 0.85 discount cap (delta >= 0.15) holds strictly
    assert eval_result.selected_anchor_id == "JIRA-841"
    assert eval_result.anchor_score > 0.85
    assert eval_result.discount_factor >= 0.15, "INVARIANT VIOLATION: discount_factor < 0.15"
    assert eval_result.discount_factor == 0.15, (
        f"Expected delta to be capped at 0.15 (85% attenuation cap), got {eval_result.discount_factor}"
    )
    assert eval_result.residual_risk_ratio == 0.15
    assert eval_result.cas_report.is_authentic is True


def test_smoke_deva_to_devb_fabricated_ticket_fails_suppression(normalizer, trust_engine, base_timestamp):
    """Smoke Test Step 3: Fabricated context (4m lead time, self-approval) fails to suppress risk."""
    raw_payroll = {
        "event_id": "EVT-SMOKE-PAYROLL-002",
        "action": "db:query",
        "actor_id": "alice.developer@corp.internal",
        "resource_id": "db:eu-payroll-records",
        "sensitivity": 0.95,
        "timestamp": (base_timestamp + timedelta(days=10)).isoformat(),
    }

    canonical_event, _ = normalizer.normalize_event(raw_payroll)
    assert canonical_event is not None

    # Fabricated anchor created 4 mins earlier with self-approval and 0 artifacts
    ticket_fab = ContextAnchor(
        anchor_id="JIRA-FAB-PAYROLL",
        anchor_type=AnchorType.JIRA,
        title="Quick DB query",
        description="Check database status",
        created_at=canonical_event.timestamp - timedelta(minutes=4),  # 4m temporal mismatch!
        requester_id=canonical_event.actor.actor_token,
        approver_id=canonical_event.actor.actor_token,  # Self-approval!
        target_resources=["generic-table"],
        authority_weight=0.85,
        downstream_commits_count=0,
        downstream_prs_count=0,
        corroborating_slack_messages_count=0,
        corroborating_calendar_events_count=0,
        is_self_approved=True,
        requester_approver_reporting_dist=0,
    )

    eval_result = trust_engine.evaluate(canonical_event, [ticket_fab])

    # Assert CAS detects fabrication and risk remains elevated
    assert eval_result.cas_report.is_authentic is False
    assert eval_result.cas_report.cas_score < 0.30
    assert eval_result.discount_factor >= 0.80, (
        f"Fabricated context must NOT attenuate risk (expected delta >= 0.80, got {eval_result.discount_factor})"
    )


def test_smoke_monte_carlo_200_trials_delta_cap(normalizer, trust_engine, base_timestamp):
    """Smoke Test Step 4: 200 randomized events & anchors verify delta >= 0.15 is invariant."""
    import random

    for i in range(200):
        lead_minutes = random.uniform(-10, 20000)
        auth = random.uniform(0.0, 1.0)
        commits = random.randint(0, 10)
        self_app = random.choice([True, False])

        raw = {
            "event_id": f"EVT-MC-{i}",
            "action": "s3:GetObject",
            "actor_id": f"user_{i}@corp.internal",
            "resource_id": "arn:aws:s3:::corp-data/bucket",
            "timestamp": base_timestamp.isoformat(),
        }
        canonical, _ = normalizer.normalize_event(raw)

        anchor = ContextAnchor(
            anchor_id=f"ANCHOR-{i}",
            created_at=base_timestamp - timedelta(minutes=lead_minutes),
            requester_id=canonical.actor.actor_token,
            approver_id=canonical.actor.actor_token if self_app else f"manager_{i}",
            target_resources=["arn:aws:s3:::corp-data/bucket"],
            authority_weight=auth,
            downstream_commits_count=commits,
            is_self_approved=self_app,
        )

        res = trust_engine.evaluate(canonical, [anchor])
        assert res.discount_factor >= 0.15, f"Trial {i}: Invariant violated! delta={res.discount_factor}"
        assert res.discount_factor <= 1.0, f"Trial {i}: delta exceeded 1.0! delta={res.discount_factor}"
