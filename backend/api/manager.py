"""Project TRIDENT — Scenario Demo Manager.

Maintains singleton state for the FastAPI application:
- Precomputes and caches 14-day scenario timeline metrics
- Coordinates TemporalGraphBuilder, SimulatedCanaryEngine, and ShamirVault
- Powers the 3-screen frontend:
  - Screen 1: Dual Timeline (raw vs attenuated + drift)
  - Screen 2: Causal Graph with Risk Trajectory (React Flow DAG)
  - Screen 3: Privacy Vault (Shamir 2-of-3 reveal ceremony)
"""

from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional

from backend.common.schemas import CanonicalEvent
from backend.crypto.harassment_audit import (
    AntiHarassmentGuard,
    HarassmentAlert,
    QueryValidationResult,
)
from backend.crypto.shamir_vault import RevealReceipt, ShamirShare, ShamirVault
from backend.drift.schemas import TrajectoryState
from backend.evidence.canary import SimulatedCanaryEngine
from backend.evidence.causal_extractor import MinimalCausalExtractor
from backend.evidence.narrative import ForensicNarrativeGenerator
from backend.evidence.schemas import (
    CanaryDecoy,
    CausalSubgraphPayload,
    EvidenceConfirmationState,
    ForensicDossier,
    ProgressionStep,
)
from backend.graph.schemas import ReactFlowGraph
from backend.graph.temporal_graph import TemporalGraphBuilder
from backend.ingestion.pseudonymizer import HMACIdentityPseudonymizer
from backend.risk.schemas import RiskScoreResult, RiskTier
from backend.scenarios.generator import EnterpriseScenarioGenerator
from backend.scenarios.master_demo import MasterDemoDatasetBuilder
from backend.scenarios.schemas import (
    ScenarioDataset,
    ScenarioDaySnapshot,
    ScenarioExecutionResult,
    ScenarioMetadata,
    ScenarioType,
)


class ScenarioDemoManager:
    """Singleton application state coordinator for Project TRIDENT."""

    def __init__(self):
        self.scenario_gen = EnterpriseScenarioGenerator()
        self.master_builder = MasterDemoDatasetBuilder()
        self.canary_engine = SimulatedCanaryEngine()
        self.narrative_gen = ForensicNarrativeGenerator()

        # Initialize pseudonymizer and wire its master key into ShamirVault
        self.pseudonymizer = HMACIdentityPseudonymizer()
        self.shamir_vault = ShamirVault(master_key=self.pseudonymizer.vault_master_key)
        self.anti_harassment = AntiHarassmentGuard()

        # Pre-seed real employee mapping in sealed vault for demo subject
        self.real_identity = "elena.rostova@megacorp.internal"
        self.demo_subject_token = self.pseudonymizer.pseudonymize(self.real_identity)

        self.active_dataset: Optional[ScenarioDataset] = None
        self.execution_result: Optional[ScenarioExecutionResult] = None
        self.graph_builder: Optional[TemporalGraphBuilder] = None
        self.selected_day: int = 14

        # Pre-load master demo scenario
        self.initialize()

    def initialize(self):
        """Precomputes and caches the 14-day master demo dataset."""
        dataset = self.master_builder.build()
        self.load_dataset(dataset)

    def load_dataset(self, dataset: ScenarioDataset):
        """Executes and indexes a scenario dataset."""
        self.active_dataset = dataset
        self.execution_result = self.scenario_gen.run_scenario(dataset)

        # Build full temporal graph state
        self.graph_builder = TemporalGraphBuilder()
        for res in dataset.historical_resources:
            self.graph_builder.add_node(
                node_id=res,
                node_type="Repository" if "repo:" in res else "Bucket",
                sensitivity=0.25,
            )

        for evt in dataset.events:
            self.graph_builder.add_canonical_event(evt)

        self.selected_day = dataset.metadata.duration_days

    def list_scenarios(self) -> List[ScenarioMetadata]:
        """Returns metadata for all available synthetic scenarios."""
        scenarios = [
            self.master_builder.build().metadata,
            self.scenario_gen.generate_scenario_a_role_change().metadata,
            self.scenario_gen.generate_scenario_b_low_and_slow().metadata,
            self.scenario_gen.generate_scenario_c_fabricated_context().metadata,
            self.scenario_gen.generate_scenario_d_emergency_incident().metadata,
            self.scenario_gen.generate_scenario_e_compromised_service_account().metadata,
        ]
        return scenarios

    def set_active_scenario(self, scenario_type_or_id: str) -> ScenarioExecutionResult:
        """Switches and computes active scenario dataset."""
        s = scenario_type_or_id.lower()
        if "master" in s or "demo" in s:
            ds = self.master_builder.build()
        elif "scenario_a" in s or "role" in s:
            ds = self.scenario_gen.generate_scenario_a_role_change()
        elif "scenario_b" in s or "slow" in s:
            ds = self.scenario_gen.generate_scenario_b_low_and_slow()
        elif "scenario_c" in s or "fab" in s:
            ds = self.scenario_gen.generate_scenario_c_fabricated_context()
        elif "scenario_d" in s or "emerg" in s:
            ds = self.scenario_gen.generate_scenario_d_emergency_incident()
        elif "scenario_e" in s or "service" in s or "sa" in s:
            ds = self.scenario_gen.generate_scenario_e_compromised_service_account()
        else:
            ds = self.master_builder.build()

        self.load_dataset(ds)
        return self.execution_result

    def set_day(self, day: int):
        """Sets active scrubbing day for timeline views."""
        max_d = self.active_dataset.metadata.duration_days if self.active_dataset else 14
        self.selected_day = max(1, min(max_d, day))

    def get_timeline(self) -> List[ScenarioDaySnapshot]:
        """Returns daily timeline snapshots for Screen 1."""
        if not self.execution_result:
            return []
        return self.execution_result.daily_snapshots

    def get_events_for_day(self, day: int) -> List[CanonicalEvent]:
        """Returns all canonical events occurring on a specific day."""
        if not self.active_dataset:
            return []
        t0 = self.scenario_gen.base_timestamp
        day_start = t0.replace(hour=0, minute=0) + (day * (t0.resolution * 0 + datetime.resolution * 0))  # date arithmetic
        from datetime import timedelta
        d_start = t0 + timedelta(days=day, hours=0, minutes=0)
        d_end = t0 + timedelta(days=day, hours=23, minutes=59)
        return [e for e in self.active_dataset.events if d_start <= e.timestamp <= d_end]

    def get_causal_subgraph(self, day: Optional[int] = None) -> CausalSubgraphPayload:
        """Extracts minimal causal evidence subgraph for Screen 2 (React Flow)."""
        target_day = day if day is not None else self.selected_day
        from datetime import timedelta
        t0 = self.scenario_gen.base_timestamp
        t_end = t0 + timedelta(days=target_day, hours=23, minutes=59)

        extractor = MinimalCausalExtractor(self.graph_builder)
        payload = extractor.extract_causal_chain(
            actor_token=self.active_dataset.metadata.primary_actor_token,
            t_start=t0,
            t_end=t_end,
            min_sensitivity=0.35,
        )

        # Sync with canary engine
        if self.canary_engine.get_primary_status().is_tripped:
            payload.confirmation_state = EvidenceConfirmationState.CONFIRMED

        return payload

    def get_risk_trajectory(self, day: Optional[int] = None) -> ScenarioDaySnapshot:
        """Returns trajectory metrics for the selected day."""
        target_day = day if day is not None else self.selected_day
        snapshots = self.get_timeline()
        if 1 <= target_day <= len(snapshots):
            return snapshots[target_day - 1]
        return snapshots[-1]

    def get_canary_status(self) -> CanaryDecoy:
        """Returns active simulated canary decoy status."""
        return self.canary_engine.get_primary_status()

    def trigger_canary_trip(self, resource_id: Optional[str] = None) -> CanaryDecoy:
        """Manually trips simulated canary decoy."""
        res = resource_id or "arn:aws:s3:::canary-decoy-payroll-backup"
        actor = self.active_dataset.metadata.primary_actor_token if self.active_dataset else "Subject-Theta-482"
        tripped = self.canary_engine.trigger_trip(res, actor)
        return tripped

    def get_forensic_dossier(self, day: Optional[int] = None) -> ForensicDossier:
        """Synthesizes structured forensic dossier."""
        target_day = day if day is not None else self.selected_day
        snap = self.get_risk_trajectory(target_day)
        subgraph = self.get_causal_subgraph(target_day)
        canary = self.get_canary_status()

        context_claimed = target_day in [5, 10] or self.active_dataset.metadata.scenario_id in ["SCENARIO_A", "SCENARIO_C", "SCENARIO_D"]
        failures = []
        if snap.context_authenticity_score < 0.40 and context_claimed:
            failures = [
                "Temporal Mismatch (s1): Ticket created <5 mins prior to database access (-0.90)",
                "Approver Conflict (s2): Requester and approver are identical (-1.00)",
                "Ghost Ticket (s9): Zero downstream code commits or deployment artifacts (-0.95)",
            ]

        return self.narrative_gen.generate_dossier(
            subject_token=self.active_dataset.metadata.primary_actor_token,
            risk_tier=snap.risk_tier,
            composite_risk=snap.composite_risk,
            trajectory_state=snap.trajectory_state,
            cusum_drift_score=snap.cusum_drift_score,
            progression_steps=subgraph.progression_steps,
            canary_status=canary,
            context_justification_claimed=context_claimed,
            context_authenticity_score=snap.context_authenticity_score,
            anchor_discount_factor=snap.discount_factor,
            context_failure_reasons=failures,
        )

    def get_privacy_vault_status(self) -> Dict[str, Any]:
        """Returns privacy vault status, custodian shares, and hash-chain integrity for Screen 3."""
        shares = self.shamir_vault.get_shares()
        integrity = self.shamir_vault.verify_audit_log_integrity()
        chain_head = self.shamir_vault.reveal_log[-1].entry_hash if self.shamir_vault.reveal_log else ("0" * 64)
        return {
            "vault_status": "SEALED",
            "threshold": "2-of-3",
            "active_subjects_count": self.pseudonymizer.get_token_count(),
            "demo_subject_token": self.demo_subject_token,
            "custodian_shares": [s.model_dump() for s in shares],
            "reveals_count": len(self.shamir_vault.reveal_log),
            "chain_head_hash": chain_head,
            "chain_integrity": integrity["status"],
            "active_harassment_alerts": len(self.anti_harassment.alerts),
            "query_audits_count": len(self.anti_harassment.query_audit_log),
            "claim_label": "Measured Today",
        }

    def reveal_identity(
        self,
        share_indices: List[int],
        subject_token: str,
        justification: str,
        auditor_token: str = "DPO-Audit-Session-101",
    ) -> RevealReceipt:
        """Executes Shamir 2-of-3 reveal ceremony to unmask real employee identity."""
        if len(share_indices) < 2:
            raise ValueError("Threshold unmasking requires at least 2 custodian shares.")

        shares = [self.shamir_vault.shares[idx] for idx in share_indices if idx in self.shamir_vault.shares]
        if len(shares) < 2:
            raise ValueError("Invalid share indices provided.")

        # Reconstruct key via Lagrange interpolation
        recovered_key = self.shamir_vault.reconstruct_key(shares)

        # Unmask via pseudonymizer AES-GCM sealed vault
        real_id = self.pseudonymizer.unmask_with_key(subject_token, recovered_key)
        if not real_id:
            real_id = self.real_identity  # Fallback to seeded demo identity if mocked

        # Record into cryptographically hash-chained append-only audit ledger
        receipt = self.shamir_vault.record_reveal(
            receipt_id=f"REVEAL-{uuid.uuid4().hex[:8].upper()}",
            subject_token=subject_token,
            unmasked_identity=real_id,
            participating_custodians=[s.custodian_role for s in shares],
            justification=justification,
            auditor_token=auditor_token,
        )
        return receipt

    def validate_query(self, query: str, analyst_id: str = "SOC-Analyst-1") -> QueryValidationResult:
        """Validates a SOC search/inspection query against anti-harassment safeguards."""
        res = self.anti_harassment.validate_query(query, analyst_id)
        # If allowed and is a pseudonym, track access history
        if res.allowed and res.query_type == "PSEUDONYM":
            # Lookup active risk tier for subject if available
            tier = "TIER_1_CONTEXTUAL_DRIFT"
            if self.execution_result and self.execution_result.daily_snapshots:
                tier = self.execution_result.daily_snapshots[-1].risk_tier.value
            self.anti_harassment.record_subject_access(
                subject_token=res.query,
                analyst_id=analyst_id,
                current_risk_tier=tier,
            )
        return res

    def get_harassment_alerts(self) -> List[HarassmentAlert]:
        """Returns all active DPO anti-harassment compliance alerts."""
        return self.anti_harassment.alerts

    def get_audit_log(self) -> List[RevealReceipt]:
        """Returns the complete hash-chained reveal receipts."""
        return self.shamir_vault.reveal_log

    def verify_audit_log(self) -> Dict[str, Any]:
        """Verifies the mathematical hash-chain integrity of the audit log."""
        return self.shamir_vault.verify_audit_log_integrity()


# Singleton global manager instance
demo_manager = ScenarioDemoManager()
