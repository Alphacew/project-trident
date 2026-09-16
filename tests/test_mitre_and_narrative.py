"""Project TRIDENT — Test Suite for MITRE ATT&CK Mapping & Forensic Narrative.

Verifies:
1. Deterministic MITRE ATT&CK mappings (T1078, T1068, T1005, T1567, T1074, T1083)
2. Stage-to-tactic and edge-to-technique inference
3. Template-driven forensic dossier generation without LLM hallucination
4. Verification of context failure explanations, containment directives, and claim labels
"""

from datetime import datetime, timezone
import pytest

from backend.drift.schemas import TrajectoryState
from backend.evidence.canary import SimulatedCanaryEngine
from backend.evidence.mitre_mapper import DeterministicMitreMapper
from backend.evidence.narrative import ForensicNarrativeGenerator
from backend.evidence.schemas import (
    EvidenceConfirmationState,
    ProgressionStage,
    ProgressionStep,
)
from backend.graph.schemas import EdgeType
from backend.risk.schemas import RiskTier


@pytest.fixture
def mitre_mapper():
    return DeterministicMitreMapper()


@pytest.fixture
def narrative_gen():
    return ForensicNarrativeGenerator()


def test_mitre_deterministic_mapping(mitre_mapper):
    """Verifies deterministic technique and tactic resolution."""
    # Test techniques
    t1078 = mitre_mapper.get_technique_details("T1078")
    assert t1078["name"] == "Valid Accounts"
    assert "Initial Access" in t1078["tactic"]

    t1068 = mitre_mapper.get_technique_details("T1068")
    assert t1068["name"] == "Exploitation for Privilege Escalation"

    t1005 = mitre_mapper.get_technique_details("T1005")
    assert t1005["name"] == "Data from Local System"

    t1567 = mitre_mapper.get_technique_details("T1567")
    assert t1567["name"] == "Exfiltration Over Web Service"

    # Test edge mapping
    tactic_role, tech_role = mitre_mapper.map_edge_to_mitre(
        EdgeType.ASSUMED_ROLE, "arn:aws:iam::role/Admin", sensitivity=0.9
    )
    assert "T1068" in tech_role

    tactic_db, tech_db = mitre_mapper.map_edge_to_mitre(
        EdgeType.QUERIED, "db:eu-payroll-records", sensitivity=0.95
    )
    assert "T1005" in tech_db

    tactic_canary, tech_canary = mitre_mapper.map_edge_to_mitre(
        EdgeType.ACCESSED, "arn:aws:s3:::canary-decoy", sensitivity=1.0, is_canary=True
    )
    assert "T1567" in tech_canary

    # Generate matrix
    matrix = mitre_mapper.generate_matrix(["T1078", "T1068", "T1005", "T1567"])
    assert len(matrix) == 4
    tech_ids = [m["technique_id"] for m in matrix]
    assert tech_ids == ["T1078", "T1068", "T1005", "T1567"]


def test_forensic_narrative_generation(narrative_gen):
    """Verifies synthesis of forensic incident dossier and invariant adherence."""
    now = datetime.now(timezone.utc)
    canary_engine = SimulatedCanaryEngine()
    canary_status = canary_engine.trigger_trip("arn:aws:s3:::canary-decoy-payroll-backup", "Subject-Theta-482")

    steps = [
        ProgressionStep(
            step_number=1,
            timestamp=now,
            stage=ProgressionStage.CREDENTIAL_ANOMALY,
            source_node="Subject-Theta-482",
            target_node="okta:login",
            action="login",
            edge_type="AUTHENTICATED",
            mitre_tactic="Initial Access",
            mitre_technique="T1078 (Valid Accounts)",
            description="Anomalous off-hours login",
            sensitivity=0.6,
        ),
        ProgressionStep(
            step_number=2,
            timestamp=now,
            stage=ProgressionStage.SENSITIVE_ACCESS,
            source_node="Subject-Theta-482",
            target_node="db:eu-payroll-records",
            action="SELECT *",
            edge_type="QUERIED",
            mitre_tactic="Collection",
            mitre_technique="T1005 (Data from Local System)",
            description="Unauthorized dump of payroll records",
            sensitivity=0.95,
        ),
        ProgressionStep(
            step_number=3,
            timestamp=now,
            stage=ProgressionStage.CANARY_TRIP,
            source_node="Subject-Theta-482",
            target_node="arn:aws:s3:::canary-decoy-payroll-backup",
            action="s3:GetObject",
            edge_type="CANARY_TRIP",
            mitre_tactic="Exfiltration",
            mitre_technique="T1567 (Exfiltration Over Web Service)",
            description="Accessed decoy canary asset",
            sensitivity=1.0,
        ),
    ]

    dossier = narrative_gen.generate_dossier(
        subject_token="Subject-Theta-482",
        risk_tier=RiskTier.TIER_4_CRITICAL,
        composite_risk=89.5,
        trajectory_state=TrajectoryState.CRITICAL,
        cusum_drift_score=16.62,
        progression_steps=steps,
        canary_status=canary_status,
        context_justification_claimed=True,
        context_authenticity_score=0.21,
        anchor_discount_factor=0.83,
        context_failure_reasons=[
            "Temporal Mismatch (s1): Ticket created 4 mins prior (-0.90)",
            "Ghost Ticket (s9): Zero downstream commits (-0.95)",
        ],
    )

    assert dossier.subject_token == "Subject-Theta-482"
    assert dossier.risk_tier == RiskTier.TIER_4_CRITICAL
    assert dossier.composite_risk == 89.5
    assert dossier.context_authenticity_score == 0.21
    assert len(dossier.progression_chain) == 3
    assert len(dossier.mitre_attack_matrix) >= 2
    assert dossier.claim_label == "Measured Today"

    # Check narrative executive summary
    assert "CRITICAL BREACH ESCALATION" in dossier.executive_summary
    assert "Subject-Theta-482" in dossier.executive_summary
    assert "Context Authenticity Score (CAS) evaluated to 0.21" in dossier.executive_summary
    assert "CRITICAL EVIDENCE: Simulated canary asset" in dossier.executive_summary

    # Check response recommendations
    assert "Isolate endpoint" in dossier.recommended_response
    assert "Shamir 2-of-3" in dossier.recommended_response
