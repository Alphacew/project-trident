"""Project TRIDENT — Test Suite for Anti-Harassment Governance & Hash-Chained Audit.

Validates:
1. Direct query blocking on employee names and email addresses.
2. Valid pseudonym tokens and anomaly IDs are permitted.
3. Repeat subject queries (>3 in 14-day window in low-risk tier) trigger DPO compliance alerts.
4. Managerial view differential privacy redaction (k >= 5 threshold).
5. ShamirVault hash-chain generation, append-only integrity, and tamper detection.
"""

from datetime import datetime, timedelta, timezone
import pytest

from backend.crypto.harassment_audit import AntiHarassmentGuard, HarassmentAlert
from backend.crypto.shamir_vault import RevealReceipt, ShamirVault


@pytest.fixture
def guard():
    return AntiHarassmentGuard(repeat_query_threshold=3, window_days=14)


def test_block_direct_email_queries(guard):
    """Verifies queries with raw email addresses are strictly blocked."""
    res = guard.validate_query("elena.rostova@megacorp.internal")
    assert res.allowed is False
    assert res.query_type == "BLOCKED_EMAIL"
    assert "Direct email query prohibited" in res.reason


def test_block_direct_employee_names(guard):
    """Verifies searches using human names are blocked to prevent targeted surveillance."""
    res1 = guard.validate_query("Elena Rostova")
    assert res1.allowed is False
    assert res1.query_type == "BLOCKED_DIRECT_NAME"

    res2 = guard.validate_query("John Doe")
    assert res2.allowed is False
    assert res2.query_type == "BLOCKED_DIRECT_NAME"


def test_allow_pseudonyms_and_anomaly_ids(guard):
    """Verifies that queries using legitimate pseudonyms or anomaly IDs are permitted."""
    # Pseudonym tokens
    res_sub = guard.validate_query("Subject-Theta-482")
    assert res_sub.allowed is True
    assert res_sub.query_type == "PSEUDONYM"

    res_run = guard.validate_query("Runner-Bravo-104")
    assert res_run.allowed is True
    assert res_run.query_type == "PSEUDONYM"

    # Graph anomaly IDs
    res_anom = guard.validate_query("ANOM-GRAPH-2026-001")
    assert res_anom.allowed is True
    assert res_anom.query_type == "ANOMALY_ID"

    res_inc = guard.validate_query("INC-4921")
    assert res_inc.allowed is True
    assert res_inc.query_type == "ANOMALY_ID"

    res_res = guard.validate_query("arn:aws:s3:::customer-pii-backup")
    assert res_res.allowed is True
    assert res_res.query_type == "RESOURCE_ID"


def test_repeat_subject_queries_trigger_dpo_alert(guard):
    """Verifies that inspecting the same subject >3 times in 14 days without escalation alerts DPO."""
    token = "Subject-Alpha-042"
    now = datetime.now(timezone.utc)

    # 1st query: allowed, no alert
    a1 = guard.record_subject_access(token, "Analyst-Bob", "TIER_1_CONTEXTUAL_DRIFT", now - timedelta(days=5))
    assert a1 is None
    assert len(guard.alerts) == 0

    # 2nd query: allowed, no alert
    a2 = guard.record_subject_access(token, "Analyst-Bob", "TIER_1_CONTEXTUAL_DRIFT", now - timedelta(days=3))
    assert a2 is None
    assert len(guard.alerts) == 0

    # 3rd query: allowed, still at threshold (no alert yet)
    a3 = guard.record_subject_access(token, "Analyst-Bob", "TIER_1_CONTEXTUAL_DRIFT", now - timedelta(days=1))
    assert a3 is None
    assert len(guard.alerts) == 0

    # 4th query: EXCEEDS threshold (count=4 > 3) on low-risk profile -> Triggers DPO Alert!
    a4 = guard.record_subject_access(token, "Analyst-Bob", "TIER_1_CONTEXTUAL_DRIFT", now)
    assert a4 is not None
    assert isinstance(a4, HarassmentAlert)
    assert a4.subject_token == token
    assert a4.query_count == 4
    assert len(guard.alerts) == 1
    assert "flagged for DPO fairness audit" in a4.dpo_notification


def test_repeat_queries_on_high_risk_do_not_trigger_harassment_alert(guard):
    """Verifies that high-risk subjects (Tier 3/4) being investigated frequently do NOT trigger false harassment alerts."""
    token = "Subject-Theta-482"
    now = datetime.now(timezone.utc)

    for i in range(5):
        guard.record_subject_access(token, "Analyst-Alice", "TIER_4_CRITICAL", now)

    # Since risk is Tier 4 Critical, investigations are justified -> 0 harassment alerts
    assert len(guard.alerts) == 0


def test_manager_view_cohort_redaction(guard):
    """Verifies k >= 5 differential privacy redaction in manager views."""
    # Cohort with 3 members (< 5) -> must be redacted
    small_cohort = [
        {"actor_token": "Subject-1", "composite_risk": 12.0, "cusum_drift_score": 0.2},
        {"actor_token": "Subject-2", "composite_risk": 15.0, "cusum_drift_score": 0.3},
        {"actor_token": "Subject-3", "composite_risk": 10.0, "cusum_drift_score": 0.1},
    ]
    redacted = guard.filter_for_manager_view(small_cohort, min_cohort_size=5)
    assert redacted["is_redacted"] is True
    assert redacted["aggregated_metrics"] is None
    assert "below the required differential privacy threshold" in redacted["message"]

    # Cohort with 5 members (>= 5) -> aggregates safe metrics without individual tokens
    valid_cohort = small_cohort + [
        {"actor_token": "Subject-4", "composite_risk": 20.0, "cusum_drift_score": 0.4},
        {"actor_token": "Subject-5", "composite_risk": 18.0, "cusum_drift_score": 0.3},
    ]
    agg = guard.filter_for_manager_view(valid_cohort, min_cohort_size=5)
    assert agg["is_redacted"] is False
    assert agg["aggregated_metrics"] is not None
    assert agg["aggregated_metrics"]["mean_composite_risk"] == 15.0
    # Confirm individual tokens are stripped from top-level response
    assert "actor_token" not in agg


def test_shamir_hash_chain_integrity_and_tamper_detection():
    """Verifies that ShamirVault maintains a valid cryptographic hash chain and detects tampering."""
    vault = ShamirVault()
    assert vault.verify_audit_log_integrity()["status"] == "EMPTY_LEDGER"

    # Add 3 reveals
    r1 = vault.record_reveal("REV-1", "Subject-A", "user.a@corp", ["SOC_LEAD", "DPO_LEGAL"], "Case 1", "Auditor-1")
    assert r1.previous_receipt_hash == "0" * 64
    assert len(r1.entry_hash) == 64

    r2 = vault.record_reveal("REV-2", "Subject-B", "user.b@corp", ["DPO_LEGAL", "WORKS_COUNCIL"], "Case 2", "Auditor-1")
    assert r2.previous_receipt_hash == r1.entry_hash

    r3 = vault.record_reveal("REV-3", "Subject-C", "user.c@corp", ["SOC_LEAD", "WORKS_COUNCIL"], "Case 3", "Auditor-1")
    assert r3.previous_receipt_hash == r2.entry_hash

    # Verify chain
    verification = vault.verify_audit_log_integrity()
    assert verification["verified"] is True
    assert verification["entries_checked"] == 3
    assert verification["status"] == "TAMPER_FREE"

    # Tamper with receipt 2 entry content (simulate unauthorized modification)
    vault.reveal_log[1].justification = "Tampered unauthorized reason!"
    tamper_check = vault.verify_audit_log_integrity()
    assert tamper_check["verified"] is False
    assert tamper_check["status"] == "ENTRY_HASH_MISMATCH"
    assert tamper_check["broken_at_index"] == 1
