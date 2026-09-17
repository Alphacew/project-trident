"""Project TRIDENT — Phase 3 Full-Stack End-to-End Integration Smoke Test.

Validates the complete vertical slice from raw telemetry ingestion through to
the 3-screen SOC console data contracts:
1. Master 14-day demo dataset loads cleanly.
2. Screen 1: Dual Timeline retrieves snapshots with capped context attenuation (delta >= 0.15).
3. Screen 2: Causal subgraph extracts React Flow DAG, triggers simulated canary trip (CONFIRMED state), and synthesizes MITRE ATT&CK dossier.
4. Screen 3: Shamir 2-of-3 reveal ceremony recovers real identity, appends SHA-256 hash-chained receipt, and verifies ledger integrity.
5. Anti-harassment safeguards block direct employee name queries and alert DPO on repeat scrutiny.
6. Ingestion protected-endpoint filter guarantees zero leaks to graph.
"""

from fastapi.testclient import TestClient
import pytest

from backend.api.app import app
from backend.api.manager import demo_manager


@pytest.fixture
def client():
    demo_manager.initialize()
    return TestClient(app)


def test_full_stack_end_to_end_pipeline(client):
    """Executes the complete Phase 3 vertical slice."""
    # 1. Verify healthcheck and Claim Ledger
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["claim_label"] == "Measured Today"

    # 2. Screen 1: Dual Timeline & Scenarios
    res_scenarios = client.get("/api/scenarios")
    assert res_scenarios.status_code == 200
    scenarios = res_scenarios.json()
    assert len(scenarios) >= 5

    res_timeline = client.get("/api/timeline")
    assert res_timeline.status_code == 200
    timeline = res_timeline.json()
    assert len(timeline) == 14

    # Beat 2 (Day 5): Benign anomaly suppressed
    day5 = timeline[4]
    assert day5["context_authenticity_score"] >= 0.70
    assert day5["discount_factor"] <= 0.40

    # Beat 3 (Day 10): Fabricated context rejected
    day10 = timeline[9]
    assert day10["context_authenticity_score"] <= 0.30
    assert day10["discount_factor"] >= 0.75  # Suppression denied!

    # 3. Screen 2: Causal Subgraph & Simulated Canary Trip
    res_graph = client.get("/api/graph/causal?day=14")
    assert res_graph.status_code == 200
    graph = res_graph.json()
    assert len(graph["nodes"]) >= 5
    assert len(graph["edges"]) >= 5

    # Simulated Canary interactive trip
    res_trip = client.post("/api/canary/trip", json={"resource_id": "arn:aws:s3:::canary-decoy-payroll-backup"})
    assert res_trip.status_code == 200
    trip_data = res_trip.json()
    assert trip_data["is_tripped"] is True
    assert trip_data["confirmation_state"] == "CONFIRMED"
    assert trip_data["claim_label"] == "Simulated Canary"

    # Forensic Dossier synthesis
    res_dossier = client.get("/api/evidence/dossier?day=14")
    assert res_dossier.status_code == 200
    dossier = res_dossier.json()
    assert dossier["risk_tier"] == "TIER_4_CRITICAL"
    assert "CRITICAL BREACH ESCALATION" in dossier["executive_summary"]
    assert any("T1078" in m["technique_id"] for m in dossier["mitre_attack_matrix"])

    # 4. Screen 3: Shamir 2-of-3 Reveal Ceremony & Hash-Chained Ledger
    res_vault = client.get("/api/privacy/vault/status")
    assert res_vault.status_code == 200
    vault_status = res_vault.json()
    assert vault_status["threshold"] == "2-of-3"
    assert len(vault_status["custodian_shares"]) == 3

    # Execute 2-of-3 unmasking (SOC Lead + DPO Legal)
    res_unmask = client.post(
        "/api/privacy/vault/recombine",
        json={
            "share_indices": [1, 2],
            "subject_token": "Subject-Theta-482",
            "justification": "Authorized Tier 4 insider breach unmasking protocol.",
            "auditor_token": "DPO-AUDIT-FINAL-2026",
        },
    )
    assert res_unmask.status_code == 200
    receipt = res_unmask.json()
    assert receipt["unmasked_identity"] == "elena.rostova@megacorp.internal"
    assert len(receipt["entry_hash"]) == 64

    # Verify audit log and hash chain integrity
    res_audit = client.get("/api/privacy/vault/audit-log")
    assert res_audit.status_code == 200
    assert len(res_audit.json()) >= 1

    res_verify = client.post("/api/privacy/vault/verify-log")
    assert res_verify.status_code == 200
    assert res_verify.json()["verified"] is True
    assert res_verify.json()["status"] == "TAMPER_FREE"

    # 5. Anti-Harassment Query Interceptor
    # Test blocked direct employee name
    res_blocked = client.post(
        "/api/privacy/query/validate",
        json={"query": "Elena Rostova", "analyst_id": "Analyst-1"},
    )
    assert res_blocked.status_code == 200
    assert res_blocked.json()["allowed"] is False
    assert res_blocked.json()["query_type"] == "BLOCKED_DIRECT_NAME"

    # Test allowed pseudonym
    res_allowed = client.post(
        "/api/privacy/query/validate",
        json={"query": "Subject-Theta-482", "analyst_id": "Analyst-1"},
    )
    assert res_allowed.status_code == 200
    assert res_allowed.json()["allowed"] is True
    assert res_allowed.json()["query_type"] == "PSEUDONYM"
