"""Project TRIDENT — Test Suite for FastAPI REST Endpoints.

Tests all exposed routes using Starlette TestClient:
- Root healthcheck & Claim Ledger metadata
- Screen 1: /api/timeline and /api/timeline/events
- Screen 2: /api/graph/causal and /api/graph/ego
- Risk: /api/risk/trajectory and /api/risk/history
- Canary: /api/canary/status and POST /api/canary/trip
- Scenarios: /api/scenarios, execute, and scrub
- Evidence: /api/evidence/dossier
- Screen 3: /api/privacy/vault/status and POST /api/privacy/vault/recombine
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.app import app
from backend.api.manager import demo_manager


@pytest.fixture
def client():
    # Re-initialize to clean demo state
    demo_manager.initialize()
    return TestClient(app)


def test_root_endpoint(client):
    """Verifies service healthcheck and root metadata."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "Project TRIDENT API"
    assert data["claim_label"] == "Measured Today"


def test_timeline_endpoints(client):
    """Verifies Screen 1 timeline series and event inspection."""
    res = client.get("/api/timeline")
    assert res.status_code == 200
    timeline = res.json()
    assert len(timeline) == 14
    assert timeline[0]["day"] == 1
    assert timeline[-1]["day"] == 14

    # Check daily events endpoint
    res_evts = client.get("/api/timeline/events?day=5")
    assert res_evts.status_code == 200
    evts = res_evts.json()
    assert len(evts) >= 1
    assert any("EVT-DEMO-D5" in e["event_id"] for e in evts)


def test_graph_endpoints(client):
    """Verifies Screen 2 React Flow causal graph and ego network."""
    res = client.get("/api/graph/causal?day=14")
    assert res.status_code == 200
    causal = res.json()
    assert causal["actor_token"] == "Subject-Theta-482"
    assert len(causal["nodes"]) >= 5
    assert len(causal["edges"]) >= 5
    assert len(causal["progression_steps"]) >= 5
    assert causal["confirmation_state"] == "CONFIRMED"

    # Ego network
    res_ego = client.get("/api/graph/ego?hops=2")
    assert res_ego.status_code == 200
    ego = res_ego.json()
    assert len(ego["nodes"]) >= 1


def test_risk_endpoints(client):
    """Verifies risk trajectory and trend endpoints."""
    res = client.get("/api/risk/trajectory?day=14")
    assert res.status_code == 200
    risk = res.json()
    assert risk["risk_tier"] == "TIER_4_CRITICAL"
    assert risk["composite_risk"] >= 75.0

    res_hist = client.get("/api/risk/history")
    assert res_hist.status_code == 200
    hist = res_hist.json()
    assert len(hist) == 14


def test_canary_endpoints(client):
    """Verifies simulated canary status and interactive trip trigger."""
    res = client.get("/api/canary/status")
    assert res.status_code == 200
    canary = res.json()
    assert canary["claim_label"] == "Simulated Canary"

    # Trigger interactive trip
    res_trip = client.post("/api/canary/trip", json={"resource_id": "arn:aws:s3:::canary-decoy-payroll-backup"})
    assert res_trip.status_code == 200
    tripped = res_trip.json()
    assert tripped["is_tripped"] is True
    assert tripped["confirmation_state"] == "CONFIRMED"


def test_scenarios_endpoints(client):
    """Verifies scenario listing, switching, and scrubbing."""
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) == 6

    # Execute Scenario A
    res_exec = client.post("/api/scenarios/scenario_a/execute")
    assert res_exec.status_code == 200
    exec_res = res_exec.json()
    assert exec_res["metadata"]["scenario_id"] == "SCENARIO_A"

    # Scrub timeline
    res_scrub = client.post("/api/scenarios/scrub/3")
    assert res_scrub.status_code == 200
    assert res_scrub.json()["selected_day"] == 3


def test_evidence_dossier_endpoint(client):
    """Verifies forensic incident dossier generation."""
    # Restore master demo
    client.post("/api/scenarios/master_demo/execute")
    res = client.get("/api/evidence/dossier?day=14")
    assert res.status_code == 200
    dossier = res.json()
    assert dossier["subject_token"] == "Subject-Theta-482"
    assert dossier["risk_tier"] == "TIER_4_CRITICAL"
    assert "CRITICAL BREACH ESCALATION" in dossier["executive_summary"]
    assert len(dossier["progression_chain"]) >= 5
    assert len(dossier["mitre_attack_matrix"]) >= 3


def test_privacy_vault_endpoints(client):
    """Verifies Screen 3 privacy vault status and Shamir 2-of-3 reveal ceremony."""
    res = client.get("/api/privacy/vault/status")
    assert res.status_code == 200
    status = res.json()
    assert status["vault_status"] == "SEALED"
    assert status["threshold"] == "2-of-3"
    assert len(status["custodian_shares"]) == 3
    demo_token = status["demo_subject_token"]

    # Attempt reveal with insufficient shares (1 share) -> Expect 400 Bad Request
    res_bad = client.post(
        "/api/privacy/vault/recombine",
        json={
            "share_indices": [1],
            "subject_token": demo_token,
            "justification": "Single custodian attempt",
        },
    )
    assert res_bad.status_code == 400

    # Valid 2-of-3 reveal ceremony (SOC Lead + DPO Legal)
    res_reveal = client.post(
        "/api/privacy/vault/recombine",
        json={
            "share_indices": [1, 2],
            "subject_token": demo_token,
            "justification": "Authorized Tier 4 insider breach investigation by Legal & SOC",
            "auditor_token": "DPO-AUDIT-491",
        },
    )
    assert res_reveal.status_code == 200
    receipt = res_reveal.json()
    assert receipt["unmasked_identity"] == "elena.rostova@megacorp.internal"
    assert "SOC_LEAD" in receipt["participating_custodians"]
    assert "DPO_LEGAL" in receipt["participating_custodians"]
    assert "REVEAL-" in receipt["receipt_id"]
