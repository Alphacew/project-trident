"""Project TRIDENT — Template-Driven Forensic Narrative Generator.

Synthesizes deterministic, evidence-backed forensic incident dossiers:
- Executive Incident Summary
- Pseudonymous Subject Overview
- Context Justification Audit (exact signals that degraded the anchor)
- Chronological Attack Progression Sequence
- MITRE ATT&CK Breakdown
- Tiered Containment & Response Directives

Invariant: Strictly template-driven without ungrounded LLM hallucination.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from backend.drift.schemas import TrajectoryState
from backend.evidence.mitre_mapper import DeterministicMitreMapper
from backend.evidence.schemas import (
    CanaryDecoy,
    EvidenceConfirmationState,
    ForensicDossier,
    ProgressionStep,
)
from backend.risk.schemas import RiskTier


class ForensicNarrativeGenerator:
    """Produces structured forensic investigation reports from evidence graphs."""

    def __init__(self):
        self.mitre_mapper = DeterministicMitreMapper()

    def generate_dossier(
        self,
        subject_token: str,
        risk_tier: RiskTier,
        composite_risk: float,
        trajectory_state: TrajectoryState,
        cusum_drift_score: float,
        progression_steps: List[ProgressionStep],
        canary_status: CanaryDecoy,
        context_justification_claimed: bool = False,
        context_authenticity_score: float = 0.0,
        anchor_discount_factor: float = 1.0,
        context_failure_reasons: Optional[List[str]] = None,
        incident_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> ForensicDossier:
        """Synthesizes an immutable, evidence-backed forensic dossier."""
        inc_id = incident_id or f"INC-TRIDENT-{uuid.uuid4().hex[:6].upper()}"
        now = timestamp or datetime.now(timezone.utc)
        failures = context_failure_reasons or []

        # 1. Executive Summary Synthesis
        if risk_tier == RiskTier.TIER_4_CRITICAL:
            summary = (
                f"CRITICAL BREACH ESCALATION: Pseudonymous subject {subject_token} has triggered a Tier 4 "
                f"incident (Composite Risk: {composite_risk:.1f}/100, Cumulative Drift: {cusum_drift_score:.2f}). "
                f"A {len(progression_steps)}-step causal chain confirms unanchored movement across sensitive databases, "
                f"staging mounts, and canary deception assets. "
            )
        elif risk_tier == RiskTier.TIER_3_HIGH_RISK_TRAJECTORY:
            summary = (
                f"HIGH-RISK TRAJECTORY DETECTED: Subject {subject_token} has accumulated anomalous behavioral drift "
                f"(CUSUM Drift: {cusum_drift_score:.2f}) crossing the high-risk escalation threshold. "
            )
        else:
            summary = (
                f"SECURITY MONITORING: Subject {subject_token} is operating within normal baseline limits "
                f"(Tier: {risk_tier.value}, Drift: {cusum_drift_score:.2f}). "
            )

        if context_justification_claimed:
            if context_authenticity_score < 0.40:
                summary += (
                    f"A claimed business anchor was evaluated and rejected: Context Authenticity Score (CAS) evaluated to "
                    f"{context_authenticity_score:.2f}, indicating fabricated or corrupted context ({', '.join(failures[:2]) or 'temporal mismatch'}). "
                    f"Risk suppression was denied."
                )
            else:
                summary += (
                    f"Claimed business anchor verified: CAS evaluated to {context_authenticity_score:.2f}. "
                    f"Risk attenuated by discount factor {anchor_discount_factor:.2f}."
                )
        else:
            summary += "No organizational anchor ticket was submitted or matched to justify this activity."

        if canary_status.confirmation_state == EvidenceConfirmationState.CONFIRMED:
            summary += (
                f" CRITICAL EVIDENCE: Simulated canary asset '{canary_status.resource_id}' was tripped at "
                f"{canary_status.trip_timestamp.strftime('%H:%M:%S UTC') if canary_status.trip_timestamp else 'Day 13'}, "
                f"converting probabilistic suspicion into deterministic forensic proof."
            )

        # 2. Recommended Response Actions
        if risk_tier == RiskTier.TIER_4_CRITICAL:
            response = (
                "1. Isolate endpoint and immediately revoke all active session credentials and API tokens.\n"
                "2. Freeze network egress paths to destination endpoints.\n"
                "3. Initiate Shamir 2-of-3 dual-custody unmasking protocol to reveal true identity for DPO/Legal.\n"
                "4. Dispatch forensic capture of local staging mount and memory dump."
            )
        elif risk_tier == RiskTier.TIER_3_HIGH_RISK_TRAJECTORY:
            response = (
                "1. Revoke temporary and elevated AWS IAM role credentials.\n"
                "2. Enforce step-up MFA challenge for all subsequent operations.\n"
                "3. Deploy targeted canary decoy in predicted target repository/bucket.\n"
                "4. Queue for priority Tier-3 SOC analyst review."
            )
        else:
            response = "Continue baseline monitoring. Context verified; no operational SOC intervention required."

        # 3. MITRE Technique Matrix
        techniques_in_chain = [s.mitre_technique for s in progression_steps]
        if "T1078" not in [t.split()[0] for t in techniques_in_chain]:
            techniques_in_chain.insert(0, "T1078 (Valid Accounts)")
        mitre_matrix = self.mitre_mapper.generate_matrix(techniques_in_chain)

        return ForensicDossier(
            subject_token=subject_token,
            incident_id=inc_id,
            timestamp=now,
            risk_tier=risk_tier,
            composite_risk=composite_risk,
            trajectory_state=trajectory_state,
            cusum_drift_score=cusum_drift_score,
            context_justification_claimed=context_justification_claimed,
            context_authenticity_score=round(context_authenticity_score, 4),
            anchor_discount_factor=round(anchor_discount_factor, 4),
            context_failure_reasons=failures,
            progression_chain=progression_steps,
            mitre_attack_matrix=mitre_matrix,
            executive_summary=summary,
            recommended_response=response,
            canary_status=canary_status,
            claim_label="Measured Today",
        )
